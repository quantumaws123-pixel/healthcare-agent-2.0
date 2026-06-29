"""
scripts/load_sample_data.py
===========================
Load the Healthcare Digital Twin CSV into the PostgreSQL database.

Usage:
    python scripts/load_sample_data.py
    python scripts/load_sample_data.py --limit 5000

The script:
  1. Reads the CSV with pandas (PascalCase column names).
  2. Renames columns to snake_case DB column names.
  3. Batch-inserts 500 rows at a time using asyncio + SQLAlchemy async session.
  4. Uses ON CONFLICT DO NOTHING to skip existing (patient_id, day) combos.
  5. Prints progress every 1 000 rows.
  6. Accepts an optional --limit N argument.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Logging setup (plain text — we're in a CLI, not FastAPI)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# CSV is in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "Healthcare_Digital_Twin_100000_generated_check.csv"

BATCH_SIZE = 500
PROGRESS_EVERY = 1000

# Mapping: CSV PascalCase column → DB snake_case column
COLUMN_MAP: dict[str, str] = {
    "Patient_ID": "patient_id",
    "Age": "age",
    "Gender": "gender",
    "BMI": "bmi",
    "Smoking_Status": "smoking_status",
    "Alcohol_Consumption": "alcohol_consumption",
    "Disease_Type": "disease_type",
    "Heart_Rate": "heart_rate",
    "Systolic_BP": "systolic_bp",
    "Diastolic_BP": "diastolic_bp",
    "SpO2": "spo2",
    "Respiratory_Rate": "respiratory_rate",
    "Body_Temperature": "body_temperature",
    "Expected_Steps": "expected_steps",
    "Expected_Sleep_Hours": "expected_sleep_hours",
    "Water_Intake_Goal": "water_intake_goal",
    "Actual_Steps": "actual_steps",
    "Actual_Sleep_Hours": "actual_sleep_hours",
    "Water_Intake": "water_intake",
    "Medication_Taken": "medication_taken",
    "Exercise_Completed": "exercise_completed",
    "Diet_Compliance": "diet_compliance",
    "Compliance_Score": "compliance_score",
    "Ideal_Health_Score": "ideal_health_score",
    "Real_Health_Score": "real_health_score",
    "Deviation_Score": "deviation_score",
    "Recovery_Score": "recovery_score",
    "Readmission_Probability": "readmission_probability",
    "Risk_Level": "risk_level",
    "Health_Trend": "health_trend",
    "Recovery_Status": "recovery_status",
    "Doctor_Recommendation": "doctor_recommendation",
    "Day": "day",
    "Patient_Name": "patient_name",
}

# DB columns that make up the composite primary key (used for ON CONFLICT)
PK_COLUMNS = ("patient_id", "day")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_database_url() -> str:
    """Build the async PostgreSQL connection URL from environment variables."""
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME", "healthcare_agent")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD")

    if not password:
        raise ValueError(
            "DATABASE_PASSWORD environment variable is required but not set. "
            "Add it to your .env file or export it before running this script."
        )

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


def load_csv(limit: int | None) -> pd.DataFrame:
    """Read the CSV, rename columns, optionally truncate, and clean nulls."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_PATH}\n"
            "Place 'Healthcare_Digital_Twin_100000_generated_check.csv' in the project root."
        )

    logger.info("Reading CSV: %s", CSV_PATH)
    df = pd.read_csv(CSV_PATH, low_memory=False)
    logger.info("CSV loaded: %d rows × %d columns", len(df), len(df.columns))

    # Apply column rename — keep only columns that have a mapping
    present_csv_cols = [c for c in COLUMN_MAP if c in df.columns]
    df = df[present_csv_cols].rename(columns=COLUMN_MAP)

    # Scale readmission_probability from percentage (0-100) to probability (0-1)
    if "readmission_probability" in df.columns:
        df["readmission_probability"] = df["readmission_probability"] / 100.0

    # Convert water intake fields from Litres (CSV) to mL (DB/Schema)
    if "water_intake_goal" in df.columns:
        df["water_intake_goal"] = (df["water_intake_goal"] * 1000).round().astype("Int64")
    if "water_intake" in df.columns:
        df["water_intake"] = (df["water_intake"] * 1000).round().astype("Int64")

    if limit is not None:
        df = df.iloc[:limit]
        logger.info("Applying --limit: using first %d rows", len(df))

    # Replace pandas NaN with None so asyncpg receives proper SQL NULLs
    df = df.where(pd.notnull(df), other=None)

    return df


def build_upsert_sql(columns: list[str]) -> str:
    """
    Build a parameterised INSERT … ON CONFLICT DO NOTHING statement.

    asyncpg uses $1, $2, … positional placeholders.
    """
    col_names = ", ".join(columns)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
    return (
        f"INSERT INTO patient_records ({col_names}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT (patient_id, day) DO NOTHING"
    )


# ---------------------------------------------------------------------------
# Async insertion logic
# ---------------------------------------------------------------------------

async def insert_batch(
    conn,
    sql: str,
    rows: list[tuple],
) -> int:
    """Execute a batch of INSERT statements and return the number inserted."""
    inserted = 0
    for row in rows:
        result = await conn.execute(text(sql).bindparams(), row)
        # asyncpg returns rowcount via the raw driver; SQLAlchemy text() gives
        # us the cursor so we check rowcount on the result.
        # Each ON CONFLICT DO NOTHING returns rowcount 0 if skipped, 1 if inserted.
        inserted += result.rowcount
    return inserted


async def run_load(df: pd.DataFrame) -> None:
    """Iterate over the DataFrame in batches and insert into the DB."""
    url = get_database_url()
    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    columns: list[str] = list(df.columns)
    total_rows = len(df)
    total_inserted = 0
    total_skipped = 0

    logger.info(
        "Starting load: %d rows → patient_records (batch_size=%d)",
        total_rows,
        BATCH_SIZE,
    )

    # Build the parameterised SQL once
    col_names = ", ".join(columns)
    placeholders = ", ".join(f":{col}" for col in columns)
    upsert_sql = (
        f"INSERT INTO patient_records ({col_names}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT (patient_id, day) DO NOTHING"
    )

    for batch_start in range(0, total_rows, BATCH_SIZE):
        batch_df = df.iloc[batch_start: batch_start + BATCH_SIZE]
        batch_records = batch_df.to_dict(orient="records")

        async with session_factory() as session:
            batch_inserted = 0
            for record in batch_records:
                # Replace Python None with SQL-safe None; keep as-is otherwise
                clean_record = {
                    k: (None if v is None else v)
                    for k, v in record.items()
                }
                result = await session.execute(text(upsert_sql), clean_record)
                batch_inserted += result.rowcount

            await session.commit()

        batch_skipped = len(batch_records) - batch_inserted
        total_inserted += batch_inserted
        total_skipped += batch_skipped

        rows_processed = batch_start + len(batch_records)

        # Print progress every PROGRESS_EVERY rows (or at the very end)
        if rows_processed % PROGRESS_EVERY < BATCH_SIZE or rows_processed >= total_rows:
            pct = rows_processed / total_rows * 100
            logger.info(
                "Progress: %d / %d rows (%.1f%%) — "
                "inserted: %d, skipped (existing): %d",
                rows_processed,
                total_rows,
                pct,
                total_inserted,
                total_skipped,
            )

    await engine.dispose()

    logger.info(
        "Load complete. Total: %d rows processed — "
        "%d inserted, %d skipped (already existed).",
        total_rows,
        total_inserted,
        total_skipped,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load Healthcare Digital Twin CSV data into PostgreSQL."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Load only the first N rows of the CSV (default: all rows).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load .env if present (convenient for local development)
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        from pathlib import Path as _P
        for line in _P(env_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

    try:
        df = load_csv(args.limit)
        asyncio.run(run_load(df))
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("%s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()

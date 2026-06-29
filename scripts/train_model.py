"""
scripts/train_model.py
======================
Train an XGBoost readmission-prediction model on data loaded in the database.

Workflow:
  1. Connect to the DB and load all patient records into a DataFrame.
  2. Run FeatureEngineer.fit_transform() to impute, encode, and normalise.
  3. Split with split_patient_data() (70 / 15 / 15, patient-level).
  4. Train with train_xgboost() (saves model to ./models/).
  5. Register the model in the DB via ModelRegistry (set as active).
  6. Print AUC-ROC and F1 score.

Usage:
    python scripts/train_model.py
    python scripts/train_model.py --model-version v1.1
    python scripts/train_model.py --model-dir /path/to/models
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root on sys.path so `app.*` imports work when run from any directory
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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
            "DATABASE_PASSWORD environment variable is required but not set."
        )

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


def load_dotenv() -> None:
    """Load .env from the project root into os.environ (keys not already set)."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


# ---------------------------------------------------------------------------
# Core async training routine
# ---------------------------------------------------------------------------

async def train(model_version: str, model_dir: str) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.ml.data_loader import load_from_database_dataframe
    from app.ml.data_splitter import split_patient_data
    from app.ml.feature_engineer import FeatureEngineer
    from app.ml.model_registry import ModelRegistry
    from app.ml.model_trainer import train_xgboost

    url = get_database_url()
    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # ------------------------------------------------------------------
    # 1. Load all patient records from the database
    # ------------------------------------------------------------------
    logger.info("Loading patient records from database …")
    async with session_factory() as session:
        df = await load_from_database_dataframe(session)

    if df.empty:
        logger.error(
            "No patient records found in the database. "
            "Run scripts/load_sample_data.py first."
        )
        await engine.dispose()
        sys.exit(1)

    logger.info("Loaded %d records for %d unique patients.", len(df), df["patient_id"].nunique())

    # ------------------------------------------------------------------
    # 2. Feature engineering
    # ------------------------------------------------------------------
    logger.info("Running FeatureEngineer.fit_transform() …")
    fe = FeatureEngineer(normalization="minmax")
    features_df = fe.fit_transform(df)
    logger.info("Feature matrix shape after engineering: %s", features_df.shape)

    # ------------------------------------------------------------------
    # 3. Patient-level train / val / test split
    # ------------------------------------------------------------------
    logger.info("Splitting data (70 / 15 / 15, patient-level) …")
    # Re-attach patient_id for splitting (fit_transform may have kept it)
    if "patient_id" not in features_df.columns and "patient_id" in df.columns:
        features_df = features_df.copy()
        features_df["patient_id"] = df["patient_id"].values

    split = split_patient_data(features_df, random_seed=42)
    sizes = split.split_sizes()
    logger.info(
        "Split sizes — train: %d, val: %d, test: %d",
        sizes["train"],
        sizes["val"],
        sizes["test"],
    )

    # ------------------------------------------------------------------
    # 4. Train XGBoost
    # ------------------------------------------------------------------
    logger.info("Training XGBoost (version=%s) …", model_version)
    result = train_xgboost(
        split,
        model_version=model_version,
        model_dir=model_dir,
    )

    metrics = result.metrics
    print("\n" + "=" * 55)
    print(f"  XGBoost Training Complete — version {model_version}")
    print("=" * 55)
    print(f"  AUC-ROC  : {metrics.auc_roc:.4f}")
    print(f"  F1 Score : {metrics.f1_score:.4f}")
    print(f"  Accuracy : {metrics.accuracy:.4f}")
    print(f"  Precision: {metrics.precision:.4f}")
    print(f"  Recall   : {metrics.recall:.4f}")
    print(f"  Dataset  : {result.dataset_size} records")
    print(f"  Model    : {result.model_path}")
    print("=" * 55 + "\n")

    # ------------------------------------------------------------------
    # 5. Save preprocessor and register model in DB (mark as active)
    # ------------------------------------------------------------------
    # Save the fitted preprocessor to disk
    from app.ml.feature_preprocessor import FeaturePreprocessor
    preprocessor = FeaturePreprocessor.from_feature_engineer(fe)
    preprocessor_path = Path(model_dir) / f"preprocessor_{model_version}.joblib"
    preprocessor.save(preprocessor_path)
    logger.info("Saved preprocessor to %s", preprocessor_path)

    logger.info("Registering model in database (set_active=True) …")
    async with session_factory() as session:
        registry = ModelRegistry(session, model_dir=model_dir)
        db_record = await registry.save_model(result, set_active=True)
        await session.commit()
        logger.info(
            "Model registered: version='%s', model_id=%d, is_active=%s",
            db_record.model_version,
            db_record.model_id,
            db_record.is_active,
        )

    await engine.dispose()
    logger.info("Training pipeline complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train XGBoost readmission model from database data."
    )
    parser.add_argument(
        "--model-version",
        default="v1.0",
        metavar="VERSION",
        help="Semantic version tag for the trained model (default: v1.0).",
    )
    parser.add_argument(
        "--model-dir",
        default="./models",
        metavar="DIR",
        help="Directory where the model artefact is saved (default: ./models).",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    try:
        asyncio.run(train(args.model_version, args.model_dir))
    except ValueError as exc:
        logger.error("%s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()

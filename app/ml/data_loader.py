"""Data loader for Healthcare Agent 2.0 Backend ML System.

This module provides ETL (Extract, Transform, Load) functionality for
ingesting patient records from CSV files and the relational database.

Corrupt or invalid records are logged and skipped rather than raising
exceptions so that the pipeline can process the maximum amount of clean
data in each run.

**Validates: Requirements 11.1, 11.8**
"""

import csv
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import PatientRecordDB
from app.models.schemas import PatientRecord

# Module-level logger
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _row_to_patient_record(
    row: dict[str, Any],
    source_label: str,
    row_index: int,
) -> Optional[PatientRecord]:
    """
    Attempt to parse a raw dictionary into a validated PatientRecord.

    Any validation error is logged at WARNING level and the function
    returns ``None`` so the caller can skip the offending row.

    Args:
        row: Dictionary of field names to raw (string) values.
        source_label: Human-readable identifier for the data source
            (e.g. a file path or "database") used in log messages.
        row_index: Zero-based index of the row within its source,
            used only for log messages.

    Returns:
        A validated ``PatientRecord`` instance, or ``None`` if the row
        could not be parsed / validated.
    """
    try:
        # Coerce empty strings to None so Pydantic can handle optional fields
        cleaned: dict[str, Any] = {
            k: (None if isinstance(v, str) and v.strip() == "" else v)
            for k, v in row.items()
        }
        return PatientRecord(**cleaned)

    except Exception as exc:  # noqa: BLE001 – intentional broad catch for pipeline resilience
        logger.warning(
            "Skipping invalid record at index %d from '%s': %s",
            row_index,
            source_label,
            exc,
        )
        return None


def _orm_record_to_dict(record: PatientRecordDB) -> dict[str, Any]:
    """
    Convert an ORM ``PatientRecordDB`` instance to a plain dictionary.

    Only the columns that map directly to ``PatientRecord`` fields are
    included; ORM-internal attributes (like ``_sa_instance_state``) are
    excluded automatically.

    Args:
        record: SQLAlchemy ORM model instance.

    Returns:
        Dictionary representation of the record.
    """
    return {
        col.name: getattr(record, col.name)
        for col in PatientRecordDB.__table__.columns
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_from_csv(
    file_path: str | Path,
    *,
    encoding: str = "utf-8",
) -> list[PatientRecord]:
    """
    Load patient records from a CSV file.

    Each row in the CSV is validated against the ``PatientRecord`` schema.
    Rows that are missing required fields, have out-of-range values, or
    otherwise fail Pydantic validation are logged and skipped; they do
    **not** raise an exception.

    The CSV is expected to have a header row whose column names match the
    field names of ``PatientRecord`` (case-sensitive).

    Args:
        file_path: Absolute or relative path to the CSV file.
        encoding: Character encoding of the file (default ``"utf-8"``).

    Returns:
        List of validated ``PatientRecord`` instances.  The list may be
        empty if the file contains no valid records.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
        ValueError: If ``file_path`` is not a regular file.
        OSError: If the file cannot be read for any other OS-level reason.

    **Validates: Requirements 11.1, 11.8**

    Example::

        records = load_from_csv("data/patients.csv")
        print(f"Loaded {len(records)} valid patient records")
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    logger.info("Loading patient records from CSV: %s", path)

    records: list[PatientRecord] = []
    skipped: int = 0

    try:
        with path.open(encoding=encoding, newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                logger.warning(
                    "CSV file '%s' appears to be empty (no header row). "
                    "Returning empty list.",
                    path,
                )
                return records

            for index, row in enumerate(reader):
                patient = _row_to_patient_record(
                    dict(row),
                    source_label=str(path),
                    row_index=index,
                )
                if patient is not None:
                    records.append(patient)
                else:
                    skipped += 1

    except OSError as exc:
        logger.error("Failed to read CSV file '%s': %s", path, exc, exc_info=True)
        raise

    logger.info(
        "CSV load complete for '%s': %d valid record(s) loaded, %d skipped.",
        path,
        len(records),
        skipped,
    )
    return records


def load_from_csv_dataframe(
    file_path: str | Path,
    *,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    """
    Load patient records from a CSV file and return a pandas DataFrame.

    This is a convenience wrapper around :func:`load_from_csv` for use
    in the ML training pipeline where a DataFrame is more ergonomic than
    a list of Pydantic models.

    Invalid rows are silently excluded from the returned DataFrame.

    Args:
        file_path: Path to the CSV file.
        encoding: Character encoding of the file (default ``"utf-8"``).

    Returns:
        ``pandas.DataFrame`` containing only valid rows.  Columns match
        the fields of ``PatientRecord``.

    **Validates: Requirements 11.1, 11.8**
    """
    records = load_from_csv(file_path, encoding=encoding)
    if not records:
        logger.warning(
            "load_from_csv_dataframe: no valid records found in '%s'. "
            "Returning empty DataFrame.",
            file_path,
        )
        return pd.DataFrame()

    return pd.DataFrame([r.model_dump() for r in records])


async def load_from_database(
    session: AsyncSession,
    *,
    patient_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[PatientRecord]:
    """
    Load patient records from the relational database.

    Each database row is converted to a ``PatientRecord`` via Pydantic
    validation.  Rows that fail validation (e.g. data that became
    inconsistent through direct DB edits) are logged and skipped.

    Args:
        session: An active async SQLAlchemy session.
        patient_id: If provided, only records for this patient are
            returned.  Useful for per-patient batch processing.
        limit: Maximum number of records to retrieve.  ``None`` means
            no limit (retrieve all matching records).
        offset: Number of records to skip before returning results.
            Primarily intended for pagination in combination with
            ``limit``.

    Returns:
        List of validated ``PatientRecord`` instances.

    Raises:
        SQLAlchemyError: Propagated if the database query itself fails
            (connection error, timeout, etc.).  Row-level errors are
            handled internally and do not raise.

    **Validates: Requirements 11.1, 11.8**

    Example::

        async with get_db_context() as db:
            records = await load_from_database(db, patient_id="P001")
    """
    logger.info(
        "Loading patient records from database "
        "(patient_id=%s, limit=%s, offset=%d).",
        patient_id,
        limit,
        offset,
    )

    # Build the SELECT query
    query = select(PatientRecordDB).order_by(
        PatientRecordDB.patient_id,
        PatientRecordDB.day,
    )

    if patient_id is not None:
        query = query.where(PatientRecordDB.patient_id == patient_id)

    if offset:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    try:
        result = await session.execute(query)
        orm_records = result.scalars().all()
    except SQLAlchemyError as exc:
        logger.error(
            "Database query failed in load_from_database: %s",
            exc,
            exc_info=True,
        )
        raise

    records: list[PatientRecord] = []
    skipped: int = 0

    for index, orm_record in enumerate(orm_records):
        row_dict = _orm_record_to_dict(orm_record)
        patient = _row_to_patient_record(
            row_dict,
            source_label="database",
            row_index=index,
        )
        if patient is not None:
            records.append(patient)
        else:
            skipped += 1

    logger.info(
        "Database load complete: %d valid record(s) loaded, %d skipped.",
        len(records),
        skipped,
    )
    return records


async def load_from_database_dataframe(
    session: AsyncSession,
    *,
    patient_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> pd.DataFrame:
    """
    Load patient records from the database and return a pandas DataFrame.

    This is a convenience wrapper around :func:`load_from_database` for
    use in the ML training pipeline.

    Args:
        session: An active async SQLAlchemy session.
        patient_id: Optional filter by patient identifier.
        limit: Maximum number of records to retrieve.
        offset: Number of records to skip.

    Returns:
        ``pandas.DataFrame`` containing only valid rows.

    **Validates: Requirements 11.1, 11.8**
    """
    records = await load_from_database(
        session,
        patient_id=patient_id,
        limit=limit,
        offset=offset,
    )

    if not records:
        logger.warning(
            "load_from_database_dataframe: no valid records found. "
            "Returning empty DataFrame."
        )
        return pd.DataFrame()

    return pd.DataFrame([r.model_dump() for r in records])

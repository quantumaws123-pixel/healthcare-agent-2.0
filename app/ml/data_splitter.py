"""
Patient-aware train/validation/test data splitter for Healthcare Agent 2.0 Backend ML System.

This module implements patient-level stratified splitting of patient records into
training (70%), validation (15%), and test (15%) sets. The key invariant is that
all records for a given patient appear in exactly one split — preventing data
leakage where the model could learn from the same patient's history in both
training and evaluation.

**Validates: Requirements 3.2, 11.6**
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

# Module-level logger
logger = logging.getLogger(__name__)

# Default split ratios (must sum to 1.0)
DEFAULT_TRAIN_RATIO: float = 0.70
DEFAULT_VAL_RATIO: float = 0.15
DEFAULT_TEST_RATIO: float = 0.15


@dataclass
class DataSplit:
    """
    Container for train/validation/test DataFrames produced by the splitter.

    Attributes:
        train: DataFrame containing the training set records.
        val: DataFrame containing the validation set records.
        test: DataFrame containing the test set records.
    """

    train: pd.DataFrame = field(default_factory=pd.DataFrame)
    val: pd.DataFrame = field(default_factory=pd.DataFrame)
    test: pd.DataFrame = field(default_factory=pd.DataFrame)

    # -----------------------------------------------------------------------
    # Convenience properties
    # -----------------------------------------------------------------------

    @property
    def train_patients(self) -> set[str]:
        """Unique patient IDs in the training set."""
        return _unique_patients(self.train)

    @property
    def val_patients(self) -> set[str]:
        """Unique patient IDs in the validation set."""
        return _unique_patients(self.val)

    @property
    def test_patients(self) -> set[str]:
        """Unique patient IDs in the test set."""
        return _unique_patients(self.test)

    def patient_overlap(self) -> set[str]:
        """
        Return the set of patient IDs that appear in more than one split.

        A correctly constructed split will always return an empty set.
        """
        all_sets = [self.train_patients, self.val_patients, self.test_patients]
        seen: set[str] = set()
        overlap: set[str] = set()
        for pid_set in all_sets:
            overlap |= seen & pid_set
            seen |= pid_set
        return overlap

    def total_records(self) -> int:
        """Total number of records across all three splits."""
        return len(self.train) + len(self.val) + len(self.test)

    def split_sizes(self) -> dict[str, int]:
        """Return a dict with record counts for each split."""
        return {
            "train": len(self.train),
            "val": len(self.val),
            "test": len(self.test),
        }

    def split_ratios(self) -> dict[str, float]:
        """
        Return the actual split ratios based on patient counts.

        Returns a dict with keys ``"train"``, ``"val"``, ``"test"`` and
        float values between 0 and 1.  Returns zeros for an empty split.
        """
        total_patients = (
            len(self.train_patients)
            + len(self.val_patients)
            + len(self.test_patients)
        )
        if total_patients == 0:
            return {"train": 0.0, "val": 0.0, "test": 0.0}
        return {
            "train": len(self.train_patients) / total_patients,
            "val": len(self.val_patients) / total_patients,
            "test": len(self.test_patients) / total_patients,
        }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _unique_patients(df: pd.DataFrame) -> set[str]:
    """Return the set of unique patient_id values in *df*."""
    if df.empty or "patient_id" not in df.columns:
        return set()
    return set(df["patient_id"].unique())


def _validate_ratios(train_ratio: float, val_ratio: float, test_ratio: float) -> None:
    """
    Validate that split ratios are positive and sum to approximately 1.0.

    Args:
        train_ratio: Fraction of patients for training.
        val_ratio: Fraction of patients for validation.
        test_ratio: Fraction of patients for testing.

    Raises:
        ValueError: If any ratio is non-positive or the sum deviates from 1.0.
    """
    for name, ratio in (
        ("train_ratio", train_ratio),
        ("val_ratio", val_ratio),
        ("test_ratio", test_ratio),
    ):
        if ratio <= 0:
            raise ValueError(f"{name} must be positive, got {ratio!r}")

    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Split ratios must sum to 1.0, got "
            f"train={train_ratio} + val={val_ratio} + test={test_ratio} = {total}"
        )


def _assign_patients_to_splits(
    patient_ids: list[str],
    train_ratio: float,
    val_ratio: float,
) -> tuple[list[str], list[str], list[str]]:
    """
    Deterministically partition *patient_ids* into three mutually exclusive lists.

    The split is performed at the patient level so that every record belonging
    to a patient ends up in the same partition.  Patients are shuffled before
    splitting to avoid any ordering bias in the source data.

    Args:
        patient_ids: Ordered (but not necessarily unique) list of patient IDs.
        train_ratio: Target fraction for training.
        val_ratio: Target fraction for validation.

    Returns:
        Tuple of ``(train_ids, val_ids, test_ids)`` lists.
    """
    unique_ids = list(dict.fromkeys(patient_ids))  # preserve order, deduplicate
    n = len(unique_ids)

    if n == 0:
        return [], [], []

    # Shuffle deterministically — caller controls the seed via random.seed()
    shuffled = unique_ids.copy()
    random.shuffle(shuffled)

    train_end = max(1, round(n * train_ratio))
    val_end = train_end + max(0, round(n * val_ratio))
    # Clamp val_end so there is at least one patient left for test when possible
    val_end = min(val_end, n - (1 if n > 2 else 0))

    train_ids = shuffled[:train_end]
    val_ids = shuffled[train_end:val_end]
    test_ids = shuffled[val_end:]

    return train_ids, val_ids, test_ids


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def split_patient_data(
    df: pd.DataFrame,
    *,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    val_ratio: float = DEFAULT_VAL_RATIO,
    test_ratio: float = DEFAULT_TEST_RATIO,
    random_seed: Optional[int] = 42,
    patient_id_col: str = "patient_id",
) -> DataSplit:
    """
    Split a patient records DataFrame into train/validation/test sets.

    The split is performed at the **patient level**: every row belonging to
    a given patient ID will appear in exactly one partition.  This prevents
    data leakage between splits (Requirement 11.6).

    The default ratios are 70 / 15 / 15 as specified in Requirement 3.2.

    Args:
        df: Input DataFrame.  Must contain a column named *patient_id_col*.
        train_ratio: Fraction of unique patients allocated to training.
            Default ``0.70``.
        val_ratio: Fraction of unique patients allocated to validation.
            Default ``0.15``.
        test_ratio: Fraction of unique patients allocated to testing.
            Default ``0.15``.
        random_seed: Seed for the random shuffle to make splits reproducible.
            Pass ``None`` for a non-deterministic split.
        patient_id_col: Name of the column containing patient identifiers.
            Default ``"patient_id"``.

    Returns:
        :class:`DataSplit` with ``train``, ``val``, and ``test`` DataFrames.

    Raises:
        ValueError: If the DataFrame is missing the patient ID column, or if
            the split ratios are invalid.

    **Validates: Requirements 3.2, 11.6**

    Example::

        df = load_from_csv_dataframe("data/patients.csv")
        split = split_patient_data(df, random_seed=0)
        print(split.split_sizes())   # {'train': N, 'val': M, 'test': K}
        assert len(split.patient_overlap()) == 0  # no leakage
    """
    _validate_ratios(train_ratio, val_ratio, test_ratio)

    if patient_id_col not in df.columns:
        raise ValueError(
            f"DataFrame is missing the patient ID column '{patient_id_col}'. "
            f"Available columns: {list(df.columns)}"
        )

    if df.empty:
        logger.warning("split_patient_data received an empty DataFrame; returning empty splits.")
        return DataSplit()

    # Set random seed for reproducibility
    if random_seed is not None:
        random.seed(random_seed)

    all_patient_ids: list[str] = df[patient_id_col].tolist()
    train_ids, val_ids, test_ids = _assign_patients_to_splits(
        all_patient_ids,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
    )

    # Build boolean masks using patient-level sets for O(1) lookup
    train_set = set(train_ids)
    val_set = set(val_ids)
    test_set = set(test_ids)

    train_mask = df[patient_id_col].isin(train_set)
    val_mask = df[patient_id_col].isin(val_set)
    test_mask = df[patient_id_col].isin(test_set)

    train_df = df[train_mask].reset_index(drop=True)
    val_df = df[val_mask].reset_index(drop=True)
    test_df = df[test_mask].reset_index(drop=True)

    split = DataSplit(train=train_df, val=val_df, test=test_df)

    # Safety assertion: log a warning if any overlap is detected (should never happen)
    overlap = split.patient_overlap()
    if overlap:
        logger.error(
            "Patient overlap detected across splits — this is a bug! "
            "Overlapping patient IDs: %s",
            overlap,
        )

    actual_ratios = split.split_ratios()
    logger.info(
        "Data split complete: %d train / %d val / %d test records "
        "(%d / %d / %d unique patients). "
        "Actual patient ratios: train=%.3f val=%.3f test=%.3f.",
        len(train_df),
        len(val_df),
        len(test_df),
        len(train_set),
        len(val_set),
        len(test_set),
        actual_ratios["train"],
        actual_ratios["val"],
        actual_ratios["test"],
    )

    return split


def split_patient_records(
    records: list,  # list[PatientRecord] — avoid circular import by using list
    *,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    val_ratio: float = DEFAULT_VAL_RATIO,
    test_ratio: float = DEFAULT_TEST_RATIO,
    random_seed: Optional[int] = 42,
) -> DataSplit:
    """
    Convenience wrapper that accepts a list of ``PatientRecord`` Pydantic models.

    Converts the records to a DataFrame and delegates to
    :func:`split_patient_data`.

    Args:
        records: List of ``PatientRecord`` instances.
        train_ratio: Fraction of unique patients for training (default 0.70).
        val_ratio: Fraction of unique patients for validation (default 0.15).
        test_ratio: Fraction of unique patients for testing (default 0.15).
        random_seed: Seed for reproducibility.

    Returns:
        :class:`DataSplit` with ``train``, ``val``, and ``test`` DataFrames.

    **Validates: Requirements 3.2, 11.6**
    """
    if not records:
        logger.warning("split_patient_records received an empty list; returning empty splits.")
        return DataSplit()

    df = pd.DataFrame([r.model_dump() for r in records])
    return split_patient_data(
        df,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        random_seed=random_seed,
    )

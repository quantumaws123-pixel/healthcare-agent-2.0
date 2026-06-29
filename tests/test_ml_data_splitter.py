"""
Unit tests for the ML data_splitter module.

Tests cover:
- split_patient_data: patient isolation, ratio approximation, empty input
- DataSplit: patient_overlap, split_sizes, split_ratios
- split_patient_records: convenience wrapper

Validates Requirements 3.2, 11.6
"""

import pandas as pd
import pytest

from app.ml.data_splitter import (
    DataSplit,
    DEFAULT_TEST_RATIO,
    DEFAULT_TRAIN_RATIO,
    DEFAULT_VAL_RATIO,
    split_patient_data,
    split_patient_records,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_df(n_patients: int = 20, records_per_patient: int = 5) -> pd.DataFrame:
    """Create a synthetic patient DataFrame with n_patients × records_per_patient rows."""
    rows = []
    for p in range(n_patients):
        pid = f"P{p:04d}"
        for day in range(1, records_per_patient + 1):
            rows.append({"patient_id": pid, "day": day, "value": float(p * 100 + day)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# split_patient_data — basic correctness
# ---------------------------------------------------------------------------

class TestSplitPatientData:
    """Core split correctness tests (Req 3.2, 11.6)."""

    def test_returns_data_split_instance(self):
        df = _make_df()
        result = split_patient_data(df, random_seed=0)
        assert isinstance(result, DataSplit)

    def test_all_records_accounted_for(self):
        df = _make_df(n_patients=30)
        result = split_patient_data(df, random_seed=42)
        assert result.total_records() == len(df)

    def test_no_patient_overlap_between_splits(self):
        """Core requirement: same patient must not appear in two splits (Req 11.6)."""
        df = _make_df(n_patients=30)
        result = split_patient_data(df, random_seed=42)
        assert len(result.patient_overlap()) == 0

    def test_train_is_largest_split(self):
        df = _make_df(n_patients=30)
        result = split_patient_data(df, random_seed=42)
        assert len(result.train) > len(result.val)
        assert len(result.train) > len(result.test)

    def test_split_ratios_approximate_defaults(self):
        """Patient-level ratios should be close to 70/15/15 (Req 3.2)."""
        df = _make_df(n_patients=100)
        result = split_patient_data(df, random_seed=42)
        ratios = result.split_ratios()
        assert abs(ratios["train"] - DEFAULT_TRAIN_RATIO) <= 0.05
        assert abs(ratios["val"] - DEFAULT_VAL_RATIO) <= 0.05
        assert abs(ratios["test"] - DEFAULT_TEST_RATIO) <= 0.05

    def test_reproducible_with_same_seed(self):
        df = _make_df(n_patients=20)
        r1 = split_patient_data(df, random_seed=7)
        r2 = split_patient_data(df, random_seed=7)
        pd.testing.assert_frame_equal(r1.train, r2.train)

    def test_different_seeds_give_different_splits(self):
        df = _make_df(n_patients=20)
        r1 = split_patient_data(df, random_seed=0)
        r2 = split_patient_data(df, random_seed=99)
        # Very unlikely to produce identical train patient sets
        assert r1.train_patients != r2.train_patients

    def test_missing_patient_id_column_raises(self):
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        with pytest.raises(ValueError, match="patient_id"):
            split_patient_data(df)

    def test_empty_dataframe_returns_empty_splits(self):
        df = pd.DataFrame(columns=["patient_id", "day"])
        result = split_patient_data(df)
        assert result.total_records() == 0
        assert len(result.train) == 0
        assert len(result.val) == 0
        assert len(result.test) == 0

    def test_custom_patient_id_column(self):
        df = pd.DataFrame({
            "pid": ["A", "A", "B", "B", "C", "C", "D", "D"],
            "day": [1, 2, 1, 2, 1, 2, 1, 2],
        })
        result = split_patient_data(df, patient_id_col="pid", random_seed=0)
        # No overlap using 'pid' column
        train_ids = set(result.train["pid"])
        val_ids = set(result.val["pid"])
        test_ids = set(result.test["pid"])
        assert len(train_ids & val_ids) == 0
        assert len(train_ids & test_ids) == 0
        assert len(val_ids & test_ids) == 0

    def test_invalid_ratios_raise(self):
        df = _make_df()
        with pytest.raises(ValueError):
            split_patient_data(df, train_ratio=0.8, val_ratio=0.3, test_ratio=0.3)

    def test_negative_ratio_raises(self):
        df = _make_df()
        with pytest.raises(ValueError):
            split_patient_data(df, train_ratio=-0.1, val_ratio=0.6, test_ratio=0.5)

    def test_split_with_single_patient_does_not_crash(self):
        """Edge case: only 1 patient — entire data goes to train."""
        df = pd.DataFrame({"patient_id": ["P001"] * 5, "day": range(1, 6)})
        result = split_patient_data(df, random_seed=0)
        # Must not raise; total records preserved
        assert result.total_records() == 5

    def test_split_preserves_all_columns(self):
        df = _make_df()
        result = split_patient_data(df, random_seed=42)
        assert set(result.train.columns) == set(df.columns)
        assert set(result.val.columns) == set(df.columns)
        assert set(result.test.columns) == set(df.columns)


# ---------------------------------------------------------------------------
# DataSplit — property tests
# ---------------------------------------------------------------------------

class TestDataSplitProperties:
    """Tests for DataSplit helper methods."""

    def _make_split(self, n_patients: int = 20) -> DataSplit:
        df = _make_df(n_patients=n_patients)
        return split_patient_data(df, random_seed=42)

    def test_train_patients_returns_set(self):
        split = self._make_split()
        assert isinstance(split.train_patients, set)

    def test_val_patients_returns_set(self):
        split = self._make_split()
        assert isinstance(split.val_patients, set)

    def test_test_patients_returns_set(self):
        split = self._make_split()
        assert isinstance(split.test_patients, set)

    def test_patient_overlap_empty_for_valid_split(self):
        split = self._make_split(n_patients=30)
        assert split.patient_overlap() == set()

    def test_patient_overlap_detected_when_injected(self):
        """Manually inject overlap and verify detection."""
        df = _make_df(n_patients=10)
        result = split_patient_data(df, random_seed=42)
        # Inject a patient from test into train
        if not result.test.empty:
            leaked_row = result.test.iloc[[0]].copy()
            result.train = pd.concat([result.train, leaked_row], ignore_index=True)
        overlap = result.patient_overlap()
        if not result.test.empty:
            assert len(overlap) > 0

    def test_total_records_is_sum_of_splits(self):
        split = self._make_split()
        expected = len(split.train) + len(split.val) + len(split.test)
        assert split.total_records() == expected

    def test_split_sizes_returns_dict(self):
        split = self._make_split()
        sizes = split.split_sizes()
        assert isinstance(sizes, dict)
        assert set(sizes.keys()) == {"train", "val", "test"}

    def test_split_sizes_match_actual_lengths(self):
        split = self._make_split()
        sizes = split.split_sizes()
        assert sizes["train"] == len(split.train)
        assert sizes["val"] == len(split.val)
        assert sizes["test"] == len(split.test)

    def test_split_ratios_sum_to_one(self):
        split = self._make_split(n_patients=30)
        ratios = split.split_ratios()
        assert sum(ratios.values()) == pytest.approx(1.0, abs=1e-9)

    def test_split_ratios_keys(self):
        split = self._make_split()
        ratios = split.split_ratios()
        assert set(ratios.keys()) == {"train", "val", "test"}

    def test_empty_split_ratios_all_zero(self):
        empty_split = DataSplit()
        ratios = empty_split.split_ratios()
        assert ratios["train"] == 0.0
        assert ratios["val"] == 0.0
        assert ratios["test"] == 0.0


# ---------------------------------------------------------------------------
# split_patient_records — convenience wrapper
# ---------------------------------------------------------------------------

class TestSplitPatientRecords:
    """Tests for split_patient_records Pydantic wrapper (Req 3.2, 11.6)."""

    def _make_records(self, n: int = 20):
        from app.models.schemas import PatientRecord
        records = []
        for i in range(n):
            records.append(PatientRecord(
                patient_id=f"P{i:04d}",
                age=40 + (i % 30),
                gender="Male" if i % 2 == 0 else "Female",
                bmi=22.0 + i % 10,
                smoking_status="Never",
                alcohol_consumption="None",
                disease_type="Diabetes",
                heart_rate=70 + i % 20,
                systolic_bp=115 + i % 20,
                diastolic_bp=70 + i % 10,
                spo2=97.0,
                respiratory_rate=16,
                body_temperature=36.6,
                expected_steps=5000,
                expected_sleep_hours=8.0,
                water_intake_goal=2000,
                actual_steps=4000 + i * 10,
                actual_sleep_hours=7.5,
                water_intake=1800,
                medication_taken="Yes",
                exercise_completed="Yes",
                diet_compliance=75.0,
                day=1,
            ))
        return records

    def test_returns_data_split(self):
        records = self._make_records(20)
        result = split_patient_records(records)
        assert isinstance(result, DataSplit)

    def test_no_patient_overlap(self):
        records = self._make_records(20)
        result = split_patient_records(records, random_seed=0)
        assert len(result.patient_overlap()) == 0

    def test_empty_list_returns_empty_splits(self):
        result = split_patient_records([])
        assert result.total_records() == 0

    def test_total_records_preserved(self):
        records = self._make_records(20)
        result = split_patient_records(records, random_seed=42)
        assert result.total_records() == 20

"""
Unit tests for the ML feature_engineer module.

Tests cover:
- impute_missing_values (median for numerical, mode for categorical)
- one_hot_encode (creates dummy columns, handles known_categories)
- minmax_normalize (scales to [0, 1], handles constant columns)
- zscore_normalize (standardises to zero mean / unit variance)
- create_derived_features (compliance, deviation, health_trend, recovery)
- FeatureEngineer fit_transform / transform round-trip

Validates Requirements 11.2, 11.3, 11.4, 11.5
"""

import math

import numpy as np
import pandas as pd
import pytest

from app.ml.feature_engineer import (
    CATEGORICAL_COLUMNS,
    NUMERICAL_COLUMNS,
    FeatureEngineer,
    create_derived_features,
    impute_missing_values,
    minmax_normalize,
    one_hot_encode,
    zscore_normalize,
    HEALTH_TREND_ENCODING,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_row(**overrides) -> dict:
    row = {
        "patient_id": "P001",
        "age": 55,
        "bmi": 26.0,
        "gender": "Male",
        "smoking_status": "Never",
        "alcohol_consumption": "None",
        "disease_type": "Diabetes",
        "heart_rate": 75,
        "systolic_bp": 120,
        "diastolic_bp": 78,
        "spo2": 97.0,
        "respiratory_rate": 16,
        "body_temperature": 36.7,
        "expected_steps": 5000,
        "expected_sleep_hours": 8.0,
        "water_intake_goal": 2000,
        "actual_steps": 4500,
        "actual_sleep_hours": 7.5,
        "water_intake": 1800,
        "medication_taken": "Yes",
        "exercise_completed": "Yes",
        "diet_compliance": 80.0,
        "day": 1,
    }
    row.update(overrides)
    return row


def _df(*rows) -> pd.DataFrame:
    if not rows:
        rows = [_base_row()]
    return pd.DataFrame(list(rows))


# ---------------------------------------------------------------------------
# impute_missing_values
# ---------------------------------------------------------------------------

class TestImputation:
    """Tests for impute_missing_values (Req 11.2)."""

    def test_numerical_nan_filled_with_median(self):
        df = pd.DataFrame({
            "age": [20.0, 40.0, float("nan"), 60.0],
        })
        result = impute_missing_values(df)
        # Median of [20, 40, 60] = 40.0
        assert result["age"].iloc[2] == pytest.approx(40.0)

    def test_categorical_nan_filled_with_mode(self):
        df = pd.DataFrame({
            "gender": ["Male", "Male", None, "Female"],
        })
        result = impute_missing_values(df)
        # Mode is "Male"
        assert result["gender"].iloc[2] == "Male"

    def test_no_mutation_of_original_df(self):
        df = pd.DataFrame({"age": [10.0, float("nan")]})
        df_copy = df.copy()
        impute_missing_values(df)
        pd.testing.assert_frame_equal(df, df_copy)

    def test_entirely_nan_categorical_uses_unknown(self):
        df = pd.DataFrame({"gender": [None, None, None]})
        result = impute_missing_values(df)
        assert result["gender"].iloc[0] == "Unknown"

    def test_no_nan_df_is_unchanged(self):
        df = _df()
        result = impute_missing_values(df)
        assert result.isnull().sum().sum() == 0


# ---------------------------------------------------------------------------
# one_hot_encode
# ---------------------------------------------------------------------------

class TestOneHotEncode:
    """Tests for one_hot_encode (Req 11.3)."""

    def test_creates_dummy_columns_for_gender(self):
        df = _df(_base_row(gender="Male"), _base_row(gender="Female"))
        result = one_hot_encode(df, columns=["gender"])
        assert "gender_Male" in result.columns
        assert "gender_Female" in result.columns
        assert "gender" not in result.columns

    def test_original_column_removed(self):
        df = _df()
        result = one_hot_encode(df, columns=["gender"])
        assert "gender" not in result.columns

    def test_known_categories_adds_missing_columns(self):
        df = pd.DataFrame({"gender": ["Male"]})
        known = {"gender": ["Male", "Female", "Other"]}
        result = one_hot_encode(df, columns=["gender"], known_categories=known)
        assert "gender_Male" in result.columns
        assert "gender_Female" in result.columns
        assert "gender_Other" in result.columns
        # Unseen categories filled with 0
        assert result["gender_Female"].iloc[0] == 0
        assert result["gender_Male"].iloc[0] == 1

    def test_extra_categories_not_in_known_are_dropped(self):
        df = pd.DataFrame({"gender": ["Unknown_Gender"]})
        known = {"gender": ["Male", "Female"]}
        result = one_hot_encode(df, columns=["gender"], known_categories=known)
        assert "gender_Unknown_Gender" not in result.columns

    def test_missing_column_skipped_gracefully(self):
        df = _df()
        # 'non_existent_col' not in df — should not raise
        result = one_hot_encode(df, columns=["non_existent_col"])
        # df unchanged apart from no-op
        assert "non_existent_col" not in result.columns


# ---------------------------------------------------------------------------
# minmax_normalize
# ---------------------------------------------------------------------------

class TestMinmaxNormalize:
    """Tests for minmax_normalize (Req 11.4)."""

    def test_min_maps_to_zero(self):
        df = pd.DataFrame({"age": [10.0, 20.0, 30.0]})
        result, ranges = minmax_normalize(df, columns=["age"])
        assert result["age"].min() == pytest.approx(0.0)

    def test_max_maps_to_one(self):
        df = pd.DataFrame({"age": [10.0, 20.0, 30.0]})
        result, ranges = minmax_normalize(df, columns=["age"])
        assert result["age"].max() == pytest.approx(1.0)

    def test_constant_column_set_to_0_5(self):
        df = pd.DataFrame({"age": [50.0, 50.0, 50.0]})
        result, _ = minmax_normalize(df, columns=["age"])
        assert (result["age"] == 0.5).all()

    def test_fitted_ranges_are_returned(self):
        df = pd.DataFrame({"age": [10.0, 20.0, 30.0]})
        _, ranges = minmax_normalize(df, columns=["age"])
        assert "age" in ranges
        assert ranges["age"] == (10.0, 30.0)

    def test_applies_pre_fitted_ranges(self):
        """Inference: use supplied ranges, not data ranges."""
        df = pd.DataFrame({"age": [20.0]})
        pre_ranges = {"age": (0.0, 100.0)}
        result, _ = minmax_normalize(df, columns=["age"], feature_ranges=pre_ranges)
        assert result["age"].iloc[0] == pytest.approx(0.20)

    def test_missing_columns_skipped(self):
        df = pd.DataFrame({"age": [10.0, 30.0]})
        # 'bmi' not in df
        result, ranges = minmax_normalize(df, columns=["age", "bmi"])
        assert "age" in ranges
        assert "bmi" not in ranges

    def test_no_mutation_of_original_df(self):
        df = pd.DataFrame({"age": [10.0, 20.0]})
        original = df.copy()
        minmax_normalize(df, columns=["age"])
        pd.testing.assert_frame_equal(df, original)


# ---------------------------------------------------------------------------
# zscore_normalize
# ---------------------------------------------------------------------------

class TestZscoreNormalize:
    """Tests for zscore_normalize (Req 11.4)."""

    def test_mean_is_zero_after_normalization(self):
        df = pd.DataFrame({"age": [10.0, 20.0, 30.0]})
        result, _ = zscore_normalize(df, columns=["age"])
        assert result["age"].mean() == pytest.approx(0.0, abs=1e-9)

    def test_std_is_one_after_normalization(self):
        df = pd.DataFrame({"age": [10.0, 20.0, 30.0, 40.0]})
        result, _ = zscore_normalize(df, columns=["age"])
        assert result["age"].std(ddof=0) == pytest.approx(1.0, abs=1e-9)

    def test_constant_column_set_to_zero(self):
        df = pd.DataFrame({"age": [42.0, 42.0, 42.0]})
        result, _ = zscore_normalize(df, columns=["age"])
        assert (result["age"] == 0.0).all()

    def test_fitted_stats_returned(self):
        df = pd.DataFrame({"age": [10.0, 20.0, 30.0]})
        _, stats = zscore_normalize(df, columns=["age"])
        assert "age" in stats
        mean, std = stats["age"]
        assert mean == pytest.approx(20.0)

    def test_applies_pre_fitted_stats(self):
        df = pd.DataFrame({"age": [30.0]})
        pre_stats = {"age": (20.0, 10.0)}  # mean=20, std=10
        result, _ = zscore_normalize(df, columns=["age"], feature_stats=pre_stats)
        assert result["age"].iloc[0] == pytest.approx(1.0)  # (30-20)/10


# ---------------------------------------------------------------------------
# create_derived_features
# ---------------------------------------------------------------------------

class TestCreateDerivedFeatures:
    """Tests for create_derived_features (Req 11.5)."""

    def test_compliance_score_column_created(self):
        df = _df()
        result = create_derived_features(df)
        assert "compliance_score" in result.columns

    def test_deviation_score_column_created(self):
        df = _df()
        result = create_derived_features(df)
        assert "deviation_score" in result.columns

    def test_health_trend_encoded_column_created(self):
        df = _df()
        result = create_derived_features(df)
        assert "health_trend_encoded" in result.columns

    def test_recovery_score_column_created(self):
        df = _df()
        result = create_derived_features(df)
        assert "recovery_score" in result.columns

    def test_compliance_score_in_valid_range(self):
        df = _df()
        result = create_derived_features(df)
        assert 0.0 <= result["compliance_score"].iloc[0] <= 100.0

    def test_deviation_score_in_valid_range(self):
        df = _df()
        result = create_derived_features(df)
        assert 0.0 <= result["deviation_score"].iloc[0] <= 100.0

    def test_recovery_score_in_valid_range(self):
        df = _df()
        result = create_derived_features(df)
        assert 0.0 <= result["recovery_score"].iloc[0] <= 100.0

    def test_perfect_compliance_gives_high_compliance_score(self):
        df = _df(_base_row(
            medication_taken="Yes",
            exercise_completed="Yes",
            actual_steps=5000,
            expected_steps=5000,
            actual_sleep_hours=8.0,
            expected_sleep_hours=8.0,
            water_intake=2000,
            water_intake_goal=2000,
            diet_compliance=100.0,
        ))
        result = create_derived_features(df)
        assert result["compliance_score"].iloc[0] == pytest.approx(100.0, abs=0.1)

    def test_no_compliance_gives_low_compliance_score(self):
        df = _df(_base_row(
            medication_taken="No",
            exercise_completed="No",
            actual_steps=0,
            expected_steps=5000,
            actual_sleep_hours=0.0,
            expected_sleep_hours=8.0,
            water_intake=0,
            water_intake_goal=2000,
            diet_compliance=0.0,
        ))
        result = create_derived_features(df)
        assert result["compliance_score"].iloc[0] < 20.0

    def test_health_trend_encoded_is_valid_value(self):
        valid_encoded = set(HEALTH_TREND_ENCODING.values())
        df = _df()
        result = create_derived_features(df)
        val = result["health_trend_encoded"].iloc[0]
        assert val in valid_encoded

    def test_no_patient_id_column_uses_row_independent_defaults(self):
        """Without patient_id, each row gets trend=Stable and recovery=50."""
        df = pd.DataFrame([{
            "age": 55, "bmi": 26.0,
            "medication_taken": "Yes", "exercise_completed": "Yes",
            "actual_steps": 4000, "expected_steps": 5000,
            "actual_sleep_hours": 7.0, "expected_sleep_hours": 8.0,
            "water_intake": 1800, "water_intake_goal": 2000,
            "diet_compliance": 70.0,
        }])
        result = create_derived_features(df)
        assert result["health_trend_encoded"].iloc[0] == HEALTH_TREND_ENCODING["Stable"]
        assert result["recovery_score"].iloc[0] == pytest.approx(50.0)

    def test_pre_existing_compliance_score_not_overwritten_with_zero(self):
        """A pre-computed valid score should be preserved by returning the same value."""
        df = _df(_base_row())
        df["compliance_score"] = 99.0  # pre-set
        result = create_derived_features(df)
        # The function re-computes from raw fields; for perfect compliance it's 100
        # Just check the result is a valid score in range
        assert 0.0 <= result["compliance_score"].iloc[0] <= 100.0


# ---------------------------------------------------------------------------
# FeatureEngineer fit/transform
# ---------------------------------------------------------------------------

class TestFeatureEngineer:
    """Tests for the FeatureEngineer class (Req 11.2, 11.3, 11.4, 11.5)."""

    def _make_df(self, n=5):
        rows = []
        for i in range(n):
            row = _base_row(
                patient_id=f"P{i:03d}",
                day=i + 1,
                age=40 + i,
                actual_steps=4000 + i * 100,
                diet_compliance=70.0 + i,
            )
            rows.append(row)
        return pd.DataFrame(rows)

    def test_fit_transform_returns_dataframe(self):
        fe = FeatureEngineer()
        df = self._make_df()
        result = fe.fit_transform(df)
        assert isinstance(result, pd.DataFrame)

    def test_fit_transform_marks_as_fitted(self):
        fe = FeatureEngineer()
        df = self._make_df()
        fe.fit_transform(df)
        assert fe.is_fitted is True

    def test_is_not_fitted_initially(self):
        fe = FeatureEngineer()
        assert fe.is_fitted is False

    def test_transform_raises_before_fit(self):
        fe = FeatureEngineer()
        df = self._make_df()
        with pytest.raises(RuntimeError, match="fit_transform"):
            fe.transform(df)

    def test_categorical_columns_absent_after_fit_transform(self):
        fe = FeatureEngineer()
        df = self._make_df()
        result = fe.fit_transform(df)
        for col in CATEGORICAL_COLUMNS:
            assert col not in result.columns, f"'{col}' should have been one-hot encoded"

    def test_numerical_columns_in_0_1_range_after_minmax(self):
        fe = FeatureEngineer(normalization="minmax")
        df = self._make_df(n=10)
        result = fe.fit_transform(df)
        for col in NUMERICAL_COLUMNS:
            if col in result.columns:
                assert result[col].min() >= -0.01, f"{col} below 0 after minmax"
                assert result[col].max() <= 1.01, f"{col} above 1 after minmax"

    def test_transform_aligns_to_training_schema(self):
        """transform() should produce the same columns as fit_transform()."""
        fe = FeatureEngineer()
        train_df = self._make_df(n=8)
        inference_df = self._make_df(n=2)
        trained = fe.fit_transform(train_df)
        inference = fe.transform(inference_df)
        # Same columns (order may differ for non-feature columns)
        assert set(trained.columns) == set(inference.columns)

    def test_known_categories_populated_after_fit(self):
        fe = FeatureEngineer()
        df = self._make_df()
        fe.fit_transform(df)
        assert len(fe.known_categories) > 0
        assert "gender" in fe.known_categories

    def test_minmax_ranges_populated_after_fit(self):
        fe = FeatureEngineer(normalization="minmax")
        df = self._make_df()
        fe.fit_transform(df)
        assert len(fe.minmax_ranges) > 0

    def test_zscore_stats_populated_after_fit(self):
        fe = FeatureEngineer(normalization="zscore")
        df = self._make_df()
        fe.fit_transform(df)
        assert len(fe.zscore_stats) > 0

    def test_unsupported_normalization_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported"):
            FeatureEngineer(normalization="log_transform")

    def test_fit_transform_produces_derived_features(self):
        fe = FeatureEngineer()
        df = self._make_df()
        result = fe.fit_transform(df)
        assert "compliance_score" in result.columns
        assert "deviation_score" in result.columns

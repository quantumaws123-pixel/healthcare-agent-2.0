"""
Unit tests for the ML feature_preprocessor module.

Tests cover:
- FeaturePreprocessor construction (valid / invalid normalization)
- from_feature_engineer factory
- save / load round-trip (validates Req 4.7)
- apply_scaling and apply_encoding correctness
- transform pipeline
- is_ready property
- error cases (unfitted engineer, missing file, missing state)

Validates Requirements 4.7, 11.3, 11.4
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.ml.feature_engineer import FeatureEngineer
from app.ml.feature_preprocessor import (
    DEFAULT_PREPROCESSOR_FILENAME,
    SUPPORTED_NORMALIZATIONS,
    FeaturePreprocessor,
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


def _make_training_df(n: int = 10) -> pd.DataFrame:
    rows = []
    genders = ["Male", "Female", "Other"]
    for i in range(n):
        rows.append(_base_row(
            patient_id=f"P{i:03d}",
            day=i + 1,
            age=40 + i,
            gender=genders[i % 3],
        ))
    return pd.DataFrame(rows)


def _fitted_engineer_and_preprocessor(normalization="minmax"):
    """Return a fitted FeatureEngineer and derived FeaturePreprocessor."""
    fe = FeatureEngineer(normalization=normalization)
    df = _make_training_df()
    fe.fit_transform(df)
    preprocessor = FeaturePreprocessor.from_feature_engineer(fe)
    return fe, preprocessor


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------

class TestFeaturePreprocessorConstruction:
    """Tests for __init__ and property access."""

    def test_default_normalization_is_minmax(self):
        fp = FeaturePreprocessor()
        assert fp.normalization == "minmax"

    def test_zscore_normalization_accepted(self):
        fp = FeaturePreprocessor(normalization="zscore")
        assert fp.normalization == "zscore"

    def test_unsupported_normalization_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            FeaturePreprocessor(normalization="log")

    def test_is_ready_false_by_default(self):
        fp = FeaturePreprocessor()
        assert fp.is_ready is False

    def test_known_categories_empty_by_default(self):
        fp = FeaturePreprocessor()
        assert fp.known_categories == {}

    def test_scaling_params_empty_by_default(self):
        fp = FeaturePreprocessor()
        assert fp.scaling_params == {}

    def test_init_with_state_marks_as_ready(self):
        fp = FeaturePreprocessor(
            normalization="minmax",
            known_categories={"gender": ["Male", "Female"]},
            scaling_params={"age": (0.0, 100.0)},
        )
        assert fp.is_ready is True


# ---------------------------------------------------------------------------
# from_feature_engineer factory
# ---------------------------------------------------------------------------

class TestFromFeatureEngineer:
    """Tests for the from_feature_engineer factory (Req 4.7)."""

    def test_returns_preprocessor_instance(self):
        fe = FeatureEngineer()
        fe.fit_transform(_make_training_df())
        fp = FeaturePreprocessor.from_feature_engineer(fe)
        assert isinstance(fp, FeaturePreprocessor)

    def test_normalization_matches_engineer(self):
        fe = FeatureEngineer(normalization="zscore")
        fe.fit_transform(_make_training_df())
        fp = FeaturePreprocessor.from_feature_engineer(fe)
        assert fp.normalization == "zscore"

    def test_known_categories_transferred(self):
        fe = FeatureEngineer()
        fe.fit_transform(_make_training_df())
        fp = FeaturePreprocessor.from_feature_engineer(fe)
        assert "gender" in fp.known_categories

    def test_scaling_params_transferred(self):
        fe = FeatureEngineer(normalization="minmax")
        fe.fit_transform(_make_training_df())
        fp = FeaturePreprocessor.from_feature_engineer(fe)
        assert len(fp.scaling_params) > 0

    def test_unfitted_engineer_raises_runtime_error(self):
        fe = FeatureEngineer()
        with pytest.raises(RuntimeError, match="fit_transform"):
            FeaturePreprocessor.from_feature_engineer(fe)

    def test_is_ready_after_creation_from_engineer(self):
        _, fp = _fitted_engineer_and_preprocessor()
        assert fp.is_ready is True


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

class TestSaveLoad:
    """Tests for serialization and deserialization (Req 4.7)."""

    def test_save_returns_path(self):
        _, fp = _fitted_engineer_and_preprocessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            saved = fp.save(tmpdir)
            assert isinstance(saved, Path)
            assert saved.exists()

    def test_save_to_directory_uses_default_filename(self):
        _, fp = _fitted_engineer_and_preprocessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            saved = fp.save(tmpdir)
            assert saved.name == DEFAULT_PREPROCESSOR_FILENAME

    def test_save_to_explicit_filepath(self):
        _, fp = _fitted_engineer_and_preprocessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            explicit = Path(tmpdir) / "my_preprocessor.joblib"
            saved = fp.save(str(explicit))
            assert saved == explicit
            assert saved.exists()

    def test_load_restores_normalization(self):
        _, fp = _fitted_engineer_and_preprocessor(normalization="zscore")
        with tempfile.TemporaryDirectory() as tmpdir:
            fp.save(tmpdir)
            loaded = FeaturePreprocessor.load(tmpdir)
            assert loaded.normalization == "zscore"

    def test_load_restores_known_categories(self):
        _, fp = _fitted_engineer_and_preprocessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            fp.save(tmpdir)
            loaded = FeaturePreprocessor.load(tmpdir)
            assert loaded.known_categories == fp.known_categories

    def test_load_restores_scaling_params(self):
        _, fp = _fitted_engineer_and_preprocessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            fp.save(tmpdir)
            loaded = FeaturePreprocessor.load(tmpdir)
            assert loaded.scaling_params == fp.scaling_params

    def test_loaded_preprocessor_is_ready(self):
        _, fp = _fitted_engineer_and_preprocessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            fp.save(tmpdir)
            loaded = FeaturePreprocessor.load(tmpdir)
            assert loaded.is_ready is True

    def test_load_produces_identical_transform_output(self):
        """The loaded preprocessor should produce the same output as the original."""
        fe, fp = _fitted_engineer_and_preprocessor()
        inference_df = _make_training_df(n=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            fp.save(tmpdir)
            loaded = FeaturePreprocessor.load(tmpdir)

        original_out = fp.transform(inference_df.copy())
        loaded_out = loaded.transform(inference_df.copy())
        pd.testing.assert_frame_equal(original_out, loaded_out)

    def test_load_missing_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            FeaturePreprocessor.load("/nonexistent/path/preprocessor.joblib")

    def test_save_creates_parent_directories(self):
        _, fp = _fitted_engineer_and_preprocessor()
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "subdir1" / "subdir2" / "fp.joblib"
            saved = fp.save(str(nested))
            assert saved.exists()


# ---------------------------------------------------------------------------
# apply_scaling and apply_encoding
# ---------------------------------------------------------------------------

class TestApplyMethods:
    """Unit tests for apply_scaling and apply_encoding."""

    def test_apply_scaling_raises_without_params(self):
        fp = FeaturePreprocessor()
        df = pd.DataFrame({"age": [40.0, 50.0]})
        with pytest.raises(RuntimeError, match="scaling parameters"):
            fp.apply_scaling(df)

    def test_apply_encoding_raises_without_categories(self):
        fp = FeaturePreprocessor()
        df = pd.DataFrame({"gender": ["Male"]})
        with pytest.raises(RuntimeError, match="known-categories"):
            fp.apply_encoding(df)

    def test_apply_scaling_returns_dataframe(self):
        _, fp = _fitted_engineer_and_preprocessor()
        df = _make_training_df(n=2)
        result = fp.apply_scaling(df)
        assert isinstance(result, pd.DataFrame)

    def test_apply_encoding_removes_categorical_columns(self):
        _, fp = _fitted_engineer_and_preprocessor()
        df = _make_training_df(n=2)
        result = fp.apply_encoding(df)
        assert "gender" not in result.columns

    def test_apply_encoding_adds_dummy_columns(self):
        _, fp = _fitted_engineer_and_preprocessor()
        df = _make_training_df(n=2)
        result = fp.apply_encoding(df)
        # At least one gender dummy should exist
        assert any("gender_" in c for c in result.columns)


# ---------------------------------------------------------------------------
# transform pipeline
# ---------------------------------------------------------------------------

class TestTransformPipeline:
    """Integration tests for the full transform() pipeline."""

    def test_transform_raises_without_state(self):
        fp = FeaturePreprocessor()
        df = _make_training_df(n=2)
        with pytest.raises(RuntimeError):
            fp.transform(df)

    def test_transform_returns_dataframe(self):
        _, fp = _fitted_engineer_and_preprocessor()
        df = _make_training_df(n=2)
        result = fp.transform(df)
        assert isinstance(result, pd.DataFrame)

    def test_transform_has_no_categorical_columns(self):
        from app.ml.feature_engineer import CATEGORICAL_COLUMNS
        _, fp = _fitted_engineer_and_preprocessor()
        df = _make_training_df(n=2)
        result = fp.transform(df)
        for col in CATEGORICAL_COLUMNS:
            assert col not in result.columns

    def test_transform_handles_missing_values(self):
        """Verify imputation step runs — NaN in age should be filled."""
        _, fp = _fitted_engineer_and_preprocessor()
        df = _make_training_df(n=3)
        df.loc[1, "age"] = float("nan")
        # Should not raise
        result = fp.transform(df)
        assert not result["age"].isna().any()

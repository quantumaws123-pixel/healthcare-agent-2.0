"""
Unit tests for the ML inference_engine module.

Tests focus on:
- classify_risk_level (Low/Medium/High/Critical thresholds)
- SHAPExplainer initialization and set_background
- InferenceEngine initialization and is_loaded state

Validates Requirements 4.2, 4.3, 4.5, 4.7
"""

import pytest
import numpy as np

from app.ml.inference_engine import (
    classify_risk_level,
    SHAPExplainer,
    InferenceEngine,
    INFERENCE_TIMEOUT_SECONDS,
    SHAP_BACKGROUND_SAMPLES,
    TOP_N_SHAP_FEATURES,
)


# ---------------------------------------------------------------------------
# classify_risk_level tests
# ---------------------------------------------------------------------------

class TestClassifyRiskLevel:
    """Tests for the classify_risk_level helper function.

    Validates Requirement 4.3:
    - Low: probability < 0.30
    - Medium: 0.30 <= probability < 0.60
    - High: 0.60 <= probability < 0.85
    - Critical: probability >= 0.85
    """

    # --- Low risk ---
    def test_probability_zero_is_low(self):
        assert classify_risk_level(0.0) == "Low"

    def test_probability_just_below_medium_threshold_is_low(self):
        assert classify_risk_level(0.299) == "Low"

    def test_probability_0_15_is_low(self):
        assert classify_risk_level(0.15) == "Low"

    # --- Medium risk ---
    def test_probability_at_medium_lower_boundary_is_medium(self):
        """0.30 exactly is the start of Medium (Req 4.3)."""
        assert classify_risk_level(0.30) == "Medium"

    def test_probability_0_45_is_medium(self):
        assert classify_risk_level(0.45) == "Medium"

    def test_probability_just_below_high_threshold_is_medium(self):
        assert classify_risk_level(0.599) == "Medium"

    # --- High risk ---
    def test_probability_at_high_lower_boundary_is_high(self):
        """0.60 exactly is the start of High (Req 4.3)."""
        assert classify_risk_level(0.60) == "High"

    def test_probability_0_72_is_high(self):
        assert classify_risk_level(0.72) == "High"

    def test_probability_just_below_critical_threshold_is_high(self):
        assert classify_risk_level(0.849) == "High"

    # --- Critical risk ---
    def test_probability_at_critical_lower_boundary_is_critical(self):
        """0.85 exactly is the start of Critical (Req 4.3)."""
        assert classify_risk_level(0.85) == "Critical"

    def test_probability_0_95_is_critical(self):
        assert classify_risk_level(0.95) == "Critical"

    def test_probability_one_is_critical(self):
        assert classify_risk_level(1.0) == "Critical"

    # --- Edge cases: exact boundary values ---
    def test_all_boundaries(self):
        """Verify the 4 tier boundaries produce the expected classifications."""
        assert classify_risk_level(0.0)   == "Low"
        assert classify_risk_level(0.30)  == "Medium"
        assert classify_risk_level(0.60)  == "High"
        assert classify_risk_level(0.85)  == "Critical"

    # --- Invalid inputs ---
    def test_negative_probability_raises_value_error(self):
        with pytest.raises(ValueError):
            classify_risk_level(-0.01)

    def test_probability_above_one_raises_value_error(self):
        with pytest.raises(ValueError):
            classify_risk_level(1.01)

    def test_return_type_is_string(self):
        result = classify_risk_level(0.5)
        assert isinstance(result, str)

    def test_result_is_one_of_four_valid_levels(self):
        valid_levels = {"Low", "Medium", "High", "Critical"}
        for p in [0.0, 0.1, 0.3, 0.45, 0.6, 0.75, 0.85, 1.0]:
            assert classify_risk_level(p) in valid_levels


# ---------------------------------------------------------------------------
# SHAPExplainer initialization tests
# ---------------------------------------------------------------------------

class TestSHAPExplainerInitialization:
    """Tests for SHAPExplainer construction and background setup."""

    def test_default_init_has_no_background(self):
        explainer = SHAPExplainer()
        assert explainer._background is None

    def test_init_with_background_stores_it(self):
        bg = np.zeros((10, 5))
        explainer = SHAPExplainer(background_samples=bg)
        assert explainer._background is not None
        assert explainer._background.shape == (10, 5)

    def test_init_with_feature_names(self):
        names = ["age", "bmi", "heart_rate"]
        explainer = SHAPExplainer(feature_names=names)
        assert explainer.feature_names == names

    def test_set_background_updates_samples(self):
        explainer = SHAPExplainer()
        bg = np.ones((50, 8))
        explainer.set_background(bg)
        assert explainer._background.shape == (50, 8)

    def test_set_background_invalidates_explainer_cache(self):
        """set_background should reset the cached KernelExplainer."""
        explainer = SHAPExplainer()
        explainer._explainer = object()  # simulate a cached explainer
        bg = np.ones((10, 3))
        explainer.set_background(bg)
        assert explainer._explainer is None

    def test_set_background_updates_feature_names(self):
        explainer = SHAPExplainer(feature_names=["a"])
        bg = np.zeros((5, 3))
        explainer.set_background(bg, feature_names=["x", "y", "z"])
        assert explainer.feature_names == ["x", "y", "z"]


# ---------------------------------------------------------------------------
# InferenceEngine initialization tests
# ---------------------------------------------------------------------------

class TestInferenceEngineInitialization:
    """Tests for InferenceEngine initialization and state before load_model."""

    def _make_engine(self):
        """Create an engine with mocked registry and preprocessor."""
        from unittest.mock import MagicMock
        registry = MagicMock()
        preprocessor = MagicMock()
        return InferenceEngine(
            model_registry=registry,
            feature_preprocessor=preprocessor,
        )

    def test_engine_not_loaded_initially(self):
        engine = self._make_engine()
        assert engine.is_loaded is False

    def test_model_is_none_before_load(self):
        engine = self._make_engine()
        assert engine.model is None

    def test_model_version_is_none_before_load(self):
        engine = self._make_engine()
        assert engine.model_version is None

    def test_custom_shap_explainer_stored(self):
        from unittest.mock import MagicMock
        registry = MagicMock()
        preprocessor = MagicMock()
        explainer = SHAPExplainer()
        engine = InferenceEngine(
            model_registry=registry,
            feature_preprocessor=preprocessor,
            shap_explainer=explainer,
        )
        assert engine._shap_explainer is explainer

    def test_default_shap_explainer_created_when_none(self):
        from unittest.mock import MagicMock
        registry = MagicMock()
        preprocessor = MagicMock()
        engine = InferenceEngine(
            model_registry=registry,
            feature_preprocessor=preprocessor,
            shap_explainer=None,
        )
        assert isinstance(engine._shap_explainer, SHAPExplainer)


# ---------------------------------------------------------------------------
# InferenceEngine._build_prediction_result tests (unit, no model needed)
# ---------------------------------------------------------------------------

class TestBuildPredictionResult:
    """Tests for _build_prediction_result using a mock model-loaded engine."""

    def _make_loaded_engine(self):
        from unittest.mock import MagicMock
        registry = MagicMock()
        preprocessor = MagicMock()
        engine = InferenceEngine(
            model_registry=registry,
            feature_preprocessor=preprocessor,
        )
        # Manually set the model to simulate loaded state
        engine._model = MagicMock()
        engine._model_version = "v1.0"
        return engine

    def _make_record(self, **overrides):
        from app.models.schemas import PatientRecord
        base = {
            "patient_id": "P001",
            "age": 55,
            "gender": "Male",
            "bmi": 26.0,
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
        }
        base.update(overrides)
        return PatientRecord(**base)

    def test_risk_level_set_from_probability(self):
        engine = self._make_loaded_engine()
        record = self._make_record()
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.20, row, "unavailable")
        assert result.risk_level == "Low"

    def test_critical_risk_level_from_probability(self):
        engine = self._make_loaded_engine()
        record = self._make_record()
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.90, row, "unavailable")
        assert result.risk_level == "Critical"

    def test_probability_rounded_to_4_decimals(self):
        engine = self._make_loaded_engine()
        record = self._make_record()
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.123456789, row, "unavailable")
        assert result.readmission_probability == round(0.123456789, 4)

    def test_patient_id_preserved(self):
        engine = self._make_loaded_engine()
        record = self._make_record(patient_id="XYZ_999")
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.4, row, "unavailable")
        assert result.patient_id == "XYZ_999"

    def test_shap_unavailable_when_passed(self):
        engine = self._make_loaded_engine()
        record = self._make_record()
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.5, row, "unavailable")
        assert result.shap_explanation == "unavailable"

    def test_pre_computed_scores_used_from_record(self):
        engine = self._make_loaded_engine()
        record = self._make_record(
            compliance_score=85.5,
            deviation_score=12.3,
            ideal_health_score=90.0,
            real_health_score=77.0,
            recovery_score=68.0,
        )
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.4, row, "unavailable")
        assert result.compliance_score == round(85.5, 2)
        assert result.deviation_score == round(12.3, 2)
        assert result.ideal_health_score == round(90.0, 2)
        assert result.real_health_score == round(77.0, 2)
        assert result.recovery_score == round(68.0, 2)

    def test_defaults_used_when_scores_are_none(self):
        engine = self._make_loaded_engine()
        record = self._make_record()  # all score fields default to None
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.4, row, "unavailable")
        assert result.compliance_score == 0.0
        assert result.deviation_score == 0.0

    def test_default_health_trend_when_not_set(self):
        engine = self._make_loaded_engine()
        record = self._make_record()
        row = np.zeros(5)
        result = engine._build_prediction_result(record, 0.4, row, "unavailable")
        assert result.health_trend == "Stable"


# ---------------------------------------------------------------------------
# Constants sanity checks
# ---------------------------------------------------------------------------

class TestConstants:
    """Sanity tests for module-level constants."""

    def test_inference_timeout_is_500ms(self):
        assert INFERENCE_TIMEOUT_SECONDS == 0.5

    def test_shap_background_samples_is_100(self):
        assert SHAP_BACKGROUND_SAMPLES == 100

    def test_top_n_shap_features_is_5(self):
        assert TOP_N_SHAP_FEATURES == 5

"""Inference engine for Healthcare Agent 2.0 Backend ML System.

This module provides the :class:`InferenceEngine` which loads a trained ML
model at startup, preprocesses features at inference time, runs predictions,
classifies risk levels, and optionally computes SHAP explainability values.

It also provides a standalone :class:`SHAPExplainer` used by
:class:`InferenceEngine` for feature attribution.

Responsibilities
----------------
- **load_model**: load the latest (or a specific) trained model from the
  :class:`~app.ml.model_registry.ModelRegistry` into memory at startup.
- **predict**: single-record inference with feature preprocessing, probability
  output, risk-level classification, and SHAP attribution.
- **batch_predict**: vectorised batch inference for multiple patient records.
- **classify_risk_level**: maps a readmission probability to a risk tier.
- Enforces a **500 ms** inference deadline (Requirement 4.5 / 20.3).

Risk Level Classification (Requirement 4.3)
-------------------------------------------
- Low      : probability < 0.30
- Medium   : 0.30 <= probability < 0.60
- High     : 0.60 <= probability < 0.85
- Critical : probability >= 0.85

**Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.7, 20.7**
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, List, Literal, Optional

import numpy as np
import pandas as pd

from app.ml.feature_preprocessor import FeaturePreprocessor
from app.ml.model_registry import ModelRegistry, VERSION_LATEST
from app.models.schemas import (
    PatientRecord,
    PredictionResult,
    SHAPExplanation,
    SHAPFeature,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Hard deadline in seconds for a single predict() call (Requirement 4.5 / 20.3).
INFERENCE_TIMEOUT_SECONDS: float = 0.500

#: Hard deadline in seconds for SHAP computation (Requirement 14.7).
SHAP_TIMEOUT_SECONDS: float = 1.0

#: Number of top features to return in SHAP explanations (Requirement 14.3).
TOP_N_SHAP_FEATURES: int = 5

#: Number of background samples used by SHAP KernelExplainer (Requirement 14.6).
SHAP_BACKGROUND_SAMPLES: int = 100

# ---------------------------------------------------------------------------
# Risk-level classification helper
# ---------------------------------------------------------------------------


def classify_risk_level(
    probability: float,
) -> Literal["Low", "Medium", "High", "Critical"]:
    """Classify a readmission probability into a named risk tier.

    Thresholds (Requirement 4.3):
    - **Low**      : probability < 0.30
    - **Medium**   : 0.30 <= probability < 0.60
    - **High**     : 0.60 <= probability < 0.85
    - **Critical** : probability >= 0.85

    Args:
        probability: Readmission probability in [0, 1].

    Returns:
        One of ``"Low"``, ``"Medium"``, ``"High"``, or ``"Critical"``.

    Raises:
        ValueError: If *probability* is outside [0, 1].

    **Validates: Requirement 4.3**
    """
    if not (0.0 <= probability <= 1.0):
        raise ValueError(
            f"Probability must be in [0, 1]; received {probability!r}."
        )
    if probability >= 0.85:
        return "Critical"
    if probability >= 0.60:
        return "High"
    if probability >= 0.30:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# SHAPExplainer
# ---------------------------------------------------------------------------


class SHAPExplainer:
    """Computes SHAP values for ML model explainability.

    Uses ``shap.KernelExplainer`` with a representative background dataset of
    :data:`SHAP_BACKGROUND_SAMPLES` samples (Requirement 14.6).  The
    explainer is initialised lazily on the first call to :meth:`explain` so
    that the class can be instantiated before inference data is available.

    **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.6**
    """

    def __init__(
        self,
        background_samples: Optional[np.ndarray] = None,
        feature_names: Optional[list[str]] = None,
    ) -> None:
        """Initialise the explainer.

        Args:
            background_samples: Representative background dataset (shape
                ``[n_samples, n_features]``) used by KernelExplainer.
                When ``None`` a minimal zero-filled placeholder is stored
                and the explainer will be initialised on first use.
            feature_names: Ordered list of feature column names.  Used to
                label SHAP output features for the API response.
        """
        self._background: Optional[np.ndarray] = background_samples
        self.feature_names: list[str] = feature_names or []
        self._explainer: Any = None  # shap.KernelExplainer — initialised lazily

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def set_background(
        self,
        background_samples: np.ndarray,
        feature_names: Optional[list[str]] = None,
    ) -> None:
        """Update the background dataset and invalidate the cached explainer.

        Call this after :meth:`InferenceEngine.load_model` with the
        training-data background slice.

        Args:
            background_samples: Array of shape ``[n_samples, n_features]``.
            feature_names: Updated feature name list.
        """
        self._background = background_samples
        if feature_names is not None:
            self.feature_names = feature_names
        # Invalidate cached explainer so it is rebuilt with new background
        self._explainer = None
        logger.info(
            "SHAPExplainer background updated: %d samples, %d features.",
            background_samples.shape[0],
            background_samples.shape[1],
        )

    async def explain(
        self,
        model: Any,
        features: np.ndarray,
    ) -> SHAPExplanation:
        """Compute SHAP values and return the top contributing features.

        The computation is offloaded to a thread-pool executor so the async
        event loop is not blocked.  A :data:`SHAP_TIMEOUT_SECONDS` deadline is
        enforced; if exceeded the result is logged and the caller should fall
        back to ``"unavailable"``.

        Algorithm (Requirement 14.1):
        1. Initialise :class:`shap.KernelExplainer` with the stored background.
        2. Compute SHAP values for the input *features* array.
        3. Rank features by absolute SHAP value magnitude.
        4. Return the top :data:`TOP_N_SHAP_FEATURES` with name, value, and
           direction (Requirement 14.4).

        Args:
            model: Trained model with a ``predict_proba`` or ``predict``
                callable accepted by SHAP.
            features: 2-D feature array ``[1, n_features]`` for the patient.

        Returns:
            :class:`~app.models.schemas.SHAPExplanation` with top features.

        Raises:
            asyncio.TimeoutError: If computation exceeds :data:`SHAP_TIMEOUT_SECONDS`.
            RuntimeError: If SHAP is not installed or the explainer fails.

        **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.6**
        """
        loop = asyncio.get_event_loop()
        try:
            shap_result = await asyncio.wait_for(
                loop.run_in_executor(None, self._compute_shap_sync, model, features),
                timeout=SHAP_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "SHAP computation exceeded %.1fs timeout; returning unavailable.",
                SHAP_TIMEOUT_SECONDS,
            )
            raise
        return shap_result

    # ------------------------------------------------------------------
    # Internal synchronous helpers (run in executor)
    # ------------------------------------------------------------------

    def _build_explainer(self, model: Any) -> Any:
        """Lazily build and cache the KernelExplainer.

        Args:
            model: Model object accepted by shap.KernelExplainer.

        Returns:
            Initialised ``shap.KernelExplainer`` instance.
        """
        try:
            import shap  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "SHAP is not installed. Run: pip install shap"
            ) from exc

        if self._background is None:
            # Fallback: single-sample zero background to allow instantiation
            logger.warning(
                "No background dataset set; using zero-filled placeholder "
                "for SHAP KernelExplainer.  Call set_background() for accuracy."
            )
            n_features = 1
            self._background = np.zeros((1, n_features))

        # Choose prediction function based on model type
        if hasattr(model, "predict_proba"):
            predict_fn = lambda x: model.predict_proba(x)[:, 1]  # noqa: E731
        else:
            predict_fn = model.predict

        self._explainer = shap.KernelExplainer(
            predict_fn,
            self._background,
            link="identity",
        )
        logger.debug("SHAP KernelExplainer built with %d background samples.", self._background.shape[0])
        return self._explainer

    def _compute_shap_sync(
        self,
        model: Any,
        features: np.ndarray,
    ) -> SHAPExplanation:
        """Synchronous SHAP computation (runs in thread executor).

        Args:
            model: Trained model object.
            features: 2-D array ``[1, n_features]``.

        Returns:
            :class:`~app.models.schemas.SHAPExplanation` with top-5 features.
        """
        if self._explainer is None:
            self._build_explainer(model)

        shap_values = self._explainer.shap_values(features, nsamples=100, silent=True)

        # shap_values may be nested (list for classifiers) — unwrap
        if isinstance(shap_values, list):
            shap_array = np.array(shap_values[1] if len(shap_values) > 1 else shap_values[0])
        else:
            shap_array = np.array(shap_values)

        # Flatten to 1-D for single-record input
        shap_flat: np.ndarray = shap_array.flatten()

        # Rank by absolute magnitude
        abs_vals = np.abs(shap_flat)
        sorted_indices = np.argsort(abs_vals)[::-1][:TOP_N_SHAP_FEATURES]

        top_features: list[SHAPFeature] = []
        for idx in sorted_indices:
            val = float(shap_flat[idx])
            name = (
                self.feature_names[int(idx)]
                if self.feature_names and int(idx) < len(self.feature_names)
                else f"feature_{idx}"
            )
            direction: Literal["positive", "negative"] = "positive" if val >= 0 else "negative"
            top_features.append(
                SHAPFeature(
                    feature_name=name,
                    shap_value=round(val, 6),
                    direction=direction,
                )
            )

        logger.debug(
            "SHAP computed %d feature attributions; top feature: %s (%.4f).",
            len(shap_flat),
            top_features[0].feature_name if top_features else "n/a",
            top_features[0].shap_value if top_features else 0.0,
        )
        return SHAPExplanation(top_features=top_features)


# ---------------------------------------------------------------------------
# InferenceEngine
# ---------------------------------------------------------------------------


class InferenceEngine:
    """Manages ML model inference, preprocessing, and SHAP explainability.

    Lifecycle
    ---------
    1. Instantiate with a :class:`~app.ml.model_registry.ModelRegistry` and a
       :class:`~app.ml.feature_preprocessor.FeaturePreprocessor`.
    2. Call :meth:`load_model` at application startup to pull the latest model
       into memory (Requirement 4.1).
    3. Call :meth:`predict` or :meth:`batch_predict` for inference.

    Thread-safety
    -------------
    The engine holds a reference to the active model.  Model hot-swapping
    (:meth:`load_model` called while requests are in-flight) is safe because
    Python attribute assignment is atomic and the old model object remains
    alive until all coroutines holding a local reference to it complete.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.7, 20.7**
    """

    def __init__(
        self,
        model_registry: ModelRegistry,
        feature_preprocessor: FeaturePreprocessor,
        shap_explainer: Optional[SHAPExplainer] = None,
    ) -> None:
        """Initialise the engine.

        Args:
            model_registry: Manages model versioning and on-disk retrieval.
            feature_preprocessor: Applies training-consistent transformations
                at inference time (Requirement 4.7).
            shap_explainer: Optional :class:`SHAPExplainer` instance.  When
                ``None`` a new one is created automatically; SHAP results will
                be ``"unavailable"`` until a background dataset is supplied via
                :meth:`SHAPExplainer.set_background`.
        """
        self._registry = model_registry
        self._preprocessor = feature_preprocessor
        self._shap_explainer: SHAPExplainer = shap_explainer or SHAPExplainer()

        # Active model state — populated by load_model()
        self._model: Any = None
        self._model_version: Optional[str] = None
        self._model_type: Optional[str] = None
        self._feature_columns: Optional[list[str]] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def model(self) -> Any:
        """The currently loaded model object (``None`` before :meth:`load_model`)."""
        return self._model

    @property
    def model_version(self) -> Optional[str]:
        """Version string of the active model."""
        return self._model_version

    @property
    def is_loaded(self) -> bool:
        """``True`` once a model has been successfully loaded."""
        return self._model is not None

    # ------------------------------------------------------------------
    # load_model
    # ------------------------------------------------------------------

    async def load_model(self, version: str = VERSION_LATEST) -> None:
        """Load a trained model from the registry into memory.

        Should be called once during application startup via FastAPI's
        ``lifespan`` event so that the model is warm before the first request
        arrives (Requirement 4.1).  Can also be called at runtime to hot-swap
        model versions without restarting the server (Requirement 16.3).

        Args:
            version: Semantic version string (e.g. ``"v1.2"``) or
                :data:`~app.ml.model_registry.VERSION_LATEST` (default).

        Raises:
            ValueError: If no matching model is found in the registry.
            FileNotFoundError: If the model artefact is missing on disk.
            RuntimeError: If the registry raises an unexpected error.

        **Validates: Requirement 4.1**
        """
        logger.info("InferenceEngine.load_model: loading version='%s' …", version)

        loop = asyncio.get_event_loop()
        model, db_record = await self._registry.load_model(version)

        self._model = model
        self._model_version = db_record.model_version
        self._model_type = db_record.model_type

        # Persist feature columns from registry metadata if available
        # (stored in the JSON sidecar during training)
        self._feature_columns = None  # will be resolved lazily at first predict

        logger.info(
            "InferenceEngine: loaded model version='%s' type='%s'.",
            self._model_version,
            self._model_type,
        )

    # ------------------------------------------------------------------
    # _preprocess
    # ------------------------------------------------------------------

    def _preprocess_records(
        self,
        records: List[PatientRecord],
    ) -> tuple[np.ndarray, list[str]]:
        """Convert patient records to a feature matrix via the preprocessor.

        Steps (Requirement 4.7):
        1. Serialise each :class:`~app.models.schemas.PatientRecord` to a dict
           and build a :class:`pandas.DataFrame`.
        2. Apply :meth:`FeaturePreprocessor.transform` (imputation, derived
           features, one-hot encoding, scaling).
        3. Drop non-feature columns (ids, text outputs, day).
        4. Return the feature matrix as a NumPy array and the column list.

        Args:
            records: One or more patient records.

        Returns:
            Tuple ``(X, feature_columns)`` where *X* has shape
            ``[len(records), n_features]``.
        """
        # Build raw DataFrame from Pydantic models
        rows = [r.model_dump() for r in records]
        df = pd.DataFrame(rows)

        # Apply inference-time preprocessing (consistent with training)
        df_transformed = self._preprocessor.transform(df)

        # Drop columns that are outputs / identifiers, not ML features
        _non_feature_cols = {
            "patient_id", "patient_name", "day", "created_at", "updated_at",
            "risk_level", "health_trend", "recovery_status",
            "doctor_recommendation", "readmission_probability",
            "readmission_target",
        }
        feature_cols = [c for c in df_transformed.columns if c not in _non_feature_cols]
        X = df_transformed[feature_cols].values.astype(float)

        # Cache feature column order for SHAP labelling
        if self._feature_columns is None:
            self._feature_columns = feature_cols
            self._shap_explainer.feature_names = feature_cols

        return X, feature_cols

    # ------------------------------------------------------------------
    # _run_inference
    # ------------------------------------------------------------------

    def _run_inference_sync(self, X: np.ndarray) -> np.ndarray:
        """Run synchronous model inference and return a probability vector.

        Supports scikit-learn / XGBoost estimators (``predict_proba``) and
        TensorFlow/Keras models (``predict``).

        Args:
            X: Feature matrix of shape ``[n_samples, n_features]``.

        Returns:
            1-D NumPy array of readmission probabilities in [0, 1].
        """
        if hasattr(self._model, "predict_proba"):
            # scikit-learn / XGBoost sklearn API
            proba = self._model.predict_proba(X)
            if proba.ndim == 2:
                return proba[:, 1].astype(float)
            return proba.astype(float)

        # TensorFlow/Keras model
        raw = self._model.predict(X, verbose=0)
        return raw.flatten().astype(float)

    async def _run_inference_async(self, X: np.ndarray) -> np.ndarray:
        """Run model inference in a thread executor to avoid blocking the loop.

        Args:
            X: Feature matrix.

        Returns:
            1-D probability array.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_inference_sync, X)

    # ------------------------------------------------------------------
    # _build_prediction_result
    # ------------------------------------------------------------------

    def _build_prediction_result(
        self,
        record: PatientRecord,
        probability: float,
        preprocessed_row: np.ndarray,
        shap_explanation: Any,
    ) -> PredictionResult:
        """Assemble a :class:`~app.models.schemas.PredictionResult` from inference outputs.

        Computed scores that are already available on the record (set by the
        digital-twin engine upstream) are used directly; otherwise sensible
        defaults are applied so the response is always well-formed.

        Args:
            record: Original patient record.
            probability: Scalar readmission probability from the model.
            preprocessed_row: 1-D feature array (used for field extraction).
            shap_explanation: :class:`SHAPExplanation` or ``"unavailable"``.

        Returns:
            Fully populated :class:`~app.models.schemas.PredictionResult`.
        """
        risk_level = classify_risk_level(probability)

        # Use pre-computed scores when available on the input record
        compliance = float(record.compliance_score or 0.0)
        deviation = float(record.deviation_score or 0.0)
        ideal_hs = float(record.ideal_health_score or 0.0)
        real_hs = float(record.real_health_score or 0.0)
        recovery = float(record.recovery_score or 0.0)
        health_trend = record.health_trend or "Stable"
        recovery_status = record.recovery_status or "Stable"
        recommendation = record.doctor_recommendation or "Continue Current Treatment"

        return PredictionResult(
            patient_id=record.patient_id,
            readmission_probability=round(probability, 4),
            risk_level=risk_level,
            recovery_status=recovery_status,
            health_trend=health_trend,
            compliance_score=round(compliance, 2),
            deviation_score=round(deviation, 2),
            ideal_health_score=round(ideal_hs, 2),
            real_health_score=round(real_hs, 2),
            recovery_score=round(recovery, 2),
            doctor_recommendation=recommendation,
            shap_explanation=shap_explanation,
        )

    # ------------------------------------------------------------------
    # predict
    # ------------------------------------------------------------------

    async def predict(
        self,
        patient_record: PatientRecord,
    ) -> PredictionResult:
        """Generate a readmission prediction for a single patient record.

        The full pipeline must complete within :data:`INFERENCE_TIMEOUT_SECONDS`
        (500 ms).  If the deadline is exceeded :exc:`asyncio.TimeoutError` is
        raised so the API layer can return HTTP 500 (Requirement 4.6).

        Algorithm:
        1. Validate model is loaded.
        2. Pre-process features (scaling + encoding) via :class:`FeaturePreprocessor`.
        3. Run model inference -> readmission probability in [0, 1].
        4. Classify risk level from probability thresholds.
        5. Attempt SHAP attribution; fall back to ``"unavailable"`` on error.
        6. Assemble and return :class:`~app.models.schemas.PredictionResult`.

        Args:
            patient_record: Validated patient data from the API request.

        Returns:
            :class:`~app.models.schemas.PredictionResult`.

        Raises:
            RuntimeError: If no model is loaded.
            asyncio.TimeoutError: If inference exceeds 500 ms.

        **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 4.7**
        """
        if not self.is_loaded:
            raise RuntimeError(
                "InferenceEngine has no model loaded. "
                "Call load_model() at startup before serving prediction requests."
            )

        start_ts = time.monotonic()
        logger.info(
            "InferenceEngine.predict: patient_id='%s'.", patient_record.patient_id
        )

        async def _run() -> PredictionResult:
            # Step 1 – Preprocess
            X, feat_cols = self._preprocess_records([patient_record])

            # Step 2 – Inference
            probabilities = await self._run_inference_async(X)
            probability = float(np.clip(probabilities[0], 0.0, 1.0))

            # Step 3 – SHAP attribution
            shap_explanation: Any = "unavailable"
            try:
                shap_explanation = await self._shap_explainer.explain(
                    self._model, X[0:1]
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "SHAP timed out for patient_id='%s'; returning 'unavailable'.",
                    patient_record.patient_id,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "SHAP failed for patient_id='%s': %s; returning 'unavailable'.",
                    patient_record.patient_id,
                    exc,
                )

            # Step 4 – Assemble result
            result = self._build_prediction_result(
                patient_record, probability, X[0], shap_explanation
            )

            elapsed_ms = (time.monotonic() - start_ts) * 1000
            logger.info(
                "InferenceEngine.predict complete: patient_id='%s' "
                "probability=%.4f risk_level='%s' elapsed=%.1f ms.",
                patient_record.patient_id,
                probability,
                result.risk_level,
                elapsed_ms,
            )
            return result

        # Enforce the 500 ms deadline
        try:
            result = await asyncio.wait_for(
                _run(),
                timeout=INFERENCE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            elapsed_ms = (time.monotonic() - start_ts) * 1000
            logger.error(
                "InferenceEngine.predict TIMED OUT for patient_id='%s' "
                "after %.1f ms (limit=%.0f ms).",
                patient_record.patient_id,
                elapsed_ms,
                INFERENCE_TIMEOUT_SECONDS * 1000,
            )
            raise

        return result

    # ------------------------------------------------------------------
    # batch_predict
    # ------------------------------------------------------------------

    async def batch_predict(
        self,
        patient_records: List[PatientRecord],
    ) -> List[PredictionResult]:
        """Optimised batch inference for multiple patient records.

        All records are preprocessed and run through the model in a single
        vectorised call for efficiency (Requirement 20.7).  SHAP attribution
        is performed per-record after the batch inference; SHAP failures are
        silenced individually and reported as ``"unavailable"``.

        The overall batch is *not* subject to the single-record 500 ms
        deadline; callers are responsible for applying appropriate timeouts
        at the API layer.

        Args:
            patient_records: List of validated patient records to process.

        Returns:
            Ordered list of :class:`~app.models.schemas.PredictionResult`
            objects, one per input record in the same order.

        Raises:
            RuntimeError: If no model is loaded.
            ValueError: If *patient_records* is empty.

        **Validates: Requirements 4.2, 4.3, 4.7, 20.7**
        """
        if not self.is_loaded:
            raise RuntimeError(
                "InferenceEngine has no model loaded. "
                "Call load_model() before batch_predict()."
            )

        if not patient_records:
            raise ValueError("patient_records must not be empty.")

        n = len(patient_records)
        start_ts = time.monotonic()
        logger.info("InferenceEngine.batch_predict: %d record(s).", n)

        # Step 1 – Vectorised preprocessing
        X, feat_cols = self._preprocess_records(patient_records)

        # Step 2 – Vectorised inference
        probabilities = await self._run_inference_async(X)
        probabilities = np.clip(probabilities, 0.0, 1.0)

        # Step 3 – SHAP per record (best-effort; non-blocking failures)
        shap_results: list[Any] = []
        for i in range(n):
            shap_val: Any = "unavailable"
            try:
                shap_val = await self._shap_explainer.explain(
                    self._model, X[i : i + 1]
                )
            except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
                logger.debug(
                    "SHAP unavailable for batch record %d (patient_id='%s'): %s",
                    i,
                    patient_records[i].patient_id,
                    exc,
                )
            shap_results.append(shap_val)

        # Step 4 – Assemble results
        results: list[PredictionResult] = []
        for i, record in enumerate(patient_records):
            result = self._build_prediction_result(
                record,
                float(probabilities[i]),
                X[i],
                shap_results[i],
            )
            results.append(result)

        elapsed_ms = (time.monotonic() - start_ts) * 1000
        logger.info(
            "InferenceEngine.batch_predict complete: %d record(s) in %.1f ms "
            "(avg %.1f ms/record).",
            n,
            elapsed_ms,
            elapsed_ms / n,
        )
        return results

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InferenceEngine("
            f"model_version={self._model_version!r}, "
            f"model_type={self._model_type!r}, "
            f"is_loaded={self.is_loaded})"
        )

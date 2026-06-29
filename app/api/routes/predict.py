"""Prediction API route handler for Healthcare Agent 2.0 Backend ML System.

Implements:
  - POST /predict  — full prediction pipeline combining the Digital Twin Engine,
    Prediction System, Recommendation Engine, and ML Inference Engine.

**Validates: Requirements 1.3, 1.7, 4.1, 4.2, 4.3, 4.4**
"""

import asyncio
import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.models.schemas import PatientRecord
from app.services.digital_twin_engine import DigitalTwinEngine
from app.services.prediction_system import PredictionSystem
from app.services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["predictions"])


# ---------------------------------------------------------------------------
# Frontend-aligned response models
# ---------------------------------------------------------------------------


class ShapFeature(BaseModel):
    """Individual SHAP feature attribution — matches TypeScript ShapFeature."""

    feature: str
    shap_value: float
    direction: Literal["positive", "negative"]


class FrontendPredictionResult(BaseModel):
    """
    Prediction response shaped to exactly match the TypeScript
    ``PredictionResponse`` interface consumed by the frontend.

    Field names are PascalCase to align with the frontend types.
    ``populate_by_name=True`` lets the model be constructed with either
    the alias or the Python attribute name.
    """

    model_config = ConfigDict(populate_by_name=True)

    Risk_Level: str = Field(..., alias="Risk_Level", serialization_alias="Risk_Level")
    Recovery_Status: str = Field(..., alias="Recovery_Status", serialization_alias="Recovery_Status")
    Doctor_Recommendation: str = Field(..., alias="Doctor_Recommendation", serialization_alias="Doctor_Recommendation")
    Readmission_Probability: float = Field(..., alias="Readmission_Probability", serialization_alias="Readmission_Probability")
    shap_features: Optional[list[ShapFeature]] = Field(default=None)
    explainability: Literal["available", "unavailable"] = Field(default="unavailable")


# ---------------------------------------------------------------------------
# POST /predict
# ---------------------------------------------------------------------------


@router.post(
    "/predict",
    response_model=FrontendPredictionResult,
    response_model_by_alias=True,
    summary="Generate readmission prediction for a patient record",
    description=(
        "Accepts a complete patient record, runs it through the Digital Twin "
        "Engine to compute compliance and health scores, classifies recovery "
        "status and health trend, generates an ML-based readmission probability "
        "with SHAP explanation, and produces a clinical recommendation. "
        "Returns a FrontendPredictionResult with PascalCase field names."
    ),
)
async def predict(
    record: PatientRecord,
    request: Request,
) -> FrontendPredictionResult:
    """
    POST /predict

    Full prediction pipeline:

    1. Compute deviation metrics (Digital Twin Engine).
    2. Compute health scores — ideal, real, deviation, recovery.
    3. Analyze health trend from historical records (empty list for single-record requests).
    4. Classify recovery status.
    5. Run ML inference to get readmission probability and SHAP explanation.
    6. Generate clinical recommendation.
    7. Return a fully populated PredictionResult.

    **Validates: Requirements 1.3, 1.7, 4.1, 4.2, 4.3, 4.4**
    """
    # ------------------------------------------------------------------
    # Step 1 – Instantiate service objects
    # ------------------------------------------------------------------
    digital_twin = DigitalTwinEngine()
    prediction_system = PredictionSystem()
    recommendation_engine = RecommendationEngine()

    # ------------------------------------------------------------------
    # Step 2 – Digital Twin: compute deviations and health scores
    # ------------------------------------------------------------------
    try:
        deviations = await digital_twin.compute_deviations(record)
    except Exception as exc:
        logger.error(
            "Digital twin deviation computation failed for patient '%s': %s",
            record.patient_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to compute deviation metrics",
        ) from exc

    # No historical records available in a single-record prediction request;
    # an empty list causes health score / trend calculations to use safe defaults.
    historical_records: list[PatientRecord] = []

    try:
        health_scores = await digital_twin.compute_health_scores(
            record, historical_records
        )
    except Exception as exc:
        logger.error(
            "Health score computation failed for patient '%s': %s",
            record.patient_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to compute health scores",
        ) from exc

    compliance_score = 100.0 - deviations.overall_deviation_score
    deviation_score = deviations.overall_deviation_score

    # ------------------------------------------------------------------
    # Step 3 – Analyze health trend
    # ------------------------------------------------------------------
    try:
        health_trend = await prediction_system.analyze_health_trend(historical_records)
    except Exception as exc:
        logger.error(
            "Health trend analysis failed for patient '%s': %s",
            record.patient_id,
            exc,
            exc_info=True,
        )
        health_trend = "Stable"

    # ------------------------------------------------------------------
    # Step 4 – Classify recovery status
    # ------------------------------------------------------------------
    try:
        recovery_status = await prediction_system.classify_recovery_status(
            recovery_score=health_scores.recovery_score,
            health_trend=health_trend,
            risk_level="Low",  # Temporary; updated after ML inference below
        )
    except Exception as exc:
        logger.error(
            "Recovery status classification failed for patient '%s': %s",
            record.patient_id,
            exc,
            exc_info=True,
        )
        recovery_status = "Stable"

    # ------------------------------------------------------------------
    # Step 5 – ML inference (InferenceEngine stored on app.state)
    # ------------------------------------------------------------------
    inference_engine = getattr(request.app.state, "inference_engine", None)

    readmission_probability: float
    risk_level: str
    shap_explanation = "unavailable"

    if inference_engine is None or not inference_engine.is_loaded:
        # Graceful degradation: no model available, return rule-based defaults
        logger.warning(
            "InferenceEngine not available or model not loaded for patient '%s'; "
            "returning default risk assessment.",
            record.patient_id,
        )
        # Derive a simple heuristic risk level from deviation and health scores
        if deviation_score >= 40:
            readmission_probability = 0.70
            risk_level = "High"
        elif deviation_score >= 20:
            readmission_probability = 0.45
            risk_level = "Medium"
        else:
            readmission_probability = 0.15
            risk_level = "Low"
    else:
        # Attach pre-computed scores to the record before inference so the
        # InferenceEngine's _build_prediction_result can use them directly.
        enriched_record = record.model_copy(
            update={
                "compliance_score": round(compliance_score, 2),
                "ideal_health_score": round(health_scores.ideal_health_score, 2),
                "real_health_score": round(health_scores.real_health_score, 2),
                "deviation_score": round(deviation_score, 2),
                "recovery_score": round(health_scores.recovery_score, 2),
                "health_trend": health_trend,
                "recovery_status": recovery_status,
            }
        )

        try:
            inference_result = await inference_engine.predict(enriched_record)
            readmission_probability = inference_result.readmission_probability
            risk_level = inference_result.risk_level
            shap_explanation = inference_result.shap_explanation
        except asyncio.TimeoutError:
            logger.error(
                "ML inference timed out for patient '%s'.", record.patient_id
            )
            raise HTTPException(
                status_code=500,
                detail="Prediction timed out; please retry",
            )
        except RuntimeError as exc:
            logger.error(
                "ML inference runtime error for patient '%s': %s",
                record.patient_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=503,
                detail="ML model unavailable; cannot generate prediction",
            ) from exc
        except Exception as exc:
            logger.error(
                "Unexpected inference error for patient '%s': %s",
                record.patient_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal error during prediction",
            ) from exc

    # ------------------------------------------------------------------
    # Step 6 – Re-classify recovery status using the real risk level
    # ------------------------------------------------------------------
    try:
        recovery_status = await prediction_system.classify_recovery_status(
            recovery_score=health_scores.recovery_score,
            health_trend=health_trend,
            risk_level=risk_level,
        )
    except Exception as exc:
        logger.warning(
            "Second recovery status classification failed for patient '%s': %s",
            record.patient_id,
            exc,
        )
        # Keep the earlier value

    # ------------------------------------------------------------------
    # Step 7 – Generate clinical recommendation
    # ------------------------------------------------------------------
    try:
        doctor_recommendation = await recommendation_engine.generate_recommendation(
            risk_level=risk_level,
            recovery_status=recovery_status,
            compliance_score=compliance_score,
            deviation_score=deviation_score,
            readmission_probability=readmission_probability,
            patient_id=record.patient_id,
        )
    except Exception as exc:
        logger.error(
            "Recommendation generation failed for patient '%s': %s",
            record.patient_id,
            exc,
            exc_info=True,
        )
        doctor_recommendation = "Continue Current Treatment"

    # ------------------------------------------------------------------
    # Step 8 – Assemble and return FrontendPredictionResult
    # ------------------------------------------------------------------

    # Convert SHAP explanation to the frontend-expected format
    shap_features: list[ShapFeature] | None = None
    explainability: Literal["available", "unavailable"] = "unavailable"

    if shap_explanation and shap_explanation != "unavailable":
        try:
            # shap_explanation may be a SHAPExplanation model or a dict-like structure
            raw_features = None
            if hasattr(shap_explanation, "top_features"):
                raw_features = shap_explanation.top_features
            elif isinstance(shap_explanation, dict) and "top_features" in shap_explanation:
                raw_features = shap_explanation["top_features"]

            if raw_features:
                shap_features = []
                for feat in raw_features:
                    if hasattr(feat, "feature_name"):
                        shap_features.append(
                            ShapFeature(
                                feature=feat.feature_name,
                                shap_value=feat.shap_value,
                                direction=feat.direction,
                            )
                        )
                    elif isinstance(feat, dict):
                        shap_features.append(
                            ShapFeature(
                                feature=feat.get("feature_name", feat.get("feature", "")),
                                shap_value=feat.get("shap_value", 0.0),
                                direction=feat.get("direction", "positive"),
                            )
                        )
                explainability = "available"
        except Exception as exc:
            logger.warning(
                "Failed to convert SHAP explanation for patient '%s': %s",
                record.patient_id,
                exc,
            )
            shap_features = None
            explainability = "unavailable"

    return FrontendPredictionResult.model_validate(
        {
            "Risk_Level": risk_level,
            "Recovery_Status": recovery_status,
            "Doctor_Recommendation": doctor_recommendation,
            "Readmission_Probability": round(readmission_probability, 4),
            "shap_features": shap_features,
            "explainability": explainability,
        }
    )

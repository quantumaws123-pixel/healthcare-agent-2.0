"""Model info API route handler for Healthcare Agent 2.0 Backend ML System.

Implements:
  - GET /model/info  — returns current ML model version and metadata.

**Validates: Requirement 16.5**
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["model"])


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class EvaluationMetrics(BaseModel):
    """ML model evaluation metrics."""

    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None


class ModelInfoResponse(BaseModel):
    """Response body for GET /model/info."""

    model_config = {"protected_namespaces": ()}

    model_version: str
    model_type: str
    training_date: str
    dataset_size: int
    evaluation_metrics: EvaluationMetrics


# ---------------------------------------------------------------------------
# Default placeholder returned when no model is loaded
# ---------------------------------------------------------------------------

_DEFAULT_MODEL_INFO: dict[str, Any] = {
    "model_version": "N/A",
    "model_type": "N/A",
    "training_date": "N/A",
    "dataset_size": 0,
    "evaluation_metrics": {
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1_score": None,
        "auc_roc": None,
    },
}


# ---------------------------------------------------------------------------
# GET /model/info
# ---------------------------------------------------------------------------


@router.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="Get current ML model version and metadata",
    description=(
        "Returns the version, architecture type, training date, dataset size, "
        "and evaluation metrics of the currently loaded ML model. "
        "When no model has been loaded, placeholder values are returned."
    ),
)
async def get_model_info(request: Request) -> ModelInfoResponse:
    """
    GET /model/info

    Retrieves metadata for the currently active ML model from the InferenceEngine
    stored on app.state. Falls back to a default placeholder response when the
    inference engine is not available or no model has been loaded.

    **Validates: Requirement 16.5**
    """
    inference_engine = getattr(request.app.state, "inference_engine", None)

    if inference_engine is None or not inference_engine.is_loaded:
        logger.info(
            "GET /model/info: InferenceEngine not available or model not loaded; "
            "returning placeholder response."
        )
        info = _DEFAULT_MODEL_INFO
    else:
        # Retrieve info from the engine's registry via the loaded model metadata.
        # The InferenceEngine exposes model_version and model_type as properties;
        # for full metadata we delegate to ModelRegistry.get_model_info if reachable.
        try:
            registry = getattr(inference_engine, "_registry", None)
            if registry is not None:
                info = await registry.get_model_info(version="latest")
            else:
                # Fallback: build partial info from InferenceEngine properties
                info = {
                    "model_version": inference_engine.model_version or "N/A",
                    "model_type": getattr(inference_engine, "_model_type", None) or "N/A",
                    "training_date": "N/A",
                    "dataset_size": 0,
                    "evaluation_metrics": {
                        "accuracy": None,
                        "precision": None,
                        "recall": None,
                        "f1_score": None,
                        "auc_roc": None,
                    },
                }
        except Exception as exc:
            logger.warning(
                "Could not retrieve model metadata from registry: %s; "
                "returning partial info.",
                exc,
            )
            info = {
                "model_version": inference_engine.model_version or "N/A",
                "model_type": getattr(inference_engine, "_model_type", None) or "N/A",
                "training_date": "N/A",
                "dataset_size": 0,
                "evaluation_metrics": {
                    "accuracy": None,
                    "precision": None,
                    "recall": None,
                    "f1_score": None,
                    "auc_roc": None,
                },
            }

    logger.info(
        "GET /model/info: model_version='%s', model_type='%s'.",
        info.get("model_version"),
        info.get("model_type"),
    )

    return ModelInfoResponse(
        model_version=info["model_version"],
        model_type=info["model_type"],
        training_date=info["training_date"],
        dataset_size=info["dataset_size"],
        evaluation_metrics=EvaluationMetrics(**info["evaluation_metrics"]),
    )

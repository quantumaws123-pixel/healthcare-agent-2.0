"""
API endpoints and route handlers for Healthcare Agent 2.0 Backend ML System.
"""

from app.api.routes.patients import router as patients_router
from app.api.routes.predict import router as predict_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.model import router as model_router

__all__ = [
    "patients_router",
    "predict_router",
    "dashboard_router",
    "model_router",
]

"""
Exception handlers for the Healthcare Agent 2.0 Backend API.

Provides structured error responses for all known error types,
mapped to appropriate HTTP status codes per Requirements 15.1, 15.2,
4.6, and 14.5.
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom application exception hierarchy
# ---------------------------------------------------------------------------

class AppBaseException(Exception):
    """Base class for all application-level exceptions."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppBaseException):
    """Raised when a requested resource cannot be found in the database."""

    error_code: str = "NOT_FOUND"


class DatabaseError(AppBaseException):
    """Raised when a database operation fails unexpectedly."""

    error_code: str = "DATABASE_ERROR"


class ModelInferenceError(AppBaseException):
    """Raised when the ML model fails to produce a prediction."""

    error_code: str = "MODEL_INFERENCE_ERROR"


class SHAPComputationError(AppBaseException):
    """Raised when SHAP value computation fails or times out."""

    error_code: str = "SHAP_COMPUTATION_ERROR"


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """Build a consistent structured error JSON response."""
    body: dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


# ---------------------------------------------------------------------------
# Individual exception handlers
# ---------------------------------------------------------------------------

async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic / FastAPI request validation failures.

    Returns HTTP 422 with a list of field-level errors so the client
    knows exactly which fields are invalid (Requirement 15.2).
    """
    field_errors = [
        {
            "field": " -> ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    logger.warning(
        "Request validation failed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": field_errors,
        },
    )
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Request validation failed. Please check the submitted data.",
        details=field_errors,
    )


async def pydantic_validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """
    Handle Pydantic ValidationError raised outside of request parsing
    (e.g., in service layer).

    Returns HTTP 422 (Requirement 15.2).
    """
    field_errors = [
        {
            "field": " -> ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    logger.warning(
        "Pydantic validation error in service layer",
        extra={"path": request.url.path, "errors": field_errors},
    )
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Data validation failed.",
        details=field_errors,
    )


async def not_found_error_handler(
    request: Request, exc: NotFoundError
) -> JSONResponse:
    """
    Handle NotFoundError — resource does not exist in the database.

    Returns HTTP 404 (Requirement 1.6, 18.5).
    """
    logger.info(
        "Resource not found: %s",
        exc.message,
        extra={"path": request.url.path},
    )
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )


async def database_error_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    """
    Handle DatabaseError — unexpected persistence layer failure.

    Returns HTTP 500 and logs the full stack trace for diagnostics
    (Requirements 15.1, 15.4, 15.5).
    """
    logger.error(
        "Database error: %s\n%s",
        exc.message,
        traceback.format_exc(),
        extra={"path": request.url.path},
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=exc.error_code,
        message="A database error occurred. Please try again later.",
        details=exc.details,
    )


async def model_inference_error_handler(
    request: Request, exc: ModelInferenceError
) -> JSONResponse:
    """
    Handle ModelInferenceError — ML model is unavailable or failed.

    Returns HTTP 503 so the client knows the service is temporarily
    unavailable (Requirements 4.6, 15.6).
    """
    logger.error(
        "ML model inference error: %s\n%s",
        exc.message,
        traceback.format_exc(),
        extra={"path": request.url.path},
    )
    return _error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_code=exc.error_code,
        message="The prediction service is temporarily unavailable. Please try again later.",
        details=exc.details,
    )


async def shap_computation_error_handler(
    request: Request, exc: SHAPComputationError
) -> JSONResponse:
    """
    Handle SHAPComputationError with graceful degradation.

    SHAP failures should NOT fail the overall prediction — the response
    still returns HTTP 200 but sets ``shap_explanation`` to
    ``"unavailable"`` (Requirement 14.5).

    NOTE: Callers are expected to catch SHAPComputationError, set
    shap_explanation="unavailable" in the prediction result, and return
    the result normally.  This handler acts as a safety net for cases
    where the exception propagates all the way to the framework.
    """
    logger.warning(
        "SHAP computation failed — returning degraded response: %s",
        exc.message,
        extra={"path": request.url.path},
    )
    # Return 200 so the client knows the prediction itself succeeded;
    # the explainability portion is simply unavailable.
    body: dict[str, Any] = {
        "shap_explanation": "unavailable",
        "warning": {
            "code": exc.error_code,
            "message": exc.message,
        },
    }
    if exc.details:
        body["warning"]["details"] = exc.details
    return JSONResponse(status_code=status.HTTP_200_OK, content=body)


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for any unhandled exception.

    Returns HTTP 500 with a generic message and logs the full stack
    trace (Requirement 15.1).
    """
    logger.error(
        "Unhandled exception: %s\n%s",
        str(exc),
        traceback.format_exc(),
        extra={"path": request.url.path, "method": request.method},
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please contact support if the problem persists.",
    )


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers on the FastAPI application instance.

    Call this once during application setup, after creating the ``FastAPI``
    object and before starting the server.

    Args:
        app: The FastAPI application instance to configure.
    """
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(ModelInferenceError, model_inference_error_handler)
    app.add_exception_handler(SHAPComputationError, shap_computation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

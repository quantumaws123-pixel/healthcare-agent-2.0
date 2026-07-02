"""
FastAPI application entry point for Healthcare Agent 2.0 Backend ML System.

Startup sequence:
  1. Configure structured JSON logging.
  2. Add CORS middleware (from app.api.middleware.cors).
  3. Register exception handlers (from app.api.middleware.error_handler).
  4. Register all API routers (patients, predict, dashboard, model).
  5. On lifespan startup: initialize DB with retry, set inference_engine=None.
  6. On lifespan shutdown: close DB connections cleanly.
"""

from contextlib import asynccontextmanager
from pathlib import Path

# Load .env file FIRST so DATABASE_PASSWORD and all other env vars are available
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI

# Logging — must be configured before any other import that logs
from app.utils.logger import setup_logging

setup_logging()

import logging  # noqa: E402 — imported after setup_logging() on purpose

from app.api.middleware.cors import add_cors_middleware
from app.api.middleware.error_handler import register_exception_handlers
from app.api.routes.patients import router as patients_router
from app.api.routes.predict import router as predict_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.model import router as model_router
from app.api.routes.admin import router as admin_router
from app.auth.router import router as auth_router
from app.api.routes.hospital import router as hospital_router
from app.api.routes.assistant import router as assistant_router
from app.cache.redis_cache import get_cache
from app.database.connection import check_db_health, close_db
from app.database.connection_manager import init_db_with_retry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    # ── Startup ──────────────────────────────────────────────────────
    logger.info("Starting Healthcare Agent 2.0 Backend ML System…")

    # Initialize database with exponential-backoff retry (Requirement 15.5)
    await init_db_with_retry()

    # Instantiate InferenceEngine and load the active model and preprocessor (Requirement 4.1)
    from app.database.connection import get_db_context
    from app.ml.model_registry import ModelRegistry
    from app.ml.feature_preprocessor import FeaturePreprocessor
    from app.ml.inference_engine import InferenceEngine

    try:
        async with get_db_context() as session:
            registry = ModelRegistry(session)
            active_models = await registry.list_models(active_only=True, limit=1)
            if active_models:
                active_model = active_models[0]
                version = active_model.model_version
                preprocessor_path = Path(registry.model_dir) / f"preprocessor_{version}.joblib"
                if preprocessor_path.exists():
                    preprocessor = FeaturePreprocessor.load(preprocessor_path)
                    logger.info("Loaded preprocessor from %s", preprocessor_path)
                else:
                    preprocessor = FeaturePreprocessor()
                    logger.warning("Preprocessor not found at %s; using default", preprocessor_path)
                
                engine = InferenceEngine(registry, preprocessor)
                await engine.load_model(version)
                app.state.inference_engine = engine
                logger.info("InferenceEngine successfully loaded model version %s", version)
            else:
                app.state.inference_engine = None
                logger.warning("No active model found in registry; using rule-based fallback")
    except Exception as exc:
        app.state.inference_engine = None
        logger.error("Failed to initialize InferenceEngine: %s; using rule-based fallback", exc, exc_info=True)

    logger.info("Application startup complete")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Shutting down Healthcare Agent 2.0 Backend ML System…")
    await close_db()
    logger.info("Application shutdown complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Healthcare Agent 2.0 Backend ML System",
    description=(
        "AI-powered digital twin platform for post-discharge patient monitoring "
        "and hospital readmission risk prediction"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — reads CORS_ORIGINS env var; falls back to localhost dev servers
add_cors_middleware(app)

# Structured exception handlers (HTTP 4xx/5xx)
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(hospital_router)
app.include_router(assistant_router)
app.include_router(patients_router)
app.include_router(predict_router)
app.include_router(dashboard_router)
app.include_router(model_router)


# ---------------------------------------------------------------------------
# Root / health-check endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"])
async def root():
    """Root endpoint — quick liveness check."""
    return {
        "message": "Healthcare Agent 2.0 Backend ML System",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for load-balancer / uptime monitoring."""
    return {
        "status": "healthy",
        "service": "backend-ml-system",
    }


@app.get("/health/detailed", tags=["health"])
async def health_check_detailed():
    """Detailed health check returning DB, inference engine, cache, and version info."""
    # Database connectivity
    db_health = await check_db_health()

    # Inference engine loaded status
    engine_loaded: bool = app.state.inference_engine is not None
    model_version: str | None = None
    if engine_loaded:
        try:
            model_version = getattr(app.state.inference_engine, "model_version", None)
        except Exception:
            model_version = None

    # Cache backend type
    cache = get_cache()
    cache_backend = cache.backend_type  # "redis", "in-memory", or "uninitialized"

    overall_status = "healthy" if db_health.get("status") == "healthy" else "degraded"

    return {
        "status": overall_status,
        "database": db_health,
        "inference_engine": {
            "loaded": engine_loaded,
            "model_version": model_version,
        },
        "cache": {
            "backend": cache_backend,
        },
        "version": app.version,
    }


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

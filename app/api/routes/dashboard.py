"""Dashboard API route handler for Healthcare Agent 2.0 Backend ML System.

Implements:
  - GET /dashboard/stats  — aggregated statistics with 5-minute in-memory caching.

**Validates: Requirements 1.4, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8**
"""

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.models.schemas import DashboardStats
from app.repositories.statistics_repository import StatisticsRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])

# ---------------------------------------------------------------------------
# 5-minute in-memory cache
# ---------------------------------------------------------------------------

#: Cache TTL in seconds (Requirement 12.7)
_CACHE_TTL_SECONDS: float = 300.0

#: Simple dict-based cache: {"data": {...}, "timestamp": float}
_stats_cache: Dict[str, Any] = {}


def _get_cached_stats() -> Dict[str, Any] | None:
    """Return cached stats if still within TTL, otherwise None."""
    if not _stats_cache:
        return None
    age = time.monotonic() - _stats_cache.get("timestamp", 0.0)
    if age < _CACHE_TTL_SECONDS:
        logger.debug("Returning cached dashboard stats (age=%.1fs).", age)
        return _stats_cache["data"]
    logger.debug("Cache expired (age=%.1fs); will recompute stats.", age)
    return None


def _set_cached_stats(data: Dict[str, Any]) -> None:
    """Store stats in the cache with the current timestamp."""
    _stats_cache["data"] = data
    _stats_cache["timestamp"] = time.monotonic()
    logger.debug("Dashboard stats cached.")


# ---------------------------------------------------------------------------
# GET /dashboard/stats
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard/stats",
    response_model=DashboardStats,
    summary="Get aggregated dashboard statistics",
    description=(
        "Returns aggregated KPI statistics for the dashboard including total "
        "patient count, high-risk count, average compliance, average readmission "
        "probability, and risk/recovery distributions. "
        "Results are cached for 5 minutes to reduce database load."
    ),
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db_session),
) -> DashboardStats:
    """
    GET /dashboard/stats

    Computes and returns all dashboard statistics. A 5-minute in-memory cache
    is checked first; if a fresh result is available it is returned immediately
    without hitting the database.

    **Validates: Requirements 1.4, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8**
    """
    # ------------------------------------------------------------------
    # Check cache first (Requirement 12.7)
    # ------------------------------------------------------------------
    cached = _get_cached_stats()
    if cached is not None:
        return DashboardStats(**cached)

    # ------------------------------------------------------------------
    # Fetch fresh aggregations from the database
    # ------------------------------------------------------------------
    repo = StatisticsRepository(db)

    try:
        stats = await repo.compute_dashboard_stats()
    except Exception as exc:
        logger.error("Failed to compute dashboard statistics: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard statistics",
        ) from exc

    # ------------------------------------------------------------------
    # Persist to cache and return
    # ------------------------------------------------------------------
    _set_cached_stats(stats)

    logger.info(
        "Dashboard stats computed: total_patients=%d, high_risk_count=%d, "
        "avg_compliance=%.2f, avg_readmission_probability=%.4f",
        stats["total_patients"],
        stats["high_risk_count"],
        stats["avg_compliance"],
        stats["avg_readmission_probability"],
    )

    return DashboardStats(**stats)

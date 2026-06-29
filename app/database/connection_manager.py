"""Database connection resilience layer for Healthcare Agent 2.0.

Provides exponential-backoff retry logic on top of the base connection module,
connection pool health checks, and structured failure/retry logging.

Retry schedule (seconds): 1 → 2 → 4 → 8 → 16 (max)
After all retries are exhausted the last exception is re-raised so callers
can handle it or let the application fail to start with a clear message.

**Validates: Requirements 15.5**
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional, TypeVar

from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.database.connection import (
    check_db_health,
    close_db,
    init_db,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------------------------

# Exponential backoff delays in seconds: 1, 2, 4, 8, 16
_BACKOFF_DELAYS: tuple[int, ...] = (1, 2, 4, 8, 16)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Core retry helper
# ---------------------------------------------------------------------------


async def _retry_with_backoff(
    operation: Callable[[], Coroutine[Any, Any, T]],
    *,
    operation_name: str,
    delays: tuple[int, ...] = _BACKOFF_DELAYS,
) -> T:
    """Execute *operation* with exponential backoff on failure.

    Args:
        operation: An async callable that takes no arguments and returns T.
        operation_name: Human-readable name used in log messages.
        delays: Sequence of sleep durations (seconds) between attempts.
                The total number of attempts is ``len(delays) + 1``.

    Returns:
        The return value of *operation* on first success.

    Raises:
        The last exception raised by *operation* once all retries are
        exhausted.
    """
    last_exc: Optional[Exception] = None
    total_attempts = len(delays) + 1

    for attempt, delay in enumerate(
        [None, *delays], start=1
    ):  # attempt 1 has no preceding delay
        if delay is not None:
            logger.warning(
                "Retrying %s (attempt %d/%d) after %ds backoff",
                operation_name,
                attempt,
                total_attempts,
                delay,
            )
            await asyncio.sleep(delay)

        try:
            logger.debug(
                "Attempting %s (attempt %d/%d)",
                operation_name,
                attempt,
                total_attempts,
            )
            result: T = await operation()
            if attempt > 1:
                logger.info(
                    "%s succeeded on attempt %d/%d",
                    operation_name,
                    attempt,
                    total_attempts,
                )
            return result

        except (OperationalError, SQLAlchemyError, OSError, ConnectionRefusedError) as exc:
            last_exc = exc
            logger.error(
                "%s failed (attempt %d/%d): %s",
                operation_name,
                attempt,
                total_attempts,
                exc,
                exc_info=False,  # Keep noise low; full trace on final failure
            )

    # All retries exhausted
    logger.critical(
        "%s failed after %d attempt(s). Last error: %s",
        operation_name,
        total_attempts,
        last_exc,
        exc_info=True,
    )
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def init_db_with_retry(
    delays: tuple[int, ...] = _BACKOFF_DELAYS,
) -> None:
    """Initialise the database connection with exponential backoff retry.

    Wraps :func:`app.database.connection.init_db` with retry logic so that
    transient connection failures during application startup are handled
    gracefully.

    Args:
        delays: Sequence of back-off delays (seconds).  Defaults to the
                module-level schedule ``(1, 2, 4, 8, 16)``.

    Raises:
        SQLAlchemyError / OSError: If the database cannot be reached after all
        retries are exhausted.

    **Validates: Requirement 15.5**
    """
    logger.info(
        "Initialising database connection (max %d attempt(s), backoff: %s s)",
        len(delays) + 1,
        delays,
    )
    await _retry_with_backoff(
        init_db,
        operation_name="database initialisation",
        delays=delays,
    )
    logger.info("Database connection initialised successfully")


async def check_pool_health() -> dict[str, Any]:
    """Perform a health check on the database connection pool.

    Delegates to :func:`app.database.connection.check_db_health` and
    enriches the result with retry metadata.

    Returns:
        Health status dictionary::

            {
                "status": "healthy" | "unhealthy",
                "message": str,
                "pool_size": int,
                "pool_checked_out": int,
            }

    **Validates: Requirement 15.5**
    """
    logger.debug("Running connection pool health check")
    result = await check_db_health()

    if result.get("status") == "healthy":
        logger.debug(
            "Connection pool healthy — size=%s, checked_out=%s",
            result.get("pool_size"),
            result.get("pool_checked_out"),
        )
    else:
        logger.warning(
            "Connection pool health check FAILED: %s",
            result.get("message"),
        )

    return result


async def reconnect_with_retry(
    delays: tuple[int, ...] = _BACKOFF_DELAYS,
) -> None:
    """Close the current database connection and reconnect with retry logic.

    Useful when a connection error is detected at runtime (e.g., during a
    health check cycle) and the application wants to self-heal without a
    full restart.

    Args:
        delays: Backoff schedule in seconds.

    Raises:
        SQLAlchemyError / OSError: Propagated if reconnection ultimately fails.

    **Validates: Requirement 15.5**
    """
    logger.info("Attempting database reconnect with exponential backoff")

    async def _reconnect() -> None:
        await close_db()
        await init_db()

    await _retry_with_backoff(
        _reconnect,
        operation_name="database reconnect",
        delays=delays,
    )
    logger.info("Database reconnect succeeded")

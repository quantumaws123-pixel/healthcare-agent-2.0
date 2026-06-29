"""
Cache backend for the Healthcare Agent 2.0 Backend API.

Tries to connect to Redis if the ``redis`` package is installed and the
``REDIS_URL`` environment variable is set.  Falls back transparently to an
in-process dictionary when Redis is unavailable so the application can run
in environments without a Redis instance (e.g. local dev, CI, Render free tier).

Usage::

    from app.cache.redis_cache import get_cache

    cache = get_cache()
    await cache.set("dashboard:stats", payload, ttl=300)
    data = await cache.get("dashboard:stats")
    await cache.delete("dashboard:stats")

**Validates: Requirements 12.7, 20.4**
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory fallback store
# ---------------------------------------------------------------------------


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float  # UNIX timestamp; 0.0 means no expiry


class _InMemoryStore:
    """Simple thread-safe(ish) in-process dict cache with TTL support."""

    def __init__(self) -> None:
        self._store: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expires_at and time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """Store *value* under *key*.  *ttl* is in seconds (0 = no expiry)."""
        async with self._lock:
            expires_at = (time.monotonic() + ttl) if ttl > 0 else 0.0
            self._store[key] = _CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def flush(self) -> None:
        """Remove all entries (useful in tests)."""
        async with self._lock:
            self._store.clear()

    def _evict_expired(self) -> None:
        """Synchronously remove expired entries (maintenance helper)."""
        now = time.monotonic()
        expired_keys = [
            k for k, e in self._store.items() if e.expires_at and now > e.expires_at
        ]
        for k in expired_keys:
            del self._store[k]


# ---------------------------------------------------------------------------
# Redis-backed store (optional)
# ---------------------------------------------------------------------------


class _RedisStore:
    """Async Redis-backed cache using the ``redis`` package."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, key: str) -> Any | None:
        import pickle  # noqa: PLC0415 — lazy import

        raw = await self._client.get(key)
        if raw is None:
            return None
        try:
            return pickle.loads(raw)  # noqa: S301 — trusted internal data
        except Exception as exc:
            logger.warning("Failed to deserialize cache entry '%s': %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: int = 0) -> None:
        import pickle  # noqa: PLC0415

        raw = pickle.dumps(value)
        if ttl > 0:
            await self._client.setex(key, ttl, raw)
        else:
            await self._client.set(key, raw)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def flush(self) -> None:
        await self._client.flushdb()


# ---------------------------------------------------------------------------
# Public CacheBackend façade
# ---------------------------------------------------------------------------


class CacheBackend:
    """
    Unified cache façade that delegates to either a Redis or in-memory backend.

    Automatically selects Redis when:
      1. The ``redis`` package is importable.
      2. The ``REDIS_URL`` environment variable is set.

    Otherwise falls back to an in-process dictionary store.

    Args:
        redis_url: Optional Redis connection URL.  Defaults to the
                   ``REDIS_URL`` environment variable.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._backend: _InMemoryStore | _RedisStore | None = None
        self._redis_url = redis_url or os.getenv("REDIS_URL", "")
        self._initialized = False

    async def initialize(self) -> None:
        """Connect to Redis or fall back to in-memory store."""
        if self._initialized:
            return

        if self._redis_url:
            try:
                import redis.asyncio as aioredis  # noqa: PLC0415

                client = aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    socket_connect_timeout=2,
                )
                # Ping to verify connectivity
                await client.ping()
                self._backend = _RedisStore(client)
                logger.info("Cache backend: Redis (%s)", self._redis_url)
            except ImportError:
                logger.warning(
                    "redis package not installed — falling back to in-memory cache"
                )
                self._backend = _InMemoryStore()
            except Exception as exc:
                logger.warning(
                    "Redis connection failed (%s) — falling back to in-memory cache", exc
                )
                self._backend = _InMemoryStore()
        else:
            logger.info("REDIS_URL not set — using in-memory cache backend")
            self._backend = _InMemoryStore()

        self._initialized = True

    def _require_initialized(self) -> None:
        if not self._initialized or self._backend is None:
            raise RuntimeError(
                "CacheBackend not initialized. Call await cache.initialize() first."
            )

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value by *key*.

        Returns:
            The cached value, or ``None`` if the key does not exist or
            has expired.
        """
        self._require_initialized()
        try:
            return await self._backend.get(key)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Cache GET error for key '%s': %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """
        Store *value* under *key* with an optional TTL.

        Args:
            key:   Cache key string.
            value: Python object to cache (must be picklable for Redis).
            ttl:   Time-to-live in seconds.  ``0`` means no expiry.
        """
        self._require_initialized()
        try:
            await self._backend.set(key, value, ttl=ttl)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Cache SET error for key '%s': %s", key, exc)

    async def delete(self, key: str) -> None:
        """
        Remove *key* from the cache.

        No-op if the key does not exist.
        """
        self._require_initialized()
        try:
            await self._backend.delete(key)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Cache DELETE error for key '%s': %s", key, exc)

    async def flush(self) -> None:
        """Clear all cache entries (primarily for testing)."""
        self._require_initialized()
        try:
            await self._backend.flush()  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Cache FLUSH error: %s", exc)

    @property
    def backend_type(self) -> str:
        """Return a human-readable name for the active backend."""
        if not self._initialized or self._backend is None:
            return "uninitialized"
        return "redis" if isinstance(self._backend, _RedisStore) else "in-memory"


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_cache_instance: CacheBackend | None = None


def get_cache() -> CacheBackend:
    """
    Return the module-level :class:`CacheBackend` singleton.

    You must call ``await get_cache().initialize()`` once at application
    startup (e.g. inside the FastAPI lifespan) before using the cache.
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheBackend()
    return _cache_instance

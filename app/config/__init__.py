"""Configuration module for Healthcare Agent 2.0.

Exposes load_config() and AppConfig as the public interface so the rest of
the application can import configuration without knowing the internal layout.

Usage::

    from app.config import load_config, AppConfig

    config = load_config()
    db_url = config.database.async_url
"""

from app.config.settings import (
    AppConfig,
    DatabaseConfig,
    APIConfig,
    MLConfig,
    CacheConfig,
    LoggingConfig,
    load_config,
)

__all__ = [
    "AppConfig",
    "DatabaseConfig",
    "APIConfig",
    "MLConfig",
    "CacheConfig",
    "LoggingConfig",
    "load_config",
]

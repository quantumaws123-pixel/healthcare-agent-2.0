"""Configuration management for Healthcare Agent 2.0 Backend ML System.

Loads all system configuration from environment variables using Pydantic Settings.
Validates required parameters at startup and rejects invalid configurations.

**Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8**
"""

import logging
from typing import List, Literal, Optional
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseSettings):
    """Database connection parameters.

    **Validates: Requirements 19.2**
    """

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    name: str = Field(default="healthcare_agent", description="Database name")
    user: str = Field(default="postgres", description="Database username")
    password: str = Field(..., description="Database password (required)")
    pool_size: int = Field(default=20, ge=1, le=200, description="Connection pool size")
    max_overflow: int = Field(
        default=10, ge=0, le=200, description="Max overflow connections"
    )

    @property
    def async_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @property
    def sync_url(self) -> str:
        """Construct sync PostgreSQL connection URL (for Alembic)."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class APIConfig(BaseSettings):
    """API server parameters and CORS configuration.

    **Validates: Requirements 19.3**
    """

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="0.0.0.0", description="API server bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="API server port")
    reload: bool = Field(default=False, description="Enable auto-reload for development")

    # CORS origins stored separately since they have a different prefix
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins (comma-separated in env as CORS_ORIGINS)",
    )

    # Pagination defaults
    default_page_size: int = Field(
        default=10, ge=1, le=100, description="Default pagination page size"
    )
    max_page_size: int = Field(
        default=100, ge=1, le=1000, description="Maximum allowed page size"
    )

    # Rate limiting
    rate_limit: int = Field(
        default=1000, ge=1, description="Max requests per hour per client"
    )

    # Request size limit (bytes)
    max_request_size: int = Field(
        default=1_048_576, ge=1024, description="Max request payload size in bytes (1 MB)"
    )

    @model_validator(mode="after")
    def validate_page_sizes(self) -> "APIConfig":
        if self.default_page_size > self.max_page_size:
            raise ValueError(
                f"default_page_size ({self.default_page_size}) must not exceed "
                f"max_page_size ({self.max_page_size})"
            )
        return self


class MLConfig(BaseSettings):
    """ML model paths, versioning, and inference parameters.

    **Validates: Requirements 19.4**
    """

    model_config = SettingsConfigDict(
        env_prefix="MODEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    version: str = Field(default="latest", description="Model version to load")
    path: str = Field(default="./models", description="Directory where models are stored")
    type: str = Field(default="XGBoost", description="Model architecture type")

    # SHAP configuration (separate prefix handled via AppConfig)
    shap_background_samples: int = Field(
        default=100, ge=10, le=10000, description="Background samples for SHAP kernel"
    )
    shap_timeout_seconds: float = Field(
        default=1.0, gt=0, description="SHAP computation timeout in seconds"
    )

    # Inference timeout
    prediction_timeout_ms: int = Field(
        default=500, ge=100, description="Prediction timeout in milliseconds"
    )

    # Feature engineering window
    feature_window_days: int = Field(
        default=30, ge=1, description="Days of history used for feature engineering"
    )
    trend_analysis_days: int = Field(
        default=7, ge=1, description="Days of history used for trend analysis"
    )


class CacheConfig(BaseSettings):
    """Cache layer configuration (Redis + in-memory fallback).

    **Validates: Requirements 12.7**
    """

    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ttl_seconds: int = Field(
        default=300, ge=0, description="Cache TTL in seconds (0 = no expiry)"
    )
    enabled: bool = Field(default=True, description="Enable or disable the cache layer")
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (e.g. redis://localhost:6379/0). "
        "Falls back to in-memory cache when None.",
    )


class LoggingConfig(BaseSettings):
    """Logging configuration.

    **Validates: Requirements 19.5**
    """

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log level"
    )
    format: Literal["json", "text"] = Field(
        default="json", description="Log output format"
    )

    @field_validator("level", mode="before")
    @classmethod
    def uppercase_level(cls, v: str) -> str:
        return v.upper()


class AppConfig(BaseSettings):
    """Top-level application configuration.

    Composes all sub-configs and provides a single entry-point for
    accessing application settings.

    **Validates: Requirements 19.1, 19.7, 19.8**
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # CORS origins at top level to capture CORS_ORIGINS env var
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Sub-configurations are built lazily via load_config()
    _db: Optional[DatabaseConfig] = None
    _api: Optional[APIConfig] = None
    _ml: Optional[MLConfig] = None
    _cache: Optional[CacheConfig] = None
    _logging: Optional[LoggingConfig] = None

    @property
    def database(self) -> DatabaseConfig:
        if self._db is None:
            self._db = DatabaseConfig()
        return self._db

    @property
    def api(self) -> APIConfig:
        if self._api is None:
            self._api = APIConfig(cors_origins=self.cors_origins)
        return self._api

    @property
    def ml(self) -> MLConfig:
        if self._ml is None:
            self._ml = MLConfig()
        return self._ml

    @property
    def cache(self) -> CacheConfig:
        if self._cache is None:
            self._cache = CacheConfig()
        return self._cache

    @property
    def logging(self) -> LoggingConfig:
        if self._logging is None:
            self._logging = LoggingConfig()
        return self._logging


@lru_cache(maxsize=1)
def load_config() -> AppConfig:
    """Load and cache application configuration from environment variables.

    Reads all configuration from environment variables (and optional .env file).
    Validates parameters at startup and raises descriptive errors for missing
    required values or invalid configurations.

    Returns:
        Fully validated AppConfig instance.

    Raises:
        pydantic.ValidationError: If required parameters are missing or invalid.

    Example::

        config = load_config()
        db_url = config.database.async_url
        log_level = config.logging.level

    **Validates: Requirements 19.1, 19.7, 19.8**
    """
    try:
        config = AppConfig()
        logger.info(
            "Configuration loaded successfully",
            extra={
                "db_host": config.database.host,
                "db_port": config.database.port,
                "db_name": config.database.name,
                "api_host": config.api.host,
                "api_port": config.api.port,
                "log_level": config.logging.level,
                "cache_enabled": config.cache.enabled,
                "model_version": config.ml.version,
            },
        )
        return config
    except Exception as exc:
        logger.critical(
            "Failed to load configuration — application cannot start. "
            f"Details: {exc}"
        )
        raise

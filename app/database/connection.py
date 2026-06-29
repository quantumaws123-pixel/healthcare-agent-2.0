"""Async database connection management for Healthcare Agent 2.0 Backend ML System.

This module provides:
- Async SQLAlchemy engine with connection pooling
- Session factory with dependency injection for FastAPI
- Database health check functionality

**Validates: Requirements 2.8, 19.2, 20.5**
"""

import os
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import Base

# Configure logger
logger = logging.getLogger(__name__)


# Global engine and session factory
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """
    Construct database URL from environment variables.
    
    Returns:
        PostgreSQL async connection string
        
    Raises:
        ValueError: If required environment variables are missing
        
    **Validates: Requirement 19.2**
    """
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME", "healthcare_agent")
    user = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD")
    
    if not password:
        raise ValueError(
            "DATABASE_PASSWORD environment variable is required but not set"
        )
    
    # Use asyncpg driver for async PostgreSQL connections
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    
    logger.info(
        f"Database URL configured: postgresql+asyncpg://{user}:****@{host}:{port}/{name}"
    )
    
    return database_url


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.
    
    Configuration from environment variables:
    - DATABASE_POOL_SIZE: Number of connections to maintain in the pool (default: 20)
    - DATABASE_MAX_OVERFLOW: Max connections beyond pool_size (default: 10)
    
    Returns:
        Configured AsyncEngine instance
        
    **Validates: Requirements 2.8, 20.5**
    """
    database_url = get_database_url()
    
    # Get pool configuration from environment
    pool_size = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    
    # Create async engine with connection pooling
    # Note: async engines use AsyncAdaptedQueuePool automatically — do NOT pass poolclass=QueuePool
    engine = create_async_engine(
        database_url,
        echo=os.getenv("LOG_LEVEL", "INFO") == "DEBUG",  # Log SQL queries in DEBUG mode
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "server_settings": {
                "application_name": "healthcare_agent_backend"
            }
        }
    )
    
    logger.info(
        f"Async database engine created with pool_size={pool_size}, "
        f"max_overflow={max_overflow}"
    )
    
    return engine


def get_engine() -> AsyncEngine:
    """
    Get or create the global database engine.
    
    Returns:
        Global AsyncEngine instance
        
    Raises:
        RuntimeError: If engine has not been initialized
    """
    global _engine
    
    if _engine is None:
        raise RuntimeError(
            "Database engine not initialized. Call init_db() first."
        )
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the global async session factory.
    
    Returns:
        Configured async_sessionmaker instance
        
    Raises:
        RuntimeError: If session factory has not been initialized
    """
    global _async_session_factory
    
    if _async_session_factory is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_db() first."
        )
    
    return _async_session_factory


async def init_db() -> None:
    """
    Initialize database engine and session factory.
    
    This should be called once at application startup.
    Creates all tables if they don't exist.
    
    **Validates: Requirements 2.8, 19.2**
    """
    global _engine, _async_session_factory
    
    try:
        # Create engine
        _engine = create_engine()
        
        # Create session factory with async engine
        _async_session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual control over flushing
            autocommit=False,  # Explicit transaction management
        )
        
        # Create all tables (idempotent operation)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


async def close_db() -> None:
    """
    Close database engine and clean up connections.
    
    This should be called once at application shutdown.
    """
    global _engine, _async_session_factory
    
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database engine disposed")
    
    _engine = None
    _async_session_factory = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for FastAPI endpoints.
    
    Provides an async database session with automatic cleanup.
    Use with FastAPI's Depends() for automatic session management.
    
    Example:
        ```python
        @app.get("/patients")
        async def get_patients(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(PatientRecordDB))
            return result.scalars().all()
        ```
    
    Yields:
        AsyncSession instance
        
    **Validates: Requirement 2.8**
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside FastAPI dependencies.
    
    Use this when you need a database session in background tasks,
    CLI scripts, or other non-endpoint contexts.
    
    Example:
        ```python
        async with get_db_context() as db:
            result = await db.execute(select(PatientRecordDB))
            patients = result.scalars().all()
        ```
    
    Yields:
        AsyncSession instance with automatic commit/rollback
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database context error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def check_db_health() -> dict[str, str | int]:
    """
    Check database connectivity and return health status.
    
    Performs a simple query to verify:
    1. Database is reachable
    2. Credentials are valid
    3. Connection pool is functioning
    
    Returns:
        Dictionary with health status information:
        - status: "healthy" or "unhealthy"
        - message: Human-readable status message
        - pool_size: Current connection pool size
        - pool_checked_out: Number of connections currently in use
        
    Example response:
        {
            "status": "healthy",
            "message": "Database connection successful",
            "pool_size": 20,
            "pool_checked_out": 2
        }
    
    **Validates: Requirement 2.8**
    """
    try:
        engine = get_engine()
        
        # Test database connection with a simple query
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as health_check"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                # Get pool statistics
                pool = engine.pool
                pool_size = pool.size() if hasattr(pool, 'size') else 0
                checked_out = pool.checkedout() if hasattr(pool, 'checkedout') else 0
                
                logger.info("Database health check passed")
                
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "pool_size": pool_size,
                    "pool_checked_out": checked_out,
                }
            else:
                logger.warning("Database health check query returned unexpected result")
                return {
                    "status": "unhealthy",
                    "message": "Database query returned unexpected result",
                    "pool_size": 0,
                    "pool_checked_out": 0,
                }
                
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "pool_size": 0,
            "pool_checked_out": 0,
        }
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Unexpected error: {str(e)}",
            "pool_size": 0,
            "pool_checked_out": 0,
        }


async def get_db_stats() -> dict[str, int | float]:
    """
    Get detailed database connection pool statistics.
    
    Returns:
        Dictionary with pool statistics:
        - pool_size: Configured pool size
        - pool_checked_out: Connections currently in use
        - pool_overflow: Connections created beyond pool_size
        - pool_checked_in: Available connections in pool
        
    Useful for monitoring and debugging connection pool behavior.
    """
    try:
        engine = get_engine()
        pool = engine.pool
        
        stats = {
            "pool_size": pool.size() if hasattr(pool, 'size') else 0,
            "pool_checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 0,
            "pool_overflow": pool.overflow() if hasattr(pool, 'overflow') else 0,
            "pool_checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else 0,
        }
        
        logger.debug(f"Database pool stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}", exc_info=True)
        return {
            "pool_size": 0,
            "pool_checked_out": 0,
            "pool_overflow": 0,
            "pool_checked_in": 0,
        }

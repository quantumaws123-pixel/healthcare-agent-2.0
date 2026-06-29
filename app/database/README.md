# Database Connection Module

This module provides async database connection management for the Healthcare Agent 2.0 Backend ML System.

## Features

- **Async SQLAlchemy Engine**: Configured with connection pooling (pool_size=20, max_overflow=10)
- **Session Factory**: For dependency injection in FastAPI endpoints
- **Health Check**: Database connectivity verification
- **Environment Configuration**: All settings loaded from environment variables

## Requirements Validation

- **Requirement 2.8**: Async database connection with connection pooling
- **Requirement 19.2**: Configuration management via environment variables
- **Requirement 20.5**: Connection pooling for performance and scalability

## Usage

### 1. Application Startup

Initialize the database connection at application startup:

```python
from app.database import init_db, close_db

# In your FastAPI app
@app.on_event("startup")
async def startup():
    await init_db()
    print("Database initialized")

@app.on_event("shutdown")
async def shutdown():
    await close_db()
    print("Database connection closed")
```

### 2. FastAPI Dependency Injection

Use `get_db_session` for automatic session management in endpoints:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session, PatientRecordDB

@app.get("/patients")
async def get_patients(db: AsyncSession = Depends(get_db_session)):
    from sqlalchemy import select
    
    result = await db.execute(select(PatientRecordDB))
    patients = result.scalars().all()
    return patients
```

### 3. Context Manager (for background tasks)

Use `get_db_context` when working outside FastAPI dependencies:

```python
from app.database import get_db_context, PatientRecordDB
from sqlalchemy import select

async def background_task():
    async with get_db_context() as db:
        result = await db.execute(select(PatientRecordDB))
        patients = result.scalars().all()
        # Process patients...
    # Automatic commit/rollback on exit
```

### 4. Health Check

Check database connectivity:

```python
from app.database import check_db_health

@app.get("/health/database")
async def database_health():
    return await check_db_health()
```

Example response:
```json
{
    "status": "healthy",
    "message": "Database connection successful",
    "pool_size": 20,
    "pool_checked_out": 2
}
```

### 5. Pool Statistics

Get detailed connection pool statistics:

```python
from app.database import get_db_stats

@app.get("/database/stats")
async def database_stats():
    return await get_db_stats()
```

Example response:
```json
{
    "pool_size": 20,
    "pool_checked_out": 5,
    "pool_overflow": 2,
    "pool_checked_in": 15
}
```

## Environment Variables

Configure database connection via environment variables (see `.env.example`):

```bash
# Database Configuration
DATABASE_HOST=localhost          # Default: localhost
DATABASE_PORT=5432              # Default: 5432
DATABASE_NAME=healthcare_agent  # Default: healthcare_agent
DATABASE_USER=postgres          # Default: postgres
DATABASE_PASSWORD=your_password # Required, no default
DATABASE_POOL_SIZE=20          # Default: 20
DATABASE_MAX_OVERFLOW=10       # Default: 10
```

## Connection Pooling

The module uses SQLAlchemy's `QueuePool` with the following configuration:

- **pool_size**: Number of permanent connections (default: 20)
- **max_overflow**: Additional connections when pool is exhausted (default: 10)
- **pool_pre_ping**: Verifies connections before use (enabled)
- **pool_recycle**: Recycles connections after 1 hour (3600 seconds)

This configuration supports:
- Up to 30 concurrent connections (20 + 10 overflow)
- Automatic connection health verification
- Connection recycling for long-running processes

## Error Handling

The module includes comprehensive error handling:

1. **Missing Configuration**: Raises `ValueError` if required environment variables are missing
2. **Connection Failures**: Logs errors and returns unhealthy status in health checks
3. **Session Errors**: Automatic rollback on exceptions within session contexts
4. **Pool Exhaustion**: SQLAlchemy will queue requests when pool is full

## Logging

All database operations are logged for debugging and monitoring:

```python
import logging

logger = logging.getLogger("app.database.connection")
logger.setLevel(logging.INFO)
```

Set `LOG_LEVEL=DEBUG` environment variable to log all SQL queries.

## Testing

Unit tests are provided in `test_connection.py`. Run with:

```bash
pytest app/database/test_connection.py -v
```

Note: asyncpg package must be installed for actual database connections.

## Architecture Integration

This module integrates with the overall system architecture:

```
FastAPI Endpoints
    ↓ (Depends)
get_db_session() → AsyncSession
    ↓
Connection Pool (20 + 10 overflow)
    ↓
PostgreSQL Database
```

## Performance Considerations

- **Async I/O**: Non-blocking database operations for better concurrency
- **Connection Pooling**: Reuses connections to reduce overhead
- **Pool Pre-ping**: Prevents errors from stale connections
- **Connection Recycling**: Handles long-running processes gracefully

## Future Enhancements

Potential improvements for future iterations:

1. **Read Replicas**: Support read-only connections to replicas
2. **Connection Retry Logic**: Exponential backoff for connection failures
3. **Metrics Collection**: Prometheus metrics for pool statistics
4. **Connection Timeouts**: Configurable query and connection timeouts
5. **Database Migrations**: Integration with Alembic for schema management

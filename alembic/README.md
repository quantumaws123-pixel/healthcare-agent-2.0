# Alembic Database Migrations

This directory contains database migration scripts for the Healthcare Agent 2.0 Backend ML System using Alembic.

## Overview

Alembic provides version control for database schemas, allowing you to:
- Track schema changes over time
- Apply migrations to upgrade the database
- Rollback migrations to downgrade the database
- Generate migrations automatically from model changes

## Prerequisites

1. PostgreSQL 15+ installed and running
2. Database created (default: `healthcare_agent`)
3. Environment variables configured in `.env` file:
   - `DATABASE_HOST`
   - `DATABASE_PORT`
   - `DATABASE_NAME`
   - `DATABASE_USER`
   - `DATABASE_PASSWORD`

## Initial Setup

The Alembic migration system has already been initialized. The initial migration includes:
- `patient_records` table with composite primary key (patient_id, day)
- `ml_models` table for ML model versioning
- All required indexes for query optimization

## Common Commands

### Apply All Pending Migrations (Upgrade to Latest)

```bash
alembic upgrade head
```

This will create all tables and indexes if they don't exist.

### Check Current Migration Version

```bash
alembic current
```

### View Migration History

```bash
alembic history
```

### Rollback to Previous Migration

```bash
alembic downgrade -1
```

### Rollback All Migrations (Drop All Tables)

```bash
alembic downgrade base
```

### Generate New Migration After Model Changes

```bash
alembic revision --autogenerate -m "Description of changes"
```

**Note:** This requires a running database connection. Review the generated migration before applying it.

### Generate Empty Migration Template

```bash
alembic revision -m "Description of changes"
```

## Migration Structure

```
alembic/
├── env.py                 # Migration environment configuration (async support)
├── script.py.mako         # Template for new migrations
├── README.md              # This file
└── versions/              # Migration scripts (ordered by revision)
    └── b1e039b53fc2_initial_database_schema_with_patient_.py
```

## Initial Migration Details

**Migration ID:** `b1e039b53fc2`

**Created:** 2026-06-29

**Tables Created:**

### patient_records
- Composite primary key: (patient_id, day)
- 42 columns including demographics, vitals, ideal/real twin data, computed scores, and AI predictions
- 5 indexes: patient_id, day, disease_type, risk_level, recovery_status

### ml_models
- Primary key: model_id (auto-increment)
- Unique constraint: model_version
- Tracks model metadata, training info, evaluation metrics, and deployment status

## Validations

This migration validates the following requirements:
- **Requirement 2.1:** Database schema for patient records and ML models
- **Requirement 2.6:** Indexes on patient_id, day, disease_type, risk_level, recovery_status

## Troubleshooting

### Connection Errors

If you get database connection errors:
1. Verify PostgreSQL is running: `pg_isready`
2. Check `.env` file has correct credentials
3. Test connection: `psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME`

### Migration Conflicts

If you get "target database is not up to date" errors:
1. Check current version: `alembic current`
2. View pending migrations: `alembic history`
3. Manually resolve conflicts or stamp to specific revision

### Async Driver Issues

This project uses `asyncpg` for async PostgreSQL support. Ensure it's installed:

```bash
pip install asyncpg
```

## Production Deployment

For production deployments:

1. **Always test migrations in a staging environment first**
2. **Backup the database before applying migrations:**
   ```bash
   pg_dump -h $HOST -U $USER -d $DATABASE > backup_$(date +%Y%m%d).sql
   ```
3. **Apply migrations:**
   ```bash
   alembic upgrade head
   ```
4. **Verify migration success:**
   ```bash
   alembic current
   psql -c "SELECT * FROM alembic_version;"
   ```

## CI/CD Integration

To integrate migrations into your CI/CD pipeline:

```bash
# In your deployment script
cd /path/to/project
source .env
alembic upgrade head
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

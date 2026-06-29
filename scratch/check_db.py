import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file FIRST
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

import asyncio
from sqlalchemy import text
from app.database.connection import get_db_context
from app.database.connection_manager import init_db_with_retry

async def main():
    print("Initializing database connection...")
    await init_db_with_retry()
    
    async with get_db_context() as session:
        # Count patient records
        result_patients = await session.execute(text("SELECT COUNT(*) FROM patient_records"))
        patient_count = result_patients.scalar()
        
        # Count unique patients
        result_unique = await session.execute(text("SELECT COUNT(DISTINCT patient_id) FROM patient_records"))
        unique_count = result_unique.scalar()
        
        # Count registered ML models
        result_models = await session.execute(text("SELECT COUNT(*) FROM ml_models"))
        model_count = result_models.scalar()
        
        # Get active model version
        result_active = await session.execute(text("SELECT model_version FROM ml_models WHERE is_active = true"))
        active_version = result_active.scalar()
        
        print("\n=== Supabase Database Status ===")
        print(f"Total Patient Records: {patient_count}")
        print(f"Unique Patients: {unique_count}")
        print(f"Registered ML Models: {model_count}")
        print(f"Active Model Version: {active_version}")
        print("================================")

if __name__ == "__main__":
    asyncio.run(main())

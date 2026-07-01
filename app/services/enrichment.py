import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import PatientRecord
from app.database.models import PatientProfileDB, PatientVitalsDailyDB, PatientRecordDB
from app.services.deviation_engine import DeviationEngine

logger = logging.getLogger(__name__)

async def enrich_patient_record(record: PatientRecord, db: AsyncSession) -> None:
    """
    Enriches a PatientRecord Pydantic object with real weight data, individual deviations,
    personalized AI recommendations, and Explainable AI explanation reasons.
    """
    try:
        # 1. Fetch patient profile
        profile = (await db.execute(
            select(PatientProfileDB).where(PatientProfileDB.user_id == record.patient_id)
        )).scalar_one_or_none()

        # 2. Get baseline expected weight
        expected_weight = float(profile.weight_kg) if profile and profile.weight_kg else 70.0
        
        # 3. Get daily actual weight
        actual_weight = expected_weight
        
        # Look up created_at from database if not set on the model
        created_at = getattr(record, "created_at", None)
        if created_at is None:
            # Query db for this patient record to retrieve created_at timestamp
            db_record = (await db.execute(
                select(PatientRecordDB).where(
                    PatientRecordDB.patient_id == record.patient_id,
                    PatientRecordDB.day == record.day
                )
            )).scalar_one_or_none()
            if db_record:
                created_at = db_record.created_at

        if created_at:
            log_date = str(created_at.date())
            vital = (await db.execute(
                select(PatientVitalsDailyDB).where(
                    PatientVitalsDailyDB.patient_user_id == record.patient_id,
                    PatientVitalsDailyDB.log_date == log_date
                )
            )).scalar_one_or_none()
            if vital and vital.weight_kg:
                actual_weight = float(vital.weight_kg)
                
        record.weight_kg = actual_weight
        record.expected_weight = expected_weight

        # 4. Run Deviation Engine
        devs = DeviationEngine.calculate_deviations(record)
        for key, val in devs.items():
            setattr(record, key, val)

        # 5. Run AI Recommendation Engine & Explainable AI Reasons
        record.ai_recommendations = DeviationEngine.generate_recommendations(record)
        record.shap_reasons = DeviationEngine.generate_shap_reasons(record)
        
    except Exception as e:
        logger.error(f"Failed to enrich record for patient {record.patient_id}: {e}", exc_info=True)

import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import PatientProfileDB, PatientRecordDB

async def ensure_patient_records(user_id: str, email: str, name: str, db: AsyncSession):
    """Verify that a patient has a profile and clinical records in the database.
    
    If missing, automatically creates a PatientProfileDB and 30 days of
    realistic clinical monitoring history (PatientRecordDB) linked using their user_id.
    """
    # 1. Check and create PatientProfileDB
    profile_stmt = select(PatientProfileDB).where(PatientProfileDB.user_id == user_id)
    profile = (await db.execute(profile_stmt)).scalar_one_or_none()
    
    if not profile:
        profile = PatientProfileDB(
            id=str(uuid.uuid4()),
            user_id=user_id,
            patient_id=user_id,
            age=45,
            gender="Male",
        )
        db.add(profile)
        await db.flush()
    
    # 2. Check and create PatientRecordDB (30 days of time-series data)
    record_stmt = select(PatientRecordDB).where(PatientRecordDB.patient_id == user_id).limit(1)
    has_records = (await db.execute(record_stmt)).scalar_one_or_none() is not None
    
    if not has_records:
        # Create 30 days of mock patient records with a realistic recovery trend
        for day in range(1, 31):
            # Calculate a progressing recovery score and decreasing readmission probability
            recovery = min(95.0, 70.0 + (day * 0.8))
            prob = max(0.05, 0.28 - (day * 0.007))
            compliance = min(100.0, 75.0 + (day % 7) * 3)
            
            record = PatientRecordDB(
                patient_id=user_id,
                day=day,
                patient_name=name or email.split("@")[0],
                age=45,
                gender="Male",
                bmi=Decimal("24.50"),
                disease_type="Cardiac",
                heart_rate=76 - (day // 10),  # slightly declining to normal resting heart rate
                systolic_bp=125 - (day // 5), # normalizing BP
                diastolic_bp=82 - (day // 10),
                spo2=Decimal("98.50") if day > 10 else Decimal("97.80"),
                respiratory_rate=16,
                body_temperature=Decimal("36.60"),
                expected_steps=8000,
                expected_sleep_hours=Decimal("8.00"),
                water_intake_goal=2000,
                actual_steps=6800 + (day * 80) % 1500,
                actual_sleep_hours=Decimal("7.20") + Decimal(str(round((day % 3) * 0.3, 2))),
                water_intake=1800 + (day * 20) % 400,
                medication_taken="Yes" if day % 15 != 0 else "No",
                exercise_completed="Yes" if day % 3 != 0 else "No",
                diet_compliance=Decimal("85.00") + Decimal(str(day % 5)),
                compliance_score=Decimal(str(round(compliance, 2))),
                ideal_health_score=Decimal("90.00"),
                real_health_score=Decimal(str(round(recovery - 2.0, 2))),
                deviation_score=Decimal("4.50") - Decimal(str(round((day % 5) * 0.2, 2))),
                recovery_score=Decimal(str(round(recovery, 2))),
                readmission_probability=Decimal(str(round(prob, 4))),
                risk_level="Low" if prob < 0.15 else "Medium",
                health_trend="Stable",
                recovery_status="Improving" if day > 10 else "Stable",
                doctor_recommendation="Continue Current Treatment" if prob < 0.15 else "Increase Monitoring",
            )
            db.add(record)
        await db.flush()

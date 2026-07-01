"""Patient setup utility — ensures every patient has seed records on first login.

Two public functions:
- ensure_patient_records()  → called on login; only creates what is missing,
                               never overwrites onboarded data.
- _seed_patient_records()   → called during registration (profile already exists);
                               only seeds PatientRecordDB rows, never touches profile.
"""
import uuid
import logging
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import PatientProfileDB, PatientRecordDB

logger = logging.getLogger(__name__)


async def ensure_patient_records(
    user_id: str, email: str, name: str, db: AsyncSession
) -> None:
    """Called on every patient login.

    Rules:
    - If profile missing → create minimal placeholder (without adding duplicate).
    - If onboarding_completed=True → respect real data, do nothing.
    - If no records exist yet → seed 30 generic days.
    """
    profile = (await db.execute(
        select(PatientProfileDB).where(PatientProfileDB.user_id == user_id)
    )).scalar_one_or_none()

    if not profile:
        try:
            profile = PatientProfileDB(
                id=str(uuid.uuid4()),
                user_id=user_id,
                patient_id=user_id,
                onboarding_completed=False,
            )
            db.add(profile)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            profile = (await db.execute(
                select(PatientProfileDB).where(PatientProfileDB.user_id == user_id)
            )).scalar_one_or_none()
            if not profile:
                logger.error("Failed to create or fetch PatientProfile for user %s", user_id)
                return

    # Onboarding done — real data exists, never touch it.
    if profile.onboarding_completed:
        return

    # Seed records only if none exist yet.
    has_records = (await db.execute(
        select(PatientRecordDB).where(PatientRecordDB.patient_id == user_id).limit(1)
    )).scalar_one_or_none() is not None

    if not has_records:
        await _seed_patient_records(user_id, email, name, db)


async def _seed_patient_records(
    user_id: str, email: str, name: str | None, db: AsyncSession
) -> None:
    """Insert 30 days of generic seed records.

    Called directly from registration so the profile is NOT re-created.
    Also called from ensure_patient_records when records are missing.
    """
    display_name = name or email.split("@")[0]

    for day in range(1, 31):
        recovery   = min(95.0, 70.0 + (day * 0.8))
        prob       = max(0.05, 0.28 - (day * 0.007))
        compliance = min(100.0, 75.0 + (day % 7) * 3)

        record = PatientRecordDB(
            patient_id=user_id,
            day=day,
            patient_name=display_name,
            age=45,
            gender="Male",
            bmi=Decimal("24.50"),
            disease_type="Cardiac",
            heart_rate=76 - (day // 10),
            systolic_bp=125 - (day // 5),
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
            doctor_recommendation=(
                "Continue Current Treatment" if prob < 0.15 else "Increase Monitoring"
            ),
        )
        db.add(record)
    await db.flush()

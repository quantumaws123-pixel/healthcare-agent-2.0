"""Hospital workflow API — hospitals, patient onboarding, care plans,
daily vitals, medical history, and doctor-patient assignment.

All new endpoints. Existing endpoints are untouched.
"""
import uuid, logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from app.database.connection import get_db_session
from app.auth.dependencies import get_current_user, require_role
from app.auth.models import UserDB, UserRole
from app.database.models import (
    HospitalDB, DoctorProfileDB, PatientProfileDB,
    CarePlanDB, PatientVitalsDailyDB, MedicalHistoryDB, PatientRecordDB,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hospital", tags=["hospital"])


# ── shared admin dependency ───────────────────────────────────────────────
async def require_admin(cu: UserDB = Depends(get_current_user)) -> UserDB:
    if str(cu.role) not in ("admin", UserRole.admin.value):
        raise HTTPException(403, "Admin access required")
    return cu


async def require_doctor_or_admin(cu: UserDB = Depends(get_current_user)) -> UserDB:
    r = str(cu.role) if not hasattr(cu.role, "value") else cu.role.value
    if r not in ("admin", "doctor"):
        raise HTTPException(403, "Doctor or Admin access required")
    return cu


# ═══════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class HospitalCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    phone: Optional[str] = None
    email: Optional[str] = None
    departments: Optional[str] = None


class HospitalOut(BaseModel):
    id: str
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    departments: Optional[str] = None
    is_active: bool
    model_config = {"from_attributes": True}


class PatientOnboardingRequest(BaseModel):
    age: int
    gender: Literal["Male", "Female", "Other"]
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None
    disease_type: str
    smoking_status: Optional[Literal["Never", "Former", "Current"]] = None
    alcohol_consumption: Optional[Literal["None", "Moderate", "Heavy", "Occasional"]] = None
    allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    current_medication: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    discharge_date: Optional[str] = None


class PatientProfileOut(BaseModel):
    id: str
    user_id: str
    patient_id: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Literal["Male", "Female", "Other"]] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    blood_group: Optional[str] = None
    disease_type: Optional[str] = None
    smoking_status: Optional[Literal["Never", "Former", "Current"]] = None
    alcohol_consumption: Optional[Literal["None", "Moderate", "Heavy", "Occasional"]] = None
    allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    current_medication: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    discharge_date: Optional[str] = None
    monitoring_start_date: Optional[str] = None
    patient_status: Optional[str] = None
    onboarding_completed: bool = False
    assigned_doctor_id: Optional[str] = None
    model_config = {"from_attributes": True}


class CarePlanCreate(BaseModel):
    patient_user_id: str
    daily_steps_goal: int = 8000
    sleep_hours_goal: float = 8.0
    water_intake_goal_ml: int = 2000
    medication_schedule: Optional[str] = None
    exercise_plan: Optional[str] = None
    diet_plan: Optional[str] = None
    followup_frequency_days: int = 7
    monitoring_duration_days: int = 30
    risk_threshold: float = 0.5
    emergency_threshold: float = 0.75
    notes: Optional[str] = None


class CarePlanOut(BaseModel):
    id: str
    patient_user_id: str
    doctor_user_id: str
    daily_steps_goal: Optional[int] = None
    sleep_hours_goal: Optional[float] = None
    water_intake_goal_ml: Optional[int] = None
    medication_schedule: Optional[str] = None
    exercise_plan: Optional[str] = None
    diet_plan: Optional[str] = None
    followup_frequency_days: Optional[int] = None
    monitoring_duration_days: Optional[int] = None
    risk_threshold: Optional[float] = None
    emergency_threshold: Optional[float] = None
    notes: Optional[str] = None
    is_active: bool = True
    model_config = {"from_attributes": True}


class DailyVitalsRequest(BaseModel):
    log_date: Optional[str] = None   # YYYY-MM-DD; defaults to today
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    spo2: Optional[float] = None
    body_temperature: Optional[float] = None
    weight_kg: Optional[float] = None
    actual_steps: Optional[int] = None
    actual_sleep_hours: Optional[float] = None
    water_intake_ml: Optional[int] = None
    medication_taken: Optional[Literal["Yes", "No"]] = None
    exercise_completed: Optional[Literal["Yes", "No"]] = None
    diet_compliance: Optional[float] = None
    pain_level: Optional[int] = None
    mood: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None


class DailyVitalsOut(BaseModel):
    id: str
    patient_user_id: str
    log_date: str
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    spo2: Optional[float] = None
    body_temperature: Optional[float] = None
    weight_kg: Optional[float] = None
    actual_steps: Optional[int] = None
    actual_sleep_hours: Optional[float] = None
    water_intake_ml: Optional[int] = None
    medication_taken: Optional[Literal["Yes", "No"]] = None
    exercise_completed: Optional[Literal["Yes", "No"]] = None
    diet_compliance: Optional[float] = None
    pain_level: Optional[int] = None
    mood: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    model_config = {"from_attributes": True}


class MedicalHistoryCreate(BaseModel):
    patient_user_id: str
    past_diseases: Optional[str] = None
    previous_admissions: Optional[str] = None
    previous_surgeries: Optional[str] = None
    family_history: Optional[str] = None
    current_medications: Optional[str] = None
    medication_history: Optional[str] = None
    allergies: Optional[str] = None
    lifestyle_smoking: Optional[str] = None
    lifestyle_alcohol: Optional[str] = None
    lifestyle_exercise: Optional[str] = None
    lifestyle_diet: Optional[str] = None
    doctor_notes: Optional[str] = None
    discharge_summary: Optional[str] = None


class MedicalHistoryOut(BaseModel):
    id: str
    patient_user_id: str
    created_by_doctor_id: Optional[str] = None
    past_diseases: Optional[str] = None
    previous_admissions: Optional[str] = None
    previous_surgeries: Optional[str] = None
    family_history: Optional[str] = None
    current_medications: Optional[str] = None
    medication_history: Optional[str] = None
    allergies: Optional[str] = None
    lifestyle_smoking: Optional[str] = None
    lifestyle_alcohol: Optional[str] = None
    lifestyle_exercise: Optional[str] = None
    lifestyle_diet: Optional[str] = None
    doctor_notes: Optional[str] = None
    discharge_summary: Optional[str] = None
    model_config = {"from_attributes": True}


class AssignDoctorRequest(BaseModel):
    patient_user_id: str
    doctor_profile_id: str   # doctor_profiles.id


class DoctorPatientOut(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    disease_type: Optional[str] = None
    patient_status: Optional[str] = None
    onboarding_completed: bool = False
    assigned_doctor_id: Optional[str] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# HOSPITAL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/hospitals", response_model=HospitalOut, status_code=201)
async def create_hospital(
    body: HospitalCreate,
    db: AsyncSession = Depends(get_db_session),
    _admin: UserDB = Depends(require_admin),
):
    """Create a new hospital entity. Admin only."""
    existing = (await db.execute(
        select(HospitalDB).where(HospitalDB.code == body.code)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(400, f"Hospital code '{body.code}' already exists")

    hospital = HospitalDB(id=str(uuid.uuid4()), **body.model_dump())
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)
    logger.info("Created hospital: %s (%s)", hospital.name, hospital.code)
    return hospital


@router.get("/hospitals", response_model=List[HospitalOut])
async def list_hospitals(
    db: AsyncSession = Depends(get_db_session),
    _cu: UserDB = Depends(get_current_user),
):
    """List all active hospitals."""
    result = await db.execute(
        select(HospitalDB).where(HospitalDB.is_active == True).order_by(HospitalDB.name)
    )
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════════════════════
# PATIENT ONBOARDING
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/patient/profile", response_model=PatientProfileOut)
async def get_my_profile(
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Return the current patient's profile (any role can call for their own)."""
    profile = (await db.execute(
        select(PatientProfileDB).where(PatientProfileDB.user_id == cu.id)
    )).scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Patient profile not found")
    return profile


@router.post("/patient/onboarding", response_model=PatientProfileOut)
async def complete_onboarding(
    body: PatientOnboardingRequest,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Patient completes their onboarding form on first login.

    Saves real demographics, computes BMI, marks onboarding_completed=True,
    then regenerates personalised mock patient_records using the real profile.
    """
    profile = (await db.execute(
        select(PatientProfileDB).where(PatientProfileDB.user_id == cu.id)
    )).scalar_one_or_none()

    if not profile:
        profile = PatientProfileDB(id=str(uuid.uuid4()), user_id=cu.id, patient_id=cu.id)
        db.add(profile)

    # Populate fields
    profile.age = body.age
    profile.gender = body.gender
    profile.height_cm = body.height_cm
    profile.weight_kg = Decimal(str(body.weight_kg)) if body.weight_kg else None
    profile.blood_group = body.blood_group
    profile.disease_type = body.disease_type
    profile.smoking_status = body.smoking_status
    profile.alcohol_consumption = body.alcohol_consumption
    profile.allergies = body.allergies
    profile.existing_conditions = body.existing_conditions
    profile.current_medication = body.current_medication
    profile.emergency_contact_name = body.emergency_contact_name
    profile.emergency_contact_phone = body.emergency_contact_phone
    profile.discharge_date = body.discharge_date
    profile.monitoring_start_date = str(date.today())
    profile.patient_status = "Monitoring"
    profile.onboarding_completed = True

    # Compute BMI if height and weight provided
    if body.height_cm and body.weight_kg:
        h_m = body.height_cm / 100
        profile.bmi = Decimal(str(round(body.weight_kg / (h_m * h_m), 2)))

    await db.flush()

    # Regenerate personalised monitoring records
    await _regenerate_patient_records(cu.id, cu.name or cu.email, body, db)

    await db.commit()
    await db.refresh(profile)
    logger.info("Patient %s completed onboarding: disease=%s", cu.email, body.disease_type)
    return profile


# ─── internal helper: regenerate personalised patient records ─────────────

_DISEASE_PROFILES = {
    "Cardiac": {
        "heart_rate_base": 88, "bp_sys": 140, "bp_dia": 90, "spo2": "97.00",
        "risk_base": 0.45, "risk_improvement": 0.012,
    },
    "Diabetes": {
        "heart_rate_base": 82, "bp_sys": 135, "bp_dia": 86, "spo2": "97.50",
        "risk_base": 0.38, "risk_improvement": 0.009,
    },
    "Hypertension": {
        "heart_rate_base": 85, "bp_sys": 155, "bp_dia": 96, "spo2": "98.00",
        "risk_base": 0.35, "risk_improvement": 0.008,
    },
    "COPD": {
        "heart_rate_base": 92, "bp_sys": 130, "bp_dia": 82, "spo2": "95.00",
        "risk_base": 0.52, "risk_improvement": 0.014,
    },
    "Kidney Disease": {
        "heart_rate_base": 84, "bp_sys": 145, "bp_dia": 92, "spo2": "97.20",
        "risk_base": 0.42, "risk_improvement": 0.010,
    },
    "Asthma": {
        "heart_rate_base": 80, "bp_sys": 128, "bp_dia": 80, "spo2": "96.00",
        "risk_base": 0.30, "risk_improvement": 0.007,
    },
    "Stroke Recovery": {
        "heart_rate_base": 78, "bp_sys": 138, "bp_dia": 88, "spo2": "97.80",
        "risk_base": 0.55, "risk_improvement": 0.015,
    },
    "Post Surgery": {
        "heart_rate_base": 90, "bp_sys": 132, "bp_dia": 84, "spo2": "98.20",
        "risk_base": 0.48, "risk_improvement": 0.013,
    },
}

_DEFAULT_PROFILE = {
    "heart_rate_base": 84, "bp_sys": 132, "bp_dia": 84, "spo2": "97.50",
    "risk_base": 0.40, "risk_improvement": 0.010,
}


async def _regenerate_patient_records(
    user_id: str,
    name: str,
    body: PatientOnboardingRequest,
    db: AsyncSession,
):
    """Delete old mock records and generate 30 personalised days."""
    # Delete existing mock records for this patient
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(PatientRecordDB).where(PatientRecordDB.patient_id == user_id)
    )

    dp = _DISEASE_PROFILES.get(body.disease_type, _DEFAULT_PROFILE)

    # Compute BMI if available, else use provided or default
    bmi_val = Decimal("24.50")
    if body.height_cm and body.weight_kg:
        h_m = body.height_cm / 100
        bmi_val = Decimal(str(round(body.weight_kg / (h_m * h_m), 2)))

    smoking = body.smoking_status or "Never"
    alcohol = body.alcohol_consumption or "None"

    for day in range(1, 31):
        recovery = min(95.0, 60.0 + (day * 1.1))
        prob = max(0.05, dp["risk_base"] - (day * dp["risk_improvement"]))
        compliance = min(100.0, 70.0 + (day % 7) * 4)
        hr = dp["heart_rate_base"] - (day // 7)
        sys_bp = dp["bp_sys"] - (day // 4)
        dia_bp = dp["bp_dia"] - (day // 7)

        record = PatientRecordDB(
            patient_id=user_id,
            day=day,
            patient_name=name,
            age=body.age,
            gender=body.gender,
            bmi=bmi_val,
            disease_type=body.disease_type,
            smoking_status=smoking,
            alcohol_consumption=alcohol,
            heart_rate=max(60, hr),
            systolic_bp=max(110, sys_bp),
            diastolic_bp=max(70, dia_bp),
            spo2=Decimal(dp["spo2"]),
            respiratory_rate=16,
            body_temperature=Decimal("36.60"),
            expected_steps=8000,
            expected_sleep_hours=Decimal("8.00"),
            water_intake_goal=2000,
            actual_steps=5500 + (day * 90) % 2000,
            actual_sleep_hours=Decimal("7.00") + Decimal(str(round((day % 3) * 0.25, 2))),
            water_intake=1700 + (day * 25) % 450,
            medication_taken="Yes" if day % 12 != 0 else "No",
            exercise_completed="Yes" if day % 3 != 0 else "No",
            diet_compliance=Decimal("80.00") + Decimal(str(day % 6)),
            compliance_score=Decimal(str(round(compliance, 2))),
            ideal_health_score=Decimal("90.00"),
            real_health_score=Decimal(str(round(recovery - 3.0, 2))),
            deviation_score=Decimal("6.00") - Decimal(str(round((day % 5) * 0.25, 2))),
            recovery_score=Decimal(str(round(recovery, 2))),
            readmission_probability=Decimal(str(round(prob, 4))),
            risk_level="Critical" if prob > 0.65 else ("High" if prob > 0.45 else ("Medium" if prob > 0.25 else "Low")),
            health_trend="Increasing" if day > 10 else "Stable",
            recovery_status="Improving" if day > 10 else "Stable",
            doctor_recommendation=(
                "Immediate Doctor Review" if prob > 0.65
                else "Increase Monitoring" if prob > 0.45
                else "Continue Current Treatment"
            ),
        )
        db.add(record)
    await db.flush()


# ═══════════════════════════════════════════════════════════════════════════
# DOCTOR ↔ PATIENT ASSIGNMENT
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/assign-doctor")
async def assign_doctor(
    body: AssignDoctorRequest,
    db: AsyncSession = Depends(get_db_session),
    _cu: UserDB = Depends(require_doctor_or_admin),
):
    """Admin or Doctor assigns a doctor to a patient.
    Accepts either doctor_profile_id (DoctorProfileDB.id) or user_id (UserDB.id).
    """
    profile = (await db.execute(
        select(PatientProfileDB).where(PatientProfileDB.user_id == body.patient_user_id)
    )).scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Patient profile not found")

    # Try doctor_profile_id first, then resolve as user_id
    doc_profile = (await db.execute(
        select(DoctorProfileDB).where(DoctorProfileDB.id == body.doctor_profile_id)
    )).scalar_one_or_none()
    if not doc_profile:
        doc_profile = (await db.execute(
            select(DoctorProfileDB).where(DoctorProfileDB.user_id == body.doctor_profile_id)
        )).scalar_one_or_none()
    if not doc_profile:
        raise HTTPException(404, "Doctor profile not found. Ensure the doctor has an approved account.")

    profile.assigned_doctor_id = doc_profile.id
    await db.commit()
    logger.info("Assigned doctor %s (profile=%s) to patient %s", doc_profile.user_id, doc_profile.id, body.patient_user_id)
    return {"message": "Doctor assigned", "patient_user_id": body.patient_user_id,
            "doctor_profile_id": doc_profile.id}


@router.get("/doctor/my-patients", response_model=List[DoctorPatientOut])
async def get_my_patients(
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Return only patients assigned to the authenticated doctor."""
    doc_profile = (await db.execute(
        select(DoctorProfileDB).where(DoctorProfileDB.user_id == cu.id)
    )).scalar_one_or_none()

    if not doc_profile:
        # Doctor has no profile yet — return empty
        return []

    profiles = (await db.execute(
        select(PatientProfileDB).where(
            PatientProfileDB.assigned_doctor_id == doc_profile.id
        )
    )).scalars().all()

    result = []
    for pp in profiles:
        user = (await db.execute(
            select(UserDB).where(UserDB.id == pp.user_id)
        )).scalar_one_or_none()
        if user:
            result.append(DoctorPatientOut(
                user_id=pp.user_id,
                name=user.name,
                email=user.email,
                age=pp.age,
                gender=pp.gender,
                disease_type=pp.disease_type,
                patient_status=pp.patient_status,
                onboarding_completed=pp.onboarding_completed,
                assigned_doctor_id=pp.assigned_doctor_id,
            ))
    return result


@router.get("/patient/{patient_user_id}/assigned-doctor")
async def get_assigned_doctor(
    patient_user_id: str,
    db: AsyncSession = Depends(get_db_session),
    _cu: UserDB = Depends(get_current_user),
):
    """Return the assigned doctor info for a patient."""
    profile = (await db.execute(
        select(PatientProfileDB).where(PatientProfileDB.user_id == patient_user_id)
    )).scalar_one_or_none()
    if not profile or not profile.assigned_doctor_id:
        return {"assigned_doctor": None}

    doc = (await db.execute(
        select(DoctorProfileDB).where(DoctorProfileDB.id == profile.assigned_doctor_id)
    )).scalar_one_or_none()
    if not doc:
        return {"assigned_doctor": None}

    doc_user = (await db.execute(
        select(UserDB).where(UserDB.id == doc.user_id)
    )).scalar_one_or_none()

    return {
        "assigned_doctor": {
            "doctor_profile_id": doc.id,
            "user_id": doc.user_id,
            "name": doc_user.name if doc_user else None,
            "email": doc_user.email if doc_user else None,
            "specialization": doc.specialization,
            "department": doc.department,
            "hospital": doc.hospital,
            "phone": doc.phone,
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# CARE PLAN
# ═══════════════════════════════════════════════════════════════════════════

async def _assert_doctor_access(doctor_user_id: str, patient_user_id: str, db: AsyncSession) -> None:
    """Raise 403 if a doctor tries to access a patient not assigned to them."""
    doc_profile = (await db.execute(
        select(DoctorProfileDB).where(DoctorProfileDB.user_id == doctor_user_id)
    )).scalar_one_or_none()
    if not doc_profile:
        raise HTTPException(403, "Doctor profile not found")
    pat_profile = (await db.execute(
        select(PatientProfileDB).where(PatientProfileDB.user_id == patient_user_id)
    )).scalar_one_or_none()
    if not pat_profile:
        raise HTTPException(404, "Patient not found")
    if pat_profile.assigned_doctor_id != doc_profile.id:
        raise HTTPException(403, "You are not assigned to this patient")


@router.post("/care-plan", response_model=CarePlanOut, status_code=201)
async def create_care_plan(
    body: CarePlanCreate,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(require_doctor_or_admin),
):
    """Doctor creates or replaces a patient's active care plan.
    Doctors may only create plans for their assigned patients.
    Admins are unrestricted.
    """
    role = cu.role.value if hasattr(cu.role, "value") else str(cu.role)
    if role == "doctor":
        await _assert_doctor_access(cu.id, body.patient_user_id, db)
    # Deactivate any existing active plan for this patient
    await db.execute(
        update(CarePlanDB)
        .where(CarePlanDB.patient_user_id == body.patient_user_id,
               CarePlanDB.is_active == True)
        .values(is_active=False)
    )

    plan = CarePlanDB(
        id=str(uuid.uuid4()),
        patient_user_id=body.patient_user_id,
        doctor_user_id=cu.id,
        daily_steps_goal=body.daily_steps_goal,
        sleep_hours_goal=Decimal(str(body.sleep_hours_goal)),
        water_intake_goal_ml=body.water_intake_goal_ml,
        medication_schedule=body.medication_schedule,
        exercise_plan=body.exercise_plan,
        diet_plan=body.diet_plan,
        followup_frequency_days=body.followup_frequency_days,
        monitoring_duration_days=body.monitoring_duration_days,
        risk_threshold=Decimal(str(body.risk_threshold)),
        emergency_threshold=Decimal(str(body.emergency_threshold)),
        notes=body.notes,
        is_active=True,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    # Update patient_records Ideal Twin columns to match new care plan
    await db.execute(
        update(PatientRecordDB)
        .where(PatientRecordDB.patient_id == body.patient_user_id)
        .values(
            expected_steps=body.daily_steps_goal,
            expected_sleep_hours=Decimal(str(body.sleep_hours_goal)),
            water_intake_goal=body.water_intake_goal_ml,
        )
    )
    await db.commit()

    logger.info("Doctor %s created care plan for patient %s", cu.id, body.patient_user_id)
    return plan


@router.get("/care-plan/{patient_user_id}", response_model=Optional[CarePlanOut])
async def get_care_plan(
    patient_user_id: str,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Get the active care plan for a patient.
    Patients can only view their own. Doctors see only assigned patients.
    """
    role = cu.role.value if hasattr(cu.role, "value") else str(cu.role)
    if role == "patient" and cu.id != patient_user_id:
        raise HTTPException(403, "You can only view your own care plan")
    if role == "doctor":
        await _assert_doctor_access(cu.id, patient_user_id, db)
    plan = (await db.execute(
        select(CarePlanDB)
        .where(CarePlanDB.patient_user_id == patient_user_id,
               CarePlanDB.is_active == True)
        .order_by(CarePlanDB.created_at.desc())
    )).scalar_one_or_none()
    return plan


# ═══════════════════════════════════════════════════════════════════════════
# DAILY VITALS (Real Twin update)
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/vitals", response_model=DailyVitalsOut, status_code=201)
async def submit_daily_vitals(
    body: DailyVitalsRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Patient submits today's vitals. Upserts the daily_vitals table (one row per day)
    and appends a NEW monitoring day in patient_records so the timeline grows.
    """
    log_date = body.log_date or str(date.today())

    # ── Validate sensible ranges ────────────────────────────────────────
    if body.heart_rate is not None and not (30 <= body.heart_rate <= 250):
        raise HTTPException(400, "Heart rate must be between 30 and 250 bpm")
    if body.spo2 is not None and not (50.0 <= body.spo2 <= 100.0):
        raise HTTPException(400, "SpO₂ must be between 50 and 100 %")
    if body.systolic_bp is not None and not (50 <= body.systolic_bp <= 300):
        raise HTTPException(400, "Systolic BP must be between 50 and 300 mmHg")
    if body.diastolic_bp is not None and not (30 <= body.diastolic_bp <= 200):
        raise HTTPException(400, "Diastolic BP must be between 30 and 200 mmHg")
    if body.actual_steps is not None and body.actual_steps < 0:
        raise HTTPException(400, "Steps cannot be negative")
    if body.actual_sleep_hours is not None and not (0 <= body.actual_sleep_hours <= 24):
        raise HTTPException(400, "Sleep hours must be between 0 and 24")
    if body.water_intake_ml is not None and body.water_intake_ml < 0:
        raise HTTPException(400, "Water intake cannot be negative")
    if body.pain_level is not None and not (0 <= body.pain_level <= 10):
        raise HTTPException(400, "Pain level must be between 0 and 10")

    # ── Upsert patient_vitals_daily (one row per date) ─────────────────
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(PatientVitalsDailyDB).where(
            PatientVitalsDailyDB.patient_user_id == cu.id,
            PatientVitalsDailyDB.log_date == log_date,
        )
    )

    vital = PatientVitalsDailyDB(
        id=str(uuid.uuid4()),
        patient_user_id=cu.id,
        log_date=log_date,
        heart_rate=body.heart_rate,
        systolic_bp=body.systolic_bp,
        diastolic_bp=body.diastolic_bp,
        spo2=Decimal(str(body.spo2)) if body.spo2 is not None else None,
        body_temperature=Decimal(str(body.body_temperature)) if body.body_temperature is not None else None,
        weight_kg=Decimal(str(body.weight_kg)) if body.weight_kg is not None else None,
        actual_steps=body.actual_steps,
        actual_sleep_hours=Decimal(str(body.actual_sleep_hours)) if body.actual_sleep_hours is not None else None,
        water_intake_ml=body.water_intake_ml,
        medication_taken=body.medication_taken,
        exercise_completed=body.exercise_completed,
        diet_compliance=Decimal(str(body.diet_compliance)) if body.diet_compliance is not None else None,
        pain_level=body.pain_level,
        mood=body.mood,
        symptoms=body.symptoms,
        notes=body.notes,
    )
    db.add(vital)
    await db.flush()

    # ── Append a NEW patient_records day (Bug #7 fix) ──────────────────
    # Get the latest existing day number
    from sqlalchemy import func as sqlfunc
    max_day_result = await db.execute(
        select(sqlfunc.max(PatientRecordDB.day)).where(PatientRecordDB.patient_id == cu.id)
    )
    current_max_day = max_day_result.scalar() or 0

    # Get the last record to copy baseline values from
    latest_record = (await db.execute(
        select(PatientRecordDB)
        .where(PatientRecordDB.patient_id == cu.id)
        .order_by(PatientRecordDB.day.desc())
        .limit(1)
    )).scalar_one_or_none()

    if latest_record:
        new_day = current_max_day + 1

        from app.models.schemas import PatientRecord
        pyd_record = PatientRecord(
            patient_id=cu.id,
            day=new_day,
            patient_name=latest_record.patient_name,
            age=latest_record.age,
            gender=latest_record.gender, # type: ignore
            bmi=float(latest_record.bmi) if latest_record.bmi else 24.0,
            smoking_status=latest_record.smoking_status, # type: ignore
            alcohol_consumption=latest_record.alcohol_consumption, # type: ignore
            disease_type=latest_record.disease_type,
            heart_rate=body.heart_rate or latest_record.heart_rate,
            systolic_bp=body.systolic_bp or latest_record.systolic_bp,
            diastolic_bp=body.diastolic_bp or latest_record.diastolic_bp,
            spo2=float(body.spo2) if body.spo2 is not None else (float(latest_record.spo2) if latest_record.spo2 else 97.0),
            respiratory_rate=latest_record.respiratory_rate or 16,
            body_temperature=float(body.body_temperature) if body.body_temperature is not None else (float(latest_record.body_temperature) if latest_record.body_temperature else 36.6),
            expected_steps=latest_record.expected_steps or 8000,
            expected_sleep_hours=float(latest_record.expected_sleep_hours) if latest_record.expected_sleep_hours else 8.0,
            water_intake_goal=latest_record.water_intake_goal or 2000,
            actual_steps=body.actual_steps or (latest_record.actual_steps or 0),
            actual_sleep_hours=float(body.actual_sleep_hours) if body.actual_sleep_hours is not None else (float(latest_record.actual_sleep_hours) if latest_record.actual_sleep_hours else 0.0),
            water_intake=body.water_intake_ml or (latest_record.water_intake or 0),
            medication_taken=body.medication_taken or (latest_record.medication_taken or "No"),
            exercise_completed=body.exercise_completed or (latest_record.exercise_completed or "No"),
            diet_compliance=float(body.diet_compliance) if body.diet_compliance is not None else (float(latest_record.diet_compliance) if latest_record.diet_compliance else 100.0),
        )

        # Load history
        history_db = (await db.execute(
            select(PatientRecordDB)
            .where(PatientRecordDB.patient_id == cu.id)
            .order_by(PatientRecordDB.day.asc())
        )).scalars().all()

        history_pydantic = [PatientRecord.model_validate(h) for h in history_db]

        # Run calculations
        from app.services.compliance_calculator import ComplianceCalculator
        from app.services.health_score_calculator import HealthScoreCalculator
        from app.services.prediction_system import PredictionSystem
        from app.services.recommendation_engine import RecommendationEngine

        comp_calc = ComplianceCalculator()
        health_calc = HealthScoreCalculator()
        pred_system = PredictionSystem()
        rec_engine = RecommendationEngine()

        # Append today's record to calculate compliance and health scores
        sim_history = list(history_pydantic) + [pyd_record]

        new_compliance = await comp_calc.calculate_compliance_score(sim_history, window_days=len(sim_history))
        pyd_record.compliance_score = new_compliance
        pyd_record.deviation_score = max(0.0, min(100.0, 100.0 - new_compliance))

        new_real_health = await health_calc.calculate_real_health_score(pyd_record)
        pyd_record.real_health_score = new_real_health
        pyd_record.ideal_health_score = await health_calc.calculate_ideal_health_score(pyd_record)

        # Patch real health score for recovery calculation
        pyd_record_patched = pyd_record.model_copy(update={"real_health_score": new_real_health})
        sim_history[-1] = pyd_record_patched

        new_recovery = await health_calc.calculate_recovery_score(sim_history)
        pyd_record.recovery_score = new_recovery

        new_trend = await pred_system.analyze_health_trend(sim_history)
        pyd_record.health_trend = new_trend # type: ignore

        # ML Prediction (with fallback)
        inference_engine = getattr(request.app.state, "inference_engine", None)

        new_prob: float
        new_risk: str

        if inference_engine is None or not inference_engine.is_loaded:
            if pyd_record.deviation_score >= 40:
                new_prob = 0.70
                new_risk = "High"
            else:
                new_prob = 0.15
                new_risk = "Low"
        else:
            try:
                inference_result = await inference_engine.predict(pyd_record)
                new_prob = inference_result.readmission_probability
                new_risk = inference_result.risk_level
            except Exception as exc:
                logger.error("Vitals submission inference failed: %s", exc)
                new_prob = 0.15
                new_risk = "Low"

        pyd_record.risk_level = new_risk # type: ignore
        pyd_record.readmission_probability = new_prob

        new_status = await pred_system.classify_recovery_status(
            recovery_score=new_recovery,
            health_trend=new_trend,
            risk_level=new_risk
        )

        new_rec = await rec_engine.generate_recommendation(
            risk_level=new_risk,
            recovery_status=new_status,
            compliance_score=new_compliance,
            deviation_score=pyd_record.deviation_score,
            readmission_probability=new_prob,
            patient_id=cu.id
        )

        new_record = PatientRecordDB(
            patient_id=cu.id,
            day=new_day,
            patient_name=latest_record.patient_name,
            age=latest_record.age,
            gender=latest_record.gender,
            bmi=latest_record.bmi,
            disease_type=latest_record.disease_type,
            smoking_status=latest_record.smoking_status,
            alcohol_consumption=latest_record.alcohol_consumption,
            heart_rate=pyd_record.heart_rate,
            systolic_bp=pyd_record.systolic_bp,
            diastolic_bp=pyd_record.diastolic_bp,
            spo2=Decimal(str(pyd_record.spo2)),
            respiratory_rate=latest_record.respiratory_rate,
            body_temperature=Decimal(str(pyd_record.body_temperature)),
            expected_steps=latest_record.expected_steps,
            expected_sleep_hours=latest_record.expected_sleep_hours,
            water_intake_goal=latest_record.water_intake_goal,
            actual_steps=pyd_record.actual_steps,
            actual_sleep_hours=Decimal(str(pyd_record.actual_sleep_hours)),
            water_intake=pyd_record.water_intake,
            medication_taken=pyd_record.medication_taken,
            exercise_completed=pyd_record.exercise_completed,
            diet_compliance=Decimal(str(pyd_record.diet_compliance)),
            compliance_score=Decimal(str(round(new_compliance, 2))),
            ideal_health_score=Decimal(str(round(pyd_record.ideal_health_score, 2))),
            real_health_score=Decimal(str(round(new_real_health, 2))),
            deviation_score=Decimal(str(round(pyd_record.deviation_score, 2))),
            recovery_score=Decimal(str(round(new_recovery, 2))),
            readmission_probability=Decimal(str(round(new_prob, 4))),
            risk_level=new_risk,
            health_trend=new_trend,
            recovery_status=new_status,
            doctor_recommendation=new_rec,
        )
        db.add(new_record)

    await db.commit()
    await db.refresh(vital)
    logger.info("Patient %s submitted vitals for %s (new monitoring day %s)", cu.id, log_date, current_max_day + 1)
    return vital


@router.get("/vitals/history", response_model=List[DailyVitalsOut])
async def get_vitals_history(
    limit: int = 30,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Return the patient's recent daily vital entries."""
    result = await db.execute(
        select(PatientVitalsDailyDB)
        .where(PatientVitalsDailyDB.patient_user_id == cu.id)
        .order_by(PatientVitalsDailyDB.log_date.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/vitals/today", response_model=Optional[DailyVitalsOut])
async def get_today_vitals(
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Return today's vitals entry if submitted."""
    today = str(date.today())
    vital = (await db.execute(
        select(PatientVitalsDailyDB).where(
            PatientVitalsDailyDB.patient_user_id == cu.id,
            PatientVitalsDailyDB.log_date == today,
        )
    )).scalar_one_or_none()
    return vital


# ═══════════════════════════════════════════════════════════════════════════
# MEDICAL HISTORY
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/medical-history", response_model=MedicalHistoryOut, status_code=201)
async def create_medical_history(
    body: MedicalHistoryCreate,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(require_doctor_or_admin),
):
    """Doctor creates or updates medical history. Doctors restricted to assigned patients."""
    role = cu.role.value if hasattr(cu.role, "value") else str(cu.role)
    if role == "doctor":
        await _assert_doctor_access(cu.id, body.patient_user_id, db)

    existing = (await db.execute(
        select(MedicalHistoryDB).where(MedicalHistoryDB.patient_user_id == body.patient_user_id)
    )).scalar_one_or_none()

    if existing:
        for field, val in body.model_dump(exclude={"patient_user_id"}).items():
            if val is not None:
                setattr(existing, field, val)
        existing.created_by_doctor_id = cu.id
        await db.commit()
        await db.refresh(existing)
        return existing

    history = MedicalHistoryDB(
        id=str(uuid.uuid4()),
        patient_user_id=body.patient_user_id,
        created_by_doctor_id=cu.id,
        **body.model_dump(exclude={"patient_user_id"}),
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)
    logger.info("Doctor %s created medical history for patient %s", cu.id, body.patient_user_id)
    return history


@router.get("/medical-history/{patient_user_id}", response_model=Optional[MedicalHistoryOut])
async def get_medical_history(
    patient_user_id: str,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
):
    """Get medical history. Patients: own only. Doctors: assigned only. Admins: all."""
    role = cu.role.value if hasattr(cu.role, "value") else str(cu.role)
    if role == "patient" and cu.id != patient_user_id:
        raise HTTPException(403, "You can only view your own medical history")
    if role == "doctor":
        await _assert_doctor_access(cu.id, patient_user_id, db)

    return (await db.execute(
        select(MedicalHistoryDB).where(MedicalHistoryDB.patient_user_id == patient_user_id)
    )).scalar_one_or_none()


@router.patch("/medical-history/{patient_user_id}/notes")
async def update_doctor_notes(
    patient_user_id: str,
    notes: str,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(require_doctor_or_admin),
):
    """Doctor updates clinical notes. Restricted to assigned patients."""
    role = cu.role.value if hasattr(cu.role, "value") else str(cu.role)
    if role == "doctor":
        await _assert_doctor_access(cu.id, patient_user_id, db)

    history = (await db.execute(
        select(MedicalHistoryDB).where(MedicalHistoryDB.patient_user_id == patient_user_id)
    )).scalar_one_or_none()

    if not history:
        history = MedicalHistoryDB(
            id=str(uuid.uuid4()),
            patient_user_id=patient_user_id,
            created_by_doctor_id=cu.id,
            doctor_notes=notes,
        )
        db.add(history)
    else:
        history.doctor_notes = notes
        history.created_by_doctor_id = cu.id

    await db.commit()
    return {"message": "Doctor notes updated", "patient_user_id": patient_user_id}

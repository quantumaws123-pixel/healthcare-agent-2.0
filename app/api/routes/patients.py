"""Patient API route handlers for Healthcare Agent 2.0 Backend ML System.

Implements:
  - GET /patients  — paginated, filterable, sorted patient list (Tasks 16.1)
  - GET /patients/{patient_id}/summary — 30-day daily trend data (Task 16.2)

**Validates: Requirements 1.1, 1.2, 1.5, 1.6, 13.1, 13.2, 13.3, 13.4, 13.5,
             13.6, 13.7, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6**
"""

import math
import logging
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.auth.dependencies import get_current_user
from app.auth.models import UserDB
from app.repositories.patient_repository import PatientRepository
from app.models.schemas import PatientRecord
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


def _role(user: UserDB) -> str:
    r = user.role
    return r.value if hasattr(r, "value") else str(r)


async def _assert_patient_access(patient_user_id: str, current_user: UserDB, db: AsyncSession) -> None:
    """Check if the current user can access the given patient's data.
    
    - Admins: full access
    - Patients: own data only
    - Doctors: only patients assigned to them
    """
    role = _role(current_user)
    if role == "admin":
        return
    if role == "patient":
        if current_user.id != patient_user_id:
            raise HTTPException(status_code=403, detail="Access denied: patients can only view their own data")
        return
    if role == "doctor":
        from app.database.models import DoctorProfileDB, PatientProfileDB
        doc_profile = (await db.execute(
            select(DoctorProfileDB).where(DoctorProfileDB.user_id == current_user.id)
        )).scalar_one_or_none()
        if not doc_profile:
            raise HTTPException(status_code=403, detail="Doctor profile not found")
        pat_profile = (await db.execute(
            select(PatientProfileDB).where(PatientProfileDB.user_id == patient_user_id)
        )).scalar_one_or_none()
        if not pat_profile or pat_profile.assigned_doctor_id != doc_profile.id:
            raise HTTPException(status_code=403, detail="Access denied: you are not assigned to this patient")
        return


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class PatientSummary(BaseModel):
    """
    Condensed patient information for list view — field names match the
    TypeScript ``PatientSummary`` interface consumed by the frontend.

    Pydantic aliases map the internal snake_case attribute names to the
    PascalCase names the frontend expects.  ``populate_by_name=True``
    allows constructing the model with either the alias or the Python
    attribute name.
    """

    model_config = ConfigDict(populate_by_name=True)

    Patient_ID: str = Field(..., alias="Patient_ID", serialization_alias="Patient_ID")
    Age: int = Field(..., alias="Age", serialization_alias="Age")
    Gender: str = Field(..., alias="Gender", serialization_alias="Gender")
    Disease_Type: str = Field(..., alias="Disease_Type", serialization_alias="Disease_Type")
    Risk_Level: str = Field(..., alias="Risk_Level", serialization_alias="Risk_Level")
    Recovery_Status: str = Field(..., alias="Recovery_Status", serialization_alias="Recovery_Status")
    Readmission_Probability: float = Field(..., alias="Readmission_Probability", serialization_alias="Readmission_Probability")
    Compliance_Score: float = Field(..., alias="Compliance_Score", serialization_alias="Compliance_Score")
    Latest_Day: int = Field(..., alias="Latest_Day", serialization_alias="Latest_Day")
    Doctor_Recommendation: str = Field(..., alias="Doctor_Recommendation", serialization_alias="Doctor_Recommendation")


class PaginatedResponse(BaseModel):
    """Paginated wrapper — field names match the TypeScript ``PaginatedResponse<T>``."""

    data: list[PatientSummary]
    page: int
    page_size: int
    total: int
    total_pages: int


class DailyTrend(BaseModel):
    """Single day of trend data for a patient summary (snake_case matches frontend)."""

    day: int
    compliance_score: Optional[float] = None
    deviation_score: Optional[float] = None
    recovery_score: Optional[float] = None
    health_trend: Optional[str] = None
    readmission_probability: Optional[float] = None
    real_health_score: Optional[float] = None
    ideal_health_score: Optional[float] = None
    
    # Timeline details
    medication_deviation: Optional[float] = None
    sleep_deviation: Optional[float] = None
    exercise_deviation: Optional[float] = None
    water_deviation: Optional[float] = None
    heart_rate_deviation: Optional[float] = None
    bp_deviation: Optional[float] = None
    weight_deviation: Optional[float] = None
    spo2_deviation: Optional[float] = None
    temp_deviation: Optional[float] = None
    
    medication_taken: Optional[str] = None
    exercise_completed: Optional[str] = None
    actual_steps: Optional[int] = None
    actual_sleep_hours: Optional[float] = None
    water_intake: Optional[int] = None
    expected_steps: Optional[int] = None
    expected_sleep_hours: Optional[float] = None
    water_intake_goal: Optional[int] = None
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    spo2: Optional[float] = None
    body_temperature: Optional[float] = None
    weight_kg: Optional[float] = None
    expected_weight: Optional[float] = None
    
    ai_recommendations: Optional[list[str]] = None
    shap_reasons: Optional[list[str]] = None


class PatientSummaryResponse(BaseModel):
    """Response body for GET /patients/{patient_id}/summary."""

    patient_id: str
    patient_name: Optional[str] = None
    disease_type: Optional[str] = None
    current_risk_level: Optional[str] = None
    current_recovery_status: Optional[str] = None
    daily_trends: list[DailyTrend]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_patient_summary(record) -> PatientSummary:
    """
    Convert a PatientRecordDB ORM row to a PatientSummary Pydantic model
    with PascalCase field names expected by the frontend.
    """
    return PatientSummary.model_validate(
        {
            "Patient_ID": record.patient_id or "",
            "Age": record.age or 0,
            "Gender": record.gender or "",
            "Disease_Type": record.disease_type or "",
            "Risk_Level": record.risk_level or "Low",
            "Recovery_Status": record.recovery_status or "Stable",
            "Readmission_Probability": float(record.readmission_probability)
            if record.readmission_probability is not None
            else 0.0,
            "Compliance_Score": float(record.compliance_score)
            if record.compliance_score is not None
            else 0.0,
            "Latest_Day": int(record.day) if record.day is not None else 0,
            "Doctor_Recommendation": record.doctor_recommendation or "Continue Current Treatment",
        }
    )


# ---------------------------------------------------------------------------
# GET /patients
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=PaginatedResponse,
    response_model_by_alias=True,
    summary="List patients with pagination and filtering",
    description=(
        "Returns a paginated, optionally filtered list of patient summaries. "
        "Results are sorted by risk level priority (Critical → High → Medium → Low) "
        "and then by readmission_probability descending."
    ),
)
async def list_patients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100, alias="page_size"),
    disease_type: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    patient_id: Optional[str] = Query(default=None, alias="patient_id"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user),
) -> PaginatedResponse:
    """
    GET /patients

    Retrieves the latest patient record for each patient, with optional
    filtering by disease_type and/or risk_level.  Results are sorted by
    risk priority then readmission_probability descending.

    **Validates: Requirements 1.1, 1.5, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7**
    """
    repo = PatientRepository(db)

    try:
        records, total = await repo.get_patients_paginated(
            page=page,
            page_size=page_size,
            disease_type=disease_type,
            risk_level=risk_level,
            patient_id=patient_id,
        )
    except Exception as exc:
        logger.error("Error fetching patient list: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve patient list") from exc

    # Calculate total_pages using ceiling division (Requirement 13.4)
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    summaries = [_to_patient_summary(r) for r in records]

    return PaginatedResponse(
        data=summaries,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )

# ---------------------------------------------------------------------------
# GET /patients/{patient_id}/latest
# ---------------------------------------------------------------------------

@router.get(
    "/{patient_id}/latest",
    response_model=PatientRecord,
    summary="Get the latest patient record including vitals",
    description="Returns the latest daily record for the specified patient.",
)
async def get_latest_patient_record(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user),
) -> PatientRecord:
    """GET /patients/{patient_id}/latest — auth required."""
    await _assert_patient_access(patient_id, current_user, db)

    repo = PatientRepository(db)
    try:
        record = await repo.get_patient_by_id(patient_id=patient_id)
    except Exception as exc:
        logger.error("Error fetching latest record for patient %s: %s", patient_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve latest patient record") from exc

    if not record:
        raise HTTPException(status_code=404, detail=f"Patient record for '{patient_id}' not found")
    
    pydantic_record = PatientRecord.model_validate(record)
    from app.services.enrichment import enrich_patient_record
    await enrich_patient_record(pydantic_record, db)
    return pydantic_record


# ---------------------------------------------------------------------------
# GET /patients/{patient_id}/summary
# ---------------------------------------------------------------------------


@router.get(
    "/{patient_id}/summary",
    response_model=PatientSummaryResponse,
    summary="Get 30-day daily trend summary for a patient",
    description=(
        "Returns up to 30 days of daily trend data for the specified patient. "
        "If the patient does not exist a 404 is returned. "
        "Records are ordered by day ascending."
    ),
)
async def get_patient_summary(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user),
) -> PatientSummaryResponse:
    """GET /patients/{patient_id}/summary — auth required."""
    await _assert_patient_access(patient_id, current_user, db)
    repo = PatientRepository(db)

    try:
        records = await repo.get_patient_summary(patient_id=patient_id, days=30)
    except Exception as exc:
        logger.error(
            "Error fetching summary for patient %s: %s", patient_id, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve patient summary",
        ) from exc

    # 404 when no records exist for this patient_id (Requirement 18.5 / 1.6)
    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"Patient '{patient_id}' not found",
        )

    # Use the most recent record for top-level fields
    latest = records[-1]

    # Build daily_trends array ordered by day ascending (Requirement 18.3)
    daily_trends: list[DailyTrend] = []
    from app.services.enrichment import enrich_patient_record
    for record in records:
        pydantic_rec = PatientRecord.model_validate(record)
        await enrich_patient_record(pydantic_rec, db)
        daily_trends.append(
            DailyTrend(
                day=pydantic_rec.day,
                compliance_score=pydantic_rec.compliance_score,
                deviation_score=pydantic_rec.deviation_score,
                recovery_score=pydantic_rec.recovery_score,
                health_trend=pydantic_rec.health_trend,
                readmission_probability=pydantic_rec.readmission_probability,
                real_health_score=pydantic_rec.real_health_score,
                ideal_health_score=pydantic_rec.ideal_health_score,
                medication_deviation=pydantic_rec.medication_deviation,
                sleep_deviation=pydantic_rec.sleep_deviation,
                exercise_deviation=pydantic_rec.exercise_deviation,
                water_deviation=pydantic_rec.water_deviation,
                heart_rate_deviation=pydantic_rec.heart_rate_deviation,
                bp_deviation=pydantic_rec.bp_deviation,
                weight_deviation=pydantic_rec.weight_deviation,
                spo2_deviation=pydantic_rec.spo2_deviation,
                temp_deviation=pydantic_rec.temp_deviation,
                medication_taken=pydantic_rec.medication_taken,
                exercise_completed=pydantic_rec.exercise_completed,
                actual_steps=pydantic_rec.actual_steps,
                actual_sleep_hours=pydantic_rec.actual_sleep_hours,
                water_intake=pydantic_rec.water_intake,
                expected_steps=pydantic_rec.expected_steps,
                expected_sleep_hours=pydantic_rec.expected_sleep_hours,
                water_intake_goal=pydantic_rec.water_intake_goal,
                heart_rate=pydantic_rec.heart_rate,
                systolic_bp=pydantic_rec.systolic_bp,
                diastolic_bp=pydantic_rec.diastolic_bp,
                spo2=pydantic_rec.spo2,
                body_temperature=pydantic_rec.body_temperature,
                weight_kg=pydantic_rec.weight_kg,
                expected_weight=pydantic_rec.expected_weight,
                ai_recommendations=pydantic_rec.ai_recommendations,
                shap_reasons=pydantic_rec.shap_reasons,
            )
        )

    # Enrich the latest record too to populate top-level fields correctly
    latest_pydantic = PatientRecord.model_validate(latest)
    await enrich_patient_record(latest_pydantic, db)

    return PatientSummaryResponse(
        patient_id=latest_pydantic.patient_id,
        patient_name=latest_pydantic.patient_name,
        disease_type=latest_pydantic.disease_type,
        current_risk_level=latest_pydantic.risk_level,
        current_recovery_status=latest_pydantic.recovery_status,
        daily_trends=daily_trends,
    )


class SimulationRequest(BaseModel):
    actual_steps: Optional[int] = None
    actual_sleep_hours: Optional[float] = None
    water_intake: Optional[int] = None
    medication_taken: Optional[Literal["Yes", "No"]] = None
    weight_kg: Optional[float] = None


class SimulationResponse(BaseModel):
    original_recovery_score: float
    original_risk_level: str
    original_readmission_probability: float
    simulated_recovery_score: float
    simulated_risk_level: str
    simulated_readmission_probability: float
    original_recommendations: list[str]
    simulated_recommendations: list[str]


@router.post(
    "/{patient_id}/simulate",
    response_model=SimulationResponse,
    summary="Simulate recovery outcome based on custom vitals/behavior inputs",
)
async def simulate_recovery(
    patient_id: str,
    body: SimulationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserDB = Depends(get_current_user),
) -> SimulationResponse:
    """Simulate recovery outcome by temporarily overwriting current daily vitals inputs."""
    await _assert_patient_access(patient_id, current_user, db)
    
    # 1. Fetch latest record for patient
    repo = PatientRepository(db)
    latest_db_record = await repo.get_patient_by_id(patient_id=patient_id)
    if not latest_db_record:
        raise HTTPException(status_code=404, detail="Patient record not found")
        
    latest_record = PatientRecord.model_validate(latest_db_record)
    from app.services.enrichment import enrich_patient_record
    await enrich_patient_record(latest_record, db)
    
    # 2. Fetch history up to 30 days
    history_db = await repo.get_patient_summary(patient_id=patient_id, days=30)
    history_pydantic = [PatientRecord.model_validate(h) for h in history_db]
    for h in history_pydantic:
        await enrich_patient_record(h, db)
        
    # 3. Create simulated copy of latest record
    sim_record = latest_record.model_copy()
    if body.actual_steps is not None:
        sim_record.actual_steps = body.actual_steps
    if body.actual_sleep_hours is not None:
        sim_record.actual_sleep_hours = body.actual_sleep_hours
    if body.water_intake is not None:
        sim_record.water_intake = body.water_intake
    if body.medication_taken is not None:
        sim_record.medication_taken = body.medication_taken
    if body.weight_kg is not None:
        sim_record.weight_kg = body.weight_kg
        
    # 4. Re-calculate compliance score
    from app.services.compliance_calculator import ComplianceCalculator
    from app.services.health_score_calculator import HealthScoreCalculator
    
    comp_calc = ComplianceCalculator()
    # Substitute the last day in history with the simulated record to get simulated compliance
    sim_history = list(history_pydantic)
    if sim_history:
        sim_history[-1] = sim_record
    else:
        sim_history = [sim_record]
        
    sim_compliance = await comp_calc.calculate_compliance_score(sim_history, window_days=len(sim_history))
    sim_record.compliance_score = sim_compliance
    sim_record.deviation_score = max(0.0, min(100.0, 100.0 - sim_compliance))
    
    # 5. Re-calculate real health score
    health_calc = HealthScoreCalculator()
    sim_real_health = await health_calc.calculate_real_health_score(sim_record)
    sim_record.real_health_score = sim_real_health
    
    # Substitute in sim_history for recovery score calculation
    sim_record_patched = sim_record.model_copy(update={"real_health_score": sim_real_health})
    sim_history[-1] = sim_record_patched
    
    sim_recovery = await health_calc.calculate_recovery_score(sim_history)
    sim_record.recovery_score = sim_recovery
    
    # 6. Run prediction (ML or fallback)
    inference_engine = getattr(request.app.state, "inference_engine", None)
    
    sim_prob: float
    sim_risk: str
    
    if inference_engine is None or not inference_engine.is_loaded:
        # Fallback rule-based prediction
        if sim_record.deviation_score >= 40:
            sim_prob = 0.70
            sim_risk = "High"
        elif sim_record.deviation_score >= 20:
            sim_prob = 0.45
            sim_risk = "Medium"
        else:
            sim_prob = 0.15
            sim_risk = "Low"
    else:
        try:
            inference_result = await inference_engine.predict(sim_record)
            sim_prob = inference_result.readmission_probability
            sim_risk = inference_result.risk_level
        except Exception as exc:
            logger.error("Simulation inference failed: %s", exc)
            sim_prob = 0.15
            sim_risk = "Low"
            
    sim_record.risk_level = sim_risk
    sim_record.readmission_probability = sim_prob
    
    # 7. Generate recommendations
    from app.services.deviation_engine import DeviationEngine
    sim_recs = DeviationEngine.generate_recommendations(sim_record)
    
    return SimulationResponse(
        original_recovery_score=latest_record.recovery_score or 50.0,
        original_risk_level=latest_record.risk_level or "Low",
        original_readmission_probability=latest_record.readmission_probability or 0.15,
        simulated_recovery_score=sim_recovery,
        simulated_risk_level=sim_risk,
        simulated_readmission_probability=sim_prob,
        original_recommendations=latest_record.ai_recommendations or [],
        simulated_recommendations=sim_recs,
    )

"""Patient API route handlers for Healthcare Agent 2.0 Backend ML System.

Implements:
  - GET /patients  — paginated, filterable, sorted patient list (Tasks 16.1)
  - GET /patients/{patient_id}/summary — 30-day daily trend data (Task 16.2)

**Validates: Requirements 1.1, 1.2, 1.5, 1.6, 13.1, 13.2, 13.3, 13.4, 13.5,
             13.6, 13.7, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6**
"""

import math
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.repositories.patient_repository import PatientRepository
from app.models.schemas import PatientRecord
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


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
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (1-indexed). Must be ≥ 1.",
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
        alias="page_size",
        description="Number of results per page (1–100).",
    ),
    disease_type: Optional[str] = Query(
        default=None,
        description="Filter results to a specific Disease_Type value.",
    ),
    risk_level: Optional[str] = Query(
        default=None,
        description="Filter results to a specific Risk_Level value (Low, Medium, High, Critical).",
    ),
    patient_id: Optional[str] = Query(
        default=None,
        alias="patient_id",
        description="Filter results to a specific patient ID (substring).",
    ),
    db: AsyncSession = Depends(get_db_session),
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
) -> PatientRecord:
    """
    GET /patients/{patient_id}/latest
    """
    repo = PatientRepository(db)
    try:
        record = await repo.get_patient_by_id(patient_id=patient_id)
    except Exception as exc:
        logger.error("Error fetching latest record for patient %s: %s", patient_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve latest patient record") from exc

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Patient record for '{patient_id}' not found",
        )
    return record


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
) -> PatientSummaryResponse:
    """
    GET /patients/{patient_id}/summary

    Retrieves the 30-day (or fewer if less data exists) daily trend data for a
    specific patient. Returns 404 when the patient_id is not found.

    **Validates: Requirements 1.2, 1.6, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6**
    """
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
    for record in records:
        daily_trends.append(
            DailyTrend(
                day=record.day,
                compliance_score=float(record.compliance_score) if record.compliance_score is not None else None,
                deviation_score=float(record.deviation_score) if record.deviation_score is not None else None,
                recovery_score=float(record.recovery_score) if record.recovery_score is not None else None,
                health_trend=record.health_trend,
                readmission_probability=float(record.readmission_probability) if record.readmission_probability is not None else None,
                real_health_score=float(record.real_health_score) if record.real_health_score is not None else None,
                ideal_health_score=float(record.ideal_health_score) if record.ideal_health_score is not None else None,
            )
        )

    return PatientSummaryResponse(
        patient_id=latest.patient_id,
        patient_name=latest.patient_name,
        disease_type=latest.disease_type,
        current_risk_level=latest.risk_level,
        current_recovery_status=latest.recovery_status,
        daily_trends=daily_trends,
    )

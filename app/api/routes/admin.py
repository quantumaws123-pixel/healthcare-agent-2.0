"""Admin management endpoints - admin-only access."""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.database.connection import get_db_session
from app.auth.models import UserDB, UserRole
from app.auth.dependencies import get_current_user
from app.auth.router import hash_password
from app.database.models import DoctorProfileDB, PatientProfileDB

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


# Schemas
class CreateAdminRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class AdminUserOut(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    status: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class DoctorOut(BaseModel):
    id: str
    email: str
    name: Optional[str]
    status: str
    is_active: bool
    specialization: Optional[str]
    hospital: Optional[str]
    experience_years: Optional[int]
    created_at: str

    model_config = {"from_attributes": True}


# Dependency: require admin role
async def require_admin(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    if current_user.role != UserRole.admin:
        raise HTTPException(403, "Admin access required")
    return current_user


# Admin Management Endpoints
@router.post("/admins", response_model=AdminUserOut, status_code=201)
async def create_admin(
    body: CreateAdminRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Create a new admin user. Only admins can create other admins."""
    existing = (await db.execute(select(UserDB).where(UserDB.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    user = UserDB(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        role=UserRole.admin,
        status="approved",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info("Admin %s created new admin: %s", admin.email, user.email)
    return user


@router.get("/admins", response_model=List[AdminUserOut])
async def list_admins(
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """List all admin users."""
    result = await db.execute(
        select(UserDB).where(UserDB.role == UserRole.admin).order_by(UserDB.created_at.desc())
    )
    admins = result.scalars().all()
    return admins


@router.patch("/admins/{user_id}/activate")
async def activate_admin(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Activate an admin user."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.admin:
        raise HTTPException(404, "Admin not found")
    
    user.is_active = True
    await db.commit()
    logger.info("Admin %s activated admin %s", admin.email, user.email)
    return {"message": "Admin activated", "user_id": user_id}


@router.patch("/admins/{user_id}/deactivate")
async def deactivate_admin(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Deactivate an admin user."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.admin:
        raise HTTPException(404, "Admin not found")
    
    if user.id == admin.id:
        raise HTTPException(400, "Cannot deactivate yourself")
    
    user.is_active = False
    await db.commit()
    logger.info("Admin %s deactivated admin %s", admin.email, user.email)
    return {"message": "Admin deactivated", "user_id": user_id}


@router.delete("/admins/{user_id}")
async def delete_admin(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Delete an admin user."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.admin:
        raise HTTPException(404, "Admin not found")
    
    if user.id == admin.id:
        raise HTTPException(400, "Cannot delete yourself")
    
    await db.delete(user)
    await db.commit()
    logger.info("Admin %s deleted admin %s", admin.email, user.email)
    return {"message": "Admin deleted", "user_id": user_id}


# Doctor Management Endpoints
@router.get("/doctors/pending", response_model=List[DoctorOut])
async def list_pending_doctors(
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """List all pending doctor registrations."""
    result = await db.execute(
        select(UserDB)
        .where(UserDB.role == UserRole.doctor, UserDB.status == "pending")
        .order_by(UserDB.created_at.desc())
    )
    doctors = result.scalars().all()
    
    # Enrich with profile data
    doctor_list = []
    for doc in doctors:
        profile = (await db.execute(
            select(DoctorProfileDB).where(DoctorProfileDB.user_id == doc.id)
        )).scalar_one_or_none()
        
        doctor_list.append({
            "id": doc.id,
            "email": doc.email,
            "name": doc.name,
            "status": doc.status,
            "is_active": doc.is_active,
            "specialization": profile.specialization if profile else None,
            "hospital": profile.hospital if profile else None,
            "experience_years": profile.experience_years if profile else None,
            "created_at": doc.created_at.isoformat(),
        })
    
    return doctor_list


@router.get("/doctors", response_model=List[DoctorOut])
async def list_all_doctors(
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """List all doctors (pending, approved, rejected)."""
    result = await db.execute(
        select(UserDB)
        .where(UserDB.role == UserRole.doctor)
        .order_by(UserDB.created_at.desc())
    )
    doctors = result.scalars().all()
    
    doctor_list = []
    for doc in doctors:
        profile = (await db.execute(
            select(DoctorProfileDB).where(DoctorProfileDB.user_id == doc.id)
        )).scalar_one_or_none()
        
        doctor_list.append({
            "id": doc.id,
            "email": doc.email,
            "name": doc.name,
            "status": doc.status,
            "is_active": doc.is_active,
            "specialization": profile.specialization if profile else None,
            "hospital": profile.hospital if profile else None,
            "experience_years": profile.experience_years if profile else None,
            "created_at": doc.created_at.isoformat(),
        })
    
    return doctor_list


@router.patch("/doctors/{user_id}/approve")
async def approve_doctor(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Approve a pending doctor registration."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.doctor:
        raise HTTPException(404, "Doctor not found")
    
    if user.status != "pending":
        raise HTTPException(400, f"Doctor is already {user.status}")
    
    user.status = "approved"
    user.is_active = True
    
    # Update doctor profile with approval info
    profile = (await db.execute(
        select(DoctorProfileDB).where(DoctorProfileDB.user_id == user_id)
    )).scalar_one_or_none()
    
    if profile:
        from datetime import datetime
        profile.approved_by = admin.id
        profile.approved_at = datetime.utcnow()
    
    await db.commit()
    logger.info("Admin %s approved doctor %s", admin.email, user.email)
    return {"message": "Doctor approved", "user_id": user_id}


@router.patch("/doctors/{user_id}/reject")
async def reject_doctor(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Reject a pending doctor registration."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.doctor:
        raise HTTPException(404, "Doctor not found")
    
    user.status = "rejected"
    user.is_active = False
    await db.commit()
    logger.info("Admin %s rejected doctor %s", admin.email, user.email)
    return {"message": "Doctor rejected", "user_id": user_id}


@router.patch("/doctors/{user_id}/deactivate")
async def deactivate_doctor(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Deactivate a doctor account."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.doctor:
        raise HTTPException(404, "Doctor not found")
    
    user.is_active = False
    await db.commit()
    logger.info("Admin %s deactivated doctor %s", admin.email, user.email)
    return {"message": "Doctor deactivated", "user_id": user_id}


@router.patch("/doctors/{user_id}/activate")
async def activate_doctor(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Activate a doctor account."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.doctor:
        raise HTTPException(404, "Doctor not found")
    
    if user.status != "approved":
        raise HTTPException(400, "Doctor must be approved before activation")
    
    user.is_active = True
    await db.commit()
    logger.info("Admin %s activated doctor %s", admin.email, user.email)
    return {"message": "Doctor activated", "user_id": user_id}


@router.delete("/doctors/{user_id}")
async def delete_doctor(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin: UserDB = Depends(require_admin)
):
    """Delete a doctor account and profile."""
    user = (await db.execute(select(UserDB).where(UserDB.id == user_id))).scalar_one_or_none()
    if not user or user.role != UserRole.doctor:
        raise HTTPException(404, "Doctor not found")
    
    await db.delete(user)  # CASCADE will delete doctor_profile
    await db.commit()
    logger.info("Admin %s deleted doctor %s", admin.email, user.email)
    return {"message": "Doctor deleted", "user_id": user_id}

"""Patient repository for Healthcare Agent 2.0 Backend ML System.

This module provides CRUD operations and query methods for patient records
with support for filtering, pagination, and aggregation.

**Validates: Requirements 2.4, 2.5, 13.1, 13.2, 13.3, 13.6**
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, desc, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import PatientRecordDB
from app.models.schemas import PatientRecord, PatientSummary

# Configure logger
logger = logging.getLogger(__name__)


class PatientRepository:
    """
    Repository for patient record database operations.
    
    Provides CRUD operations, filtering, pagination, and aggregation
    for patient monitoring data.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.session = session
    
    async def create_patient_record(
        self,
        patient_record: PatientRecord
    ) -> PatientRecordDB:
        """
        Create a new patient record in the database.
        
        Args:
            patient_record: Pydantic PatientRecord model with all patient data
            
        Returns:
            Created PatientRecordDB ORM instance
            
        Raises:
            SQLAlchemyError: If database operation fails
            
        **Validates: Requirement 2.4**
        """
        try:
            # Convert Pydantic model to ORM model
            db_record = PatientRecordDB(
                patient_id=patient_record.patient_id,
                day=patient_record.day or 1,
                patient_name=patient_record.patient_name,
                age=patient_record.age,
                gender=patient_record.gender,
                bmi=patient_record.bmi,
                smoking_status=patient_record.smoking_status,
                alcohol_consumption=patient_record.alcohol_consumption,
                disease_type=patient_record.disease_type,
                heart_rate=patient_record.heart_rate,
                systolic_bp=patient_record.systolic_bp,
                diastolic_bp=patient_record.diastolic_bp,
                spo2=patient_record.spo2,
                respiratory_rate=patient_record.respiratory_rate,
                body_temperature=patient_record.body_temperature,
                expected_steps=patient_record.expected_steps,
                expected_sleep_hours=patient_record.expected_sleep_hours,
                water_intake_goal=patient_record.water_intake_goal,
                actual_steps=patient_record.actual_steps,
                actual_sleep_hours=patient_record.actual_sleep_hours,
                water_intake=patient_record.water_intake,
                medication_taken=patient_record.medication_taken,
                exercise_completed=patient_record.exercise_completed,
                diet_compliance=patient_record.diet_compliance,
                compliance_score=patient_record.compliance_score,
                ideal_health_score=patient_record.ideal_health_score,
                real_health_score=patient_record.real_health_score,
                deviation_score=patient_record.deviation_score,
                recovery_score=patient_record.recovery_score,
                readmission_probability=patient_record.readmission_probability,
                risk_level=patient_record.risk_level,
                health_trend=patient_record.health_trend,
                recovery_status=patient_record.recovery_status,
                doctor_recommendation=patient_record.doctor_recommendation,
            )
            
            # Add to session and flush to get generated values
            self.session.add(db_record)
            await self.session.flush()
            await self.session.refresh(db_record)
            
            logger.info(
                f"Created patient record: patient_id={patient_record.patient_id}, "
                f"day={db_record.day}"
            )
            
            return db_record
            
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to create patient record for {patient_record.patient_id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_patient_by_id(
        self,
        patient_id: str,
        day: Optional[int] = None
    ) -> Optional[PatientRecordDB]:
        """
        Retrieve a patient record by patient_id and optional day.
        
        Args:
            patient_id: Unique patient identifier
            day: Optional day number (if None, returns latest day)
            
        Returns:
            PatientRecordDB instance or None if not found
            
        **Validates: Requirement 2.4**
        """
        try:
            if day is not None:
                # Get specific day record
                query = select(PatientRecordDB).where(
                    and_(
                        PatientRecordDB.patient_id == patient_id,
                        PatientRecordDB.day == day
                    )
                )
                result = await self.session.execute(query)
                record = result.scalar_one_or_none()
                
                if record:
                    logger.debug(f"Retrieved patient {patient_id} for day {day}")
                else:
                    logger.debug(f"No record found for patient {patient_id} on day {day}")
                
                return record
            else:
                # Get latest day record
                query = (
                    select(PatientRecordDB)
                    .where(PatientRecordDB.patient_id == patient_id)
                    .order_by(desc(PatientRecordDB.day))
                    .limit(1)
                )
                result = await self.session.execute(query)
                record = result.scalar_one_or_none()
                
                if record:
                    logger.debug(f"Retrieved latest record for patient {patient_id}")
                else:
                    logger.debug(f"No record found for patient {patient_id}")
                
                return record
                
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to retrieve patient {patient_id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_patients_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        disease_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        patient_id: Optional[str] = None
    ) -> tuple[list[PatientRecordDB], int]:
        """
        Retrieve paginated list of patient records with optional filtering.
        
        Returns only the latest day record for each patient, sorted by
        risk level priority and readmission probability.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page
            disease_type: Optional filter by disease type
            risk_level: Optional filter by risk level
            patient_id: Optional filter by patient ID (case-insensitive substring)
            
        Returns:
            Tuple of (list of patient records, total count)
            
        **Validates: Requirements 2.5, 13.1, 13.2, 13.3, 13.6**
        """
        try:
            # Build base query for latest records per patient using window function
            # This is a subquery that gets the max day for each patient
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            # Main query joining with the subquery to get only latest records
            query = (
                select(PatientRecordDB)
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
            )
            
            # Apply filters if provided
            if disease_type:
                query = query.where(PatientRecordDB.disease_type == disease_type)
            
            if risk_level:
                query = query.where(PatientRecordDB.risk_level == risk_level)

            if patient_id:
                query = query.where(PatientRecordDB.patient_id.ilike(f"%{patient_id}%"))
            
            # Count total records before pagination
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0
            
            # Apply sorting by risk level priority and readmission probability
            # Risk_Level priority: Critical → High → Medium → Low
            risk_priority = case(
                (PatientRecordDB.risk_level == "Critical", 1),
                (PatientRecordDB.risk_level == "High", 2),
                (PatientRecordDB.risk_level == "Medium", 3),
                (PatientRecordDB.risk_level == "Low", 4),
                else_=5
            )
            
            query = query.order_by(
                risk_priority,
                desc(PatientRecordDB.readmission_probability)
            )
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.session.execute(query)
            records = result.scalars().all()
            
            logger.info(
                f"Retrieved {len(records)} patient records (page={page}, "
                f"page_size={page_size}, total={total}, "
                f"disease_type={disease_type}, risk_level={risk_level})"
            )
            
            return list(records), total
            
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to retrieve paginated patients: {e}",
                exc_info=True
            )
            raise
    
    async def get_patient_summary(
        self,
        patient_id: str,
        days: int = 30
    ) -> list[PatientRecordDB]:
        """
        Retrieve daily trend data for a specific patient over a time window.
        
        Returns records ordered by day in ascending order for the last N days.
        
        Args:
            patient_id: Unique patient identifier
            days: Number of days to retrieve (default: 30)
            
        Returns:
            List of PatientRecordDB instances ordered by day (ascending)
            
        **Validates: Requirement 2.5**
        """
        try:
            # Build query for patient's records in the last N days
            query = (
                select(PatientRecordDB)
                .where(PatientRecordDB.patient_id == patient_id)
                .order_by(PatientRecordDB.day)  # Ascending order
            )
            
            # Execute query
            result = await self.session.execute(query)
            all_records = result.scalars().all()
            
            # Get the last N days
            records = list(all_records)[-days:] if len(all_records) > days else list(all_records)
            
            logger.info(
                f"Retrieved {len(records)} daily records for patient {patient_id} "
                f"(requested {days} days)"
            )
            
            return records
            
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to retrieve patient summary for {patient_id}: {e}",
                exc_info=True
            )
            raise
    
    async def update_patient_record(
        self,
        patient_id: str,
        day: int,
        update_data: dict
    ) -> Optional[PatientRecordDB]:
        """
        Update an existing patient record.
        
        Args:
            patient_id: Unique patient identifier
            day: Day number to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated PatientRecordDB instance or None if not found
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get existing record
            record = await self.get_patient_by_id(patient_id, day)
            
            if not record:
                logger.warning(
                    f"Cannot update: patient {patient_id} day {day} not found"
                )
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            # Flush changes
            await self.session.flush()
            await self.session.refresh(record)
            
            logger.info(
                f"Updated patient record: patient_id={patient_id}, day={day}"
            )
            
            return record
            
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to update patient record {patient_id} day {day}: {e}",
                exc_info=True
            )
            raise
    
    async def delete_patient_record(
        self,
        patient_id: str,
        day: Optional[int] = None
    ) -> int:
        """
        Delete patient record(s).
        
        Args:
            patient_id: Unique patient identifier
            day: Optional day number (if None, deletes all records for patient)
            
        Returns:
            Number of records deleted
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            if day is not None:
                # Delete specific day record
                query = select(PatientRecordDB).where(
                    and_(
                        PatientRecordDB.patient_id == patient_id,
                        PatientRecordDB.day == day
                    )
                )
                result = await self.session.execute(query)
                record = result.scalar_one_or_none()
                
                if record:
                    await self.session.delete(record)
                    await self.session.flush()
                    logger.info(f"Deleted patient {patient_id} day {day}")
                    return 1
                else:
                    logger.warning(f"No record found to delete: {patient_id} day {day}")
                    return 0
            else:
                # Delete all records for patient
                query = select(PatientRecordDB).where(
                    PatientRecordDB.patient_id == patient_id
                )
                result = await self.session.execute(query)
                records = result.scalars().all()
                
                count = len(records)
                for record in records:
                    await self.session.delete(record)
                
                await self.session.flush()
                logger.info(f"Deleted {count} records for patient {patient_id}")
                return count
                
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to delete patient record(s) {patient_id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_patient_count(
        self,
        disease_type: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> int:
        """
        Get count of unique patients with optional filtering.
        
        Args:
            disease_type: Optional filter by disease type
            risk_level: Optional filter by risk level
            
        Returns:
            Count of unique patients
        """
        try:
            # Count unique patient_ids with filters applied to latest records
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            query = (
                select(func.count(func.distinct(PatientRecordDB.patient_id)))
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
            )
            
            if disease_type:
                query = query.where(PatientRecordDB.disease_type == disease_type)
            
            if risk_level:
                query = query.where(PatientRecordDB.risk_level == risk_level)
            
            result = await self.session.execute(query)
            count = result.scalar() or 0
            
            logger.debug(
                f"Patient count: {count} "
                f"(disease_type={disease_type}, risk_level={risk_level})"
            )
            
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to count patients: {e}", exc_info=True)
            raise
    
    async def get_all_patient_ids(self) -> list[str]:
        """
        Get list of all unique patient IDs.
        
        Returns:
            List of unique patient_id strings
        """
        try:
            query = select(func.distinct(PatientRecordDB.patient_id))
            result = await self.session.execute(query)
            patient_ids = [row[0] for row in result.all()]
            
            logger.debug(f"Retrieved {len(patient_ids)} unique patient IDs")
            
            return patient_ids
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve patient IDs: {e}", exc_info=True)
            raise

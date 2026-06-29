"""Statistics repository for Healthcare Agent 2.0 Backend ML System.

This module provides aggregation queries for dashboard statistics including
patient counts, risk distributions, recovery distributions, and average metrics.

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
"""

import logging
from typing import Dict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import PatientRecordDB

# Configure logger
logger = logging.getLogger(__name__)


class StatisticsRepository:
    """
    Repository for dashboard statistics aggregation queries.
    
    Provides methods to compute KPIs and distributions for the dashboard
    including patient counts, risk levels, recovery status, and averages.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.session = session
    
    async def compute_dashboard_stats(self) -> Dict:
        """
        Compute all dashboard statistics in a single operation.
        
        Aggregates:
        - total_patients: Unique patient count with data in last 30 days
        - high_risk_count: Count of High + Critical risk patients
        - avg_compliance: Mean compliance score across all active patients
        - avg_readmission_probability: Mean readmission probability
        - risk_distribution: Count by risk level (Low, Medium, High, Critical)
        - recovery_distribution: Count by recovery status
        
        Returns:
            Dictionary with all dashboard statistics
            
        **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
        """
        try:
            # Get latest day record for each patient (active patients)
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            # Query for latest records only
            latest_records_query = (
                select(PatientRecordDB)
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
            )
            
            result = await self.session.execute(latest_records_query)
            latest_records = result.scalars().all()
            
            # Compute total_patients (Requirement 12.1)
            total_patients = len(latest_records)
            
            # Initialize distributions
            risk_distribution = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }
            
            recovery_distribution = {
                "recovered": 0,
                "improving": 0,
                "stable": 0,
                "delayed_recovery": 0,
                "worsening": 0,
                "critical": 0
            }
            
            # Initialize aggregates for averages
            total_compliance = 0.0
            total_readmission_prob = 0.0
            high_risk_count = 0
            
            compliance_count = 0
            readmission_count = 0
            
            # Process each record
            for record in latest_records:
                # Risk distribution (Requirement 12.2)
                if record.risk_level:
                    risk_level_lower = record.risk_level.lower()
                    if risk_level_lower in risk_distribution:
                        risk_distribution[risk_level_lower] += 1
                    
                    # High risk count (High + Critical) (Requirement 12.6)
                    if risk_level_lower in ["high", "critical"]:
                        high_risk_count += 1
                
                # Recovery distribution (Requirement 12.3)
                if record.recovery_status:
                    # Normalize recovery status to match distribution keys
                    status_lower = record.recovery_status.lower().replace(" ", "_")
                    if status_lower in recovery_distribution:
                        recovery_distribution[status_lower] += 1
                
                # Compliance score aggregation (Requirement 12.4)
                if record.compliance_score is not None:
                    total_compliance += float(record.compliance_score)
                    compliance_count += 1
                
                # Readmission probability aggregation (Requirement 12.5)
                if record.readmission_probability is not None:
                    total_readmission_prob += float(record.readmission_probability)
                    readmission_count += 1
            
            # Calculate averages
            avg_compliance = (
                total_compliance / compliance_count if compliance_count > 0 else 0.0
            )
            avg_readmission_probability = (
                total_readmission_prob / readmission_count if readmission_count > 0 else 0.0
            )
            
            # Build result dictionary
            stats = {
                "total_patients": total_patients,
                "high_risk_count": high_risk_count,
                "avg_compliance": round(avg_compliance, 2),
                "avg_readmission_probability": round(avg_readmission_probability, 4),
                "risk_distribution": risk_distribution,
                "recovery_distribution": recovery_distribution
            }
            
            logger.info(
                f"Computed dashboard stats: total_patients={total_patients}, "
                f"high_risk_count={high_risk_count}, "
                f"avg_compliance={avg_compliance:.2f}, "
                f"avg_readmission_probability={avg_readmission_probability:.4f}"
            )
            
            return stats
            
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to compute dashboard statistics: {e}",
                exc_info=True
            )
            raise
    
    async def get_unique_patient_count(self) -> int:
        """
        Get count of unique patients with data in the system.
        
        Returns:
            Count of unique patient IDs
            
        **Validates: Requirement 12.1**
        """
        try:
            query = select(func.count(func.distinct(PatientRecordDB.patient_id)))
            result = await self.session.execute(query)
            count = result.scalar() or 0
            
            logger.debug(f"Unique patient count: {count}")
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to count unique patients: {e}", exc_info=True)
            raise
    
    async def get_risk_distribution(self) -> Dict[str, int]:
        """
        Get distribution of patients by risk level (latest records only).
        
        Returns:
            Dictionary with counts for each risk level:
            {"low": int, "medium": int, "high": int, "critical": int}
            
        **Validates: Requirement 12.2**
        """
        try:
            # Get latest records per patient
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            # Count by risk level
            query = (
                select(
                    PatientRecordDB.risk_level,
                    func.count(PatientRecordDB.patient_id).label('count')
                )
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
                .group_by(PatientRecordDB.risk_level)
            )
            
            result = await self.session.execute(query)
            rows = result.all()
            
            # Initialize distribution with zeros
            distribution = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }
            
            # Populate from query results
            for risk_level, count in rows:
                if risk_level:
                    risk_level_lower = risk_level.lower()
                    if risk_level_lower in distribution:
                        distribution[risk_level_lower] = count
            
            logger.debug(f"Risk distribution: {distribution}")
            return distribution
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get risk distribution: {e}", exc_info=True)
            raise
    
    async def get_recovery_distribution(self) -> Dict[str, int]:
        """
        Get distribution of patients by recovery status (latest records only).
        
        Returns:
            Dictionary with counts for each recovery status:
            {"recovered": int, "improving": int, "stable": int,
             "delayed_recovery": int, "worsening": int, "critical": int}
            
        **Validates: Requirement 12.3**
        """
        try:
            # Get latest records per patient
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            # Count by recovery status
            query = (
                select(
                    PatientRecordDB.recovery_status,
                    func.count(PatientRecordDB.patient_id).label('count')
                )
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
                .group_by(PatientRecordDB.recovery_status)
            )
            
            result = await self.session.execute(query)
            rows = result.all()
            
            # Initialize distribution with zeros
            distribution = {
                "recovered": 0,
                "improving": 0,
                "stable": 0,
                "delayed_recovery": 0,
                "worsening": 0,
                "critical": 0
            }
            
            # Populate from query results
            for recovery_status, count in rows:
                if recovery_status:
                    # Normalize status to match expected keys
                    status_lower = recovery_status.lower().replace(" ", "_")
                    if status_lower in distribution:
                        distribution[status_lower] = count
            
            logger.debug(f"Recovery distribution: {distribution}")
            return distribution
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get recovery distribution: {e}", exc_info=True)
            raise
    
    async def get_average_compliance(self) -> float:
        """
        Calculate average compliance score across all active patients.
        
        Uses only the latest record for each patient.
        
        Returns:
            Average compliance score (0-100)
            
        **Validates: Requirement 12.4**
        """
        try:
            # Get latest records per patient
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            # Calculate average compliance score
            query = (
                select(func.avg(PatientRecordDB.compliance_score))
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
                .where(PatientRecordDB.compliance_score.isnot(None))
            )
            
            result = await self.session.execute(query)
            avg = result.scalar()
            
            # Return 0.0 if no records or None
            avg_compliance = float(avg) if avg is not None else 0.0
            
            logger.debug(f"Average compliance: {avg_compliance:.2f}")
            return round(avg_compliance, 2)
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to calculate average compliance: {e}", exc_info=True)
            raise
    
    async def get_average_readmission_probability(self) -> float:
        """
        Calculate average readmission probability across all active patients.
        
        Uses only the latest record for each patient.
        
        Returns:
            Average readmission probability (0-1)
            
        **Validates: Requirement 12.5**
        """
        try:
            # Get latest records per patient
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            # Calculate average readmission probability
            query = (
                select(func.avg(PatientRecordDB.readmission_probability))
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
                .where(PatientRecordDB.readmission_probability.isnot(None))
            )
            
            result = await self.session.execute(query)
            avg = result.scalar()
            
            # Return 0.0 if no records or None
            avg_prob = float(avg) if avg is not None else 0.0
            
            logger.debug(f"Average readmission probability: {avg_prob:.4f}")
            return round(avg_prob, 4)
            
        except SQLAlchemyError as e:
            logger.error(
                f"Failed to calculate average readmission probability: {e}",
                exc_info=True
            )
            raise
    
    async def get_high_risk_count(self) -> int:
        """
        Get count of patients with High or Critical risk level.
        
        Uses only the latest record for each patient.
        
        Returns:
            Count of high-risk patients (High + Critical)
            
        **Validates: Requirement 12.6**
        """
        try:
            # Get latest records per patient
            latest_day_subquery = (
                select(
                    PatientRecordDB.patient_id,
                    func.max(PatientRecordDB.day).label('max_day')
                )
                .group_by(PatientRecordDB.patient_id)
                .subquery()
            )
            
            # Count High and Critical patients
            query = (
                select(func.count(PatientRecordDB.patient_id))
                .join(
                    latest_day_subquery,
                    and_(
                        PatientRecordDB.patient_id == latest_day_subquery.c.patient_id,
                        PatientRecordDB.day == latest_day_subquery.c.max_day
                    )
                )
                .where(
                    PatientRecordDB.risk_level.in_(["High", "Critical"])
                )
            )
            
            result = await self.session.execute(query)
            count = result.scalar() or 0
            
            logger.debug(f"High risk count (High + Critical): {count}")
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get high risk count: {e}", exc_info=True)
            raise

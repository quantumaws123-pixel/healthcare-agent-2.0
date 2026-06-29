"""
Unit tests for PatientRepository CRUD operations.

Tests Requirements 2.4, 2.5, 13.1, 13.2, 13.3, 13.6
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.patient_repository import PatientRepository
from app.database.models import PatientRecordDB
from app.models.schemas import PatientRecord


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_patient_record():
    """Create a sample patient record for testing."""
    return PatientRecord(
        patient_id="P001",
        patient_name="John Doe",
        age=65,
        gender="Male",
        bmi=28.5,
        smoking_status="Former",
        alcohol_consumption="Moderate",
        disease_type="Heart Failure",
        heart_rate=78,
        systolic_bp=130,
        diastolic_bp=85,
        spo2=96.5,
        respiratory_rate=16,
        body_temperature=36.8,
        expected_steps=5000,
        expected_sleep_hours=8.0,
        water_intake_goal=2000,
        actual_steps=4200,
        actual_sleep_hours=7.5,
        water_intake=1800,
        medication_taken="Yes",
        exercise_completed="Yes",
        diet_compliance=85.0,
        compliance_score=78.5,
        ideal_health_score=85.0,
        real_health_score=72.3,
        deviation_score=15.2,
        recovery_score=68.0,
        readmission_probability=0.42,
        risk_level="Medium",
        health_trend="Increasing",
        recovery_status="Improving",
        doctor_recommendation="Increase Monitoring",
        day=1
    )


@pytest.fixture
def sample_db_record():
    """Create a sample database record for testing."""
    return PatientRecordDB(
        patient_id="P001",
        day=1,
        patient_name="John Doe",
        age=65,
        gender="Male",
        bmi=28.5,
        smoking_status="Former",
        alcohol_consumption="Moderate",
        disease_type="Heart Failure",
        heart_rate=78,
        systolic_bp=130,
        diastolic_bp=85,
        spo2=96.5,
        respiratory_rate=16,
        body_temperature=36.8,
        expected_steps=5000,
        expected_sleep_hours=8.0,
        water_intake_goal=2000,
        actual_steps=4200,
        actual_sleep_hours=7.5,
        water_intake=1800,
        medication_taken="Yes",
        exercise_completed="Yes",
        diet_compliance=85.0,
        compliance_score=78.5,
        ideal_health_score=85.0,
        real_health_score=72.3,
        deviation_score=15.2,
        recovery_score=68.0,
        readmission_probability=0.42,
        risk_level="Medium",
        health_trend="Increasing",
        recovery_status="Improving",
        doctor_recommendation="Increase Monitoring",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestPatientRepositoryCreate:
    """Test suite for create_patient_record method."""
    
    @pytest.mark.asyncio
    async def test_create_patient_record_success(self, mock_session, sample_patient_record):
        """Test successful patient record creation (Requirement 2.4)."""
        repository = PatientRepository(mock_session)
        
        # Execute
        result = await repository.create_patient_record(sample_patient_record)
        
        # Verify
        assert mock_session.add.called
        assert mock_session.flush.called
        assert mock_session.refresh.called
        assert result.patient_id == "P001"
        assert result.day == 1
    
    @pytest.mark.asyncio
    async def test_create_patient_record_with_default_day(self, mock_session):
        """Test patient record creation with default day value."""
        patient_record = PatientRecord(
            patient_id="P002",
            patient_name="Jane Smith",
            age=45,
            gender="Female",
            bmi=24.0,
            smoking_status="Never",
            alcohol_consumption="None",
            disease_type="Diabetes",
            heart_rate=72,
            systolic_bp=120,
            diastolic_bp=80,
            spo2=98.0,
            respiratory_rate=14,
            body_temperature=36.6,
            expected_steps=6000,
            expected_sleep_hours=8.0,
            water_intake_goal=2500,
            actual_steps=5800,
            actual_sleep_hours=7.8,
            water_intake=2400,
            medication_taken="Yes",
            exercise_completed="Yes",
            diet_compliance=92.0,
            day=None  # No day specified
        )
        
        repository = PatientRepository(mock_session)
        result = await repository.create_patient_record(patient_record)
        
        # Verify default day is set to 1
        assert result.day == 1
    
    @pytest.mark.asyncio
    async def test_create_patient_record_database_error(self, mock_session, sample_patient_record):
        """Test error handling when database operation fails."""
        mock_session.flush.side_effect = SQLAlchemyError("Database error")
        
        repository = PatientRepository(mock_session)
        
        with pytest.raises(SQLAlchemyError):
            await repository.create_patient_record(sample_patient_record)


class TestPatientRepositoryGetById:
    """Test suite for get_patient_by_id method."""
    
    @pytest.mark.asyncio
    async def test_get_patient_by_id_with_day(self, mock_session, sample_db_record):
        """Test retrieving patient record by ID and day (Requirement 2.4)."""
        # Mock the execute result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_record
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        result = await repository.get_patient_by_id("P001", day=1)
        
        assert result is not None
        assert result.patient_id == "P001"
        assert result.day == 1
    
    @pytest.mark.asyncio
    async def test_get_patient_by_id_latest_day(self, mock_session, sample_db_record):
        """Test retrieving latest patient record without specifying day."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_record
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        result = await repository.get_patient_by_id("P001", day=None)
        
        assert result is not None
        assert result.patient_id == "P001"
    
    @pytest.mark.asyncio
    async def test_get_patient_by_id_not_found(self, mock_session):
        """Test handling when patient record is not found."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        result = await repository.get_patient_by_id("P999", day=1)
        
        assert result is None


class TestPatientRepositoryGetPaginated:
    """Test suite for get_patients_paginated method."""
    
    @pytest.mark.asyncio
    async def test_get_patients_paginated_no_filters(self, mock_session):
        """Test paginated retrieval without filters (Requirements 2.5, 13.3)."""
        mock_records = [
            PatientRecordDB(
                patient_id=f"P{i:03d}",
                day=1,
                patient_name=f"Patient {i}",
                age=50 + i,
                risk_level="Medium",
                readmission_probability=0.5
            )
            for i in range(1, 11)
        ]
        
        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 10
        
        # Mock data query
        mock_data_result = AsyncMock()
        mock_data_result.scalars.return_value.all.return_value = mock_records
        
        mock_session.execute.side_effect = [mock_count_result, mock_data_result]
        
        repository = PatientRepository(mock_session)
        records, total = await repository.get_patients_paginated(page=1, page_size=10)
        
        assert len(records) == 10
        assert total == 10
    
    @pytest.mark.asyncio
    async def test_get_patients_paginated_with_disease_filter(self, mock_session):
        """Test paginated retrieval with disease_type filter (Requirement 13.1)."""
        mock_records = [
            PatientRecordDB(
                patient_id="P001",
                day=1,
                disease_type="Heart Failure",
                risk_level="High",
                readmission_probability=0.7
            )
        ]
        
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 1
        
        mock_data_result = AsyncMock()
        mock_data_result.scalars.return_value.all.return_value = mock_records
        
        mock_session.execute.side_effect = [mock_count_result, mock_data_result]
        
        repository = PatientRepository(mock_session)
        records, total = await repository.get_patients_paginated(
            page=1,
            page_size=10,
            disease_type="Heart Failure"
        )
        
        assert len(records) == 1
        assert total == 1
        assert records[0].disease_type == "Heart Failure"
    
    @pytest.mark.asyncio
    async def test_get_patients_paginated_with_risk_filter(self, mock_session):
        """Test paginated retrieval with risk_level filter (Requirement 13.2)."""
        mock_records = [
            PatientRecordDB(
                patient_id="P001",
                day=1,
                risk_level="Critical",
                readmission_probability=0.9
            )
        ]
        
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 1
        
        mock_data_result = AsyncMock()
        mock_data_result.scalars.return_value.all.return_value = mock_records
        
        mock_session.execute.side_effect = [mock_count_result, mock_data_result]
        
        repository = PatientRepository(mock_session)
        records, total = await repository.get_patients_paginated(
            page=1,
            page_size=10,
            risk_level="Critical"
        )
        
        assert len(records) == 1
        assert total == 1
        assert records[0].risk_level == "Critical"
    
    @pytest.mark.asyncio
    async def test_get_patients_paginated_pagination_offset(self, mock_session):
        """Test pagination with page offset (Requirement 13.3)."""
        mock_records = [
            PatientRecordDB(
                patient_id=f"P{i:03d}",
                day=1,
                risk_level="Medium",
                readmission_probability=0.5
            )
            for i in range(11, 21)  # Records 11-20 (page 2)
        ]
        
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 50
        
        mock_data_result = AsyncMock()
        mock_data_result.scalars.return_value.all.return_value = mock_records
        
        mock_session.execute.side_effect = [mock_count_result, mock_data_result]
        
        repository = PatientRepository(mock_session)
        records, total = await repository.get_patients_paginated(page=2, page_size=10)
        
        assert len(records) == 10
        assert total == 50


class TestPatientRepositoryGetSummary:
    """Test suite for get_patient_summary method."""
    
    @pytest.mark.asyncio
    async def test_get_patient_summary_30_days(self, mock_session):
        """Test retrieving 30-day patient summary (Requirement 2.5)."""
        mock_records = [
            PatientRecordDB(
                patient_id="P001",
                day=i,
                compliance_score=70.0 + i,
                recovery_score=60.0 + i
            )
            for i in range(1, 31)
        ]
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        records = await repository.get_patient_summary("P001", days=30)
        
        assert len(records) == 30
        assert records[0].day == 1
        assert records[-1].day == 30
    
    @pytest.mark.asyncio
    async def test_get_patient_summary_fewer_than_requested_days(self, mock_session):
        """Test retrieving summary when fewer days available than requested."""
        mock_records = [
            PatientRecordDB(
                patient_id="P001",
                day=i,
                compliance_score=70.0
            )
            for i in range(1, 11)  # Only 10 days available
        ]
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        records = await repository.get_patient_summary("P001", days=30)
        
        assert len(records) == 10  # Returns all available records


class TestPatientRepositoryUpdate:
    """Test suite for update_patient_record method."""
    
    @pytest.mark.asyncio
    async def test_update_patient_record_success(self, mock_session, sample_db_record):
        """Test successful patient record update."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_record
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        
        update_data = {
            "compliance_score": 85.0,
            "risk_level": "Low"
        }
        
        result = await repository.update_patient_record("P001", 1, update_data)
        
        assert result is not None
        assert result.compliance_score == 85.0
        assert result.risk_level == "Low"
    
    @pytest.mark.asyncio
    async def test_update_patient_record_not_found(self, mock_session):
        """Test update when patient record doesn't exist."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        result = await repository.update_patient_record("P999", 1, {"risk_level": "Low"})
        
        assert result is None


class TestPatientRepositoryDelete:
    """Test suite for delete_patient_record method."""
    
    @pytest.mark.asyncio
    async def test_delete_patient_record_specific_day(self, mock_session, sample_db_record):
        """Test deleting specific day record."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_record
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        count = await repository.delete_patient_record("P001", day=1)
        
        assert count == 1
        assert mock_session.delete.called
    
    @pytest.mark.asyncio
    async def test_delete_patient_record_all_days(self, mock_session):
        """Test deleting all records for a patient."""
        mock_records = [
            PatientRecordDB(patient_id="P001", day=i)
            for i in range(1, 6)
        ]
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        count = await repository.delete_patient_record("P001", day=None)
        
        assert count == 5
        assert mock_session.delete.call_count == 5


class TestPatientRepositoryCount:
    """Test suite for get_patient_count method."""
    
    @pytest.mark.asyncio
    async def test_get_patient_count_no_filters(self, mock_session):
        """Test counting all patients."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 100
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        count = await repository.get_patient_count()
        
        assert count == 100
    
    @pytest.mark.asyncio
    async def test_get_patient_count_with_filters(self, mock_session):
        """Test counting patients with filters."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 15
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        count = await repository.get_patient_count(
            disease_type="Heart Failure",
            risk_level="High"
        )
        
        assert count == 15


class TestPatientRepositoryGetAllIds:
    """Test suite for get_all_patient_ids method."""
    
    @pytest.mark.asyncio
    async def test_get_all_patient_ids(self, mock_session):
        """Test retrieving all unique patient IDs."""
        mock_result = AsyncMock()
        mock_result.all.return_value = [
            ("P001",),
            ("P002",),
            ("P003",)
        ]
        mock_session.execute.return_value = mock_result
        
        repository = PatientRepository(mock_session)
        patient_ids = await repository.get_all_patient_ids()
        
        assert len(patient_ids) == 3
        assert "P001" in patient_ids
        assert "P002" in patient_ids
        assert "P003" in patient_ids

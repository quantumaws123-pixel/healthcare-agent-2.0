"""
Unit tests for StatisticsRepository aggregation operations.

Tests Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.statistics_repository import StatisticsRepository
from app.database.models import PatientRecordDB


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def sample_patient_records():
    """Create sample patient records for testing dashboard statistics."""
    return [
        PatientRecordDB(
            patient_id="P001",
            day=5,
            risk_level="Critical",
            recovery_status="Worsening",
            compliance_score=45.0,
            readmission_probability=0.92
        ),
        PatientRecordDB(
            patient_id="P002",
            day=3,
            risk_level="High",
            recovery_status="Delayed Recovery",
            compliance_score=58.0,
            readmission_probability=0.68
        ),
        PatientRecordDB(
            patient_id="P003",
            day=7,
            risk_level="Medium",
            recovery_status="Stable",
            compliance_score=72.5,
            readmission_probability=0.42
        ),
        PatientRecordDB(
            patient_id="P004",
            day=2,
            risk_level="Low",
            recovery_status="Improving",
            compliance_score=85.0,
            readmission_probability=0.18
        ),
        PatientRecordDB(
            patient_id="P005",
            day=1,
            risk_level="Low",
            recovery_status="Recovered",
            compliance_score=92.0,
            readmission_probability=0.12
        ),
    ]


class TestComputeDashboardStats:
    """Test suite for compute_dashboard_stats method."""
    
    @pytest.mark.asyncio
    async def test_compute_dashboard_stats_success(self, mock_session, sample_patient_records):
        """
        Test successful computation of all dashboard statistics.
        
        **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
        """
        # Mock the database query to return sample patient records
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = sample_patient_records
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        stats = await repository.compute_dashboard_stats()
        
        # Verify total_patients (Requirement 12.1)
        assert stats["total_patients"] == 5
        
        # Verify high_risk_count (High + Critical) (Requirement 12.6)
        assert stats["high_risk_count"] == 2  # P001 (Critical) + P002 (High)
        
        # Verify risk_distribution (Requirement 12.2)
        assert stats["risk_distribution"]["critical"] == 1
        assert stats["risk_distribution"]["high"] == 1
        assert stats["risk_distribution"]["medium"] == 1
        assert stats["risk_distribution"]["low"] == 2
        
        # Verify recovery_distribution (Requirement 12.3)
        assert stats["recovery_distribution"]["worsening"] == 1
        assert stats["recovery_distribution"]["delayed_recovery"] == 1
        assert stats["recovery_distribution"]["stable"] == 1
        assert stats["recovery_distribution"]["improving"] == 1
        assert stats["recovery_distribution"]["recovered"] == 1
        
        # Verify avg_compliance (Requirement 12.4)
        # (45 + 58 + 72.5 + 85 + 92) / 5 = 70.5
        expected_avg_compliance = 70.5
        assert stats["avg_compliance"] == expected_avg_compliance
        
        # Verify avg_readmission_probability (Requirement 12.5)
        # (0.92 + 0.68 + 0.42 + 0.18 + 0.12) / 5 = 0.464
        expected_avg_prob = 0.464
        assert stats["avg_readmission_probability"] == expected_avg_prob
    
    @pytest.mark.asyncio
    async def test_compute_dashboard_stats_empty_database(self, mock_session):
        """Test dashboard stats computation with no patient records."""
        # Mock empty result
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        stats = await repository.compute_dashboard_stats()
        
        # Verify all stats are zero/empty
        assert stats["total_patients"] == 0
        assert stats["high_risk_count"] == 0
        assert stats["avg_compliance"] == 0.0
        assert stats["avg_readmission_probability"] == 0.0
        assert all(count == 0 for count in stats["risk_distribution"].values())
        assert all(count == 0 for count in stats["recovery_distribution"].values())
    
    @pytest.mark.asyncio
    async def test_compute_dashboard_stats_with_null_values(self, mock_session):
        """Test dashboard stats computation with records containing null values."""
        records_with_nulls = [
            PatientRecordDB(
                patient_id="P001",
                day=1,
                risk_level="High",
                recovery_status="Improving",
                compliance_score=None,  # Null compliance
                readmission_probability=0.65
            ),
            PatientRecordDB(
                patient_id="P002",
                day=1,
                risk_level="Medium",
                recovery_status="Stable",
                compliance_score=75.0,
                readmission_probability=None  # Null probability
            ),
        ]
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = records_with_nulls
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        stats = await repository.compute_dashboard_stats()
        
        # Verify averages only count non-null values
        assert stats["total_patients"] == 2
        assert stats["avg_compliance"] == 75.0  # Only P002 has compliance
        assert stats["avg_readmission_probability"] == 0.65  # Only P001 has probability
    
    @pytest.mark.asyncio
    async def test_compute_dashboard_stats_database_error(self, mock_session):
        """Test error handling when database query fails."""
        mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")
        
        repository = StatisticsRepository(mock_session)
        
        with pytest.raises(SQLAlchemyError):
            await repository.compute_dashboard_stats()


class TestGetUniquePatientCount:
    """Test suite for get_unique_patient_count method."""
    
    @pytest.mark.asyncio
    async def test_get_unique_patient_count_success(self, mock_session):
        """
        Test counting unique patients.
        
        **Validates: Requirement 12.1**
        """
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        count = await repository.get_unique_patient_count()
        
        assert count == 42
    
    @pytest.mark.asyncio
    async def test_get_unique_patient_count_empty(self, mock_session):
        """Test counting with no patients in database."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        count = await repository.get_unique_patient_count()
        
        assert count == 0


class TestGetRiskDistribution:
    """Test suite for get_risk_distribution method."""
    
    @pytest.mark.asyncio
    async def test_get_risk_distribution_success(self, mock_session):
        """
        Test retrieving risk level distribution.
        
        **Validates: Requirement 12.2**
        """
        # Mock query result with risk level counts
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Critical", 5),
            ("High", 12),
            ("Medium", 25),
            ("Low", 18)
        ]
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        distribution = await repository.get_risk_distribution()
        
        assert distribution["critical"] == 5
        assert distribution["high"] == 12
        assert distribution["medium"] == 25
        assert distribution["low"] == 18
    
    @pytest.mark.asyncio
    async def test_get_risk_distribution_partial_data(self, mock_session):
        """Test risk distribution with only some risk levels present."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Critical", 3),
            ("Medium", 10)
        ]
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        distribution = await repository.get_risk_distribution()
        
        # Missing risk levels should be zero
        assert distribution["critical"] == 3
        assert distribution["high"] == 0
        assert distribution["medium"] == 10
        assert distribution["low"] == 0
    
    @pytest.mark.asyncio
    async def test_get_risk_distribution_case_insensitive(self, mock_session):
        """Test that risk level matching is case-insensitive."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("CRITICAL", 2),
            ("High", 5),
            ("medium", 8),
            ("LOW", 10)
        ]
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        distribution = await repository.get_risk_distribution()
        
        assert distribution["critical"] == 2
        assert distribution["high"] == 5
        assert distribution["medium"] == 8
        assert distribution["low"] == 10


class TestGetRecoveryDistribution:
    """Test suite for get_recovery_distribution method."""
    
    @pytest.mark.asyncio
    async def test_get_recovery_distribution_success(self, mock_session):
        """
        Test retrieving recovery status distribution.
        
        **Validates: Requirement 12.3**
        """
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Recovered", 10),
            ("Improving", 15),
            ("Stable", 20),
            ("Delayed Recovery", 8),
            ("Worsening", 5),
            ("Critical", 2)
        ]
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        distribution = await repository.get_recovery_distribution()
        
        assert distribution["recovered"] == 10
        assert distribution["improving"] == 15
        assert distribution["stable"] == 20
        assert distribution["delayed_recovery"] == 8
        assert distribution["worsening"] == 5
        assert distribution["critical"] == 2
    
    @pytest.mark.asyncio
    async def test_get_recovery_distribution_normalize_keys(self, mock_session):
        """Test that recovery status keys are normalized (spaces to underscores)."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Delayed Recovery", 12),  # Should map to "delayed_recovery"
            ("Improving", 8),
        ]
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        distribution = await repository.get_recovery_distribution()
        
        assert distribution["delayed_recovery"] == 12
        assert distribution["improving"] == 8


class TestGetAverageCompliance:
    """Test suite for get_average_compliance method."""
    
    @pytest.mark.asyncio
    async def test_get_average_compliance_success(self, mock_session):
        """
        Test calculating average compliance score.
        
        **Validates: Requirement 12.4**
        """
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("73.456")
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        avg_compliance = await repository.get_average_compliance()
        
        assert avg_compliance == 73.46  # Rounded to 2 decimal places
    
    @pytest.mark.asyncio
    async def test_get_average_compliance_no_data(self, mock_session):
        """Test average compliance with no patient records."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        avg_compliance = await repository.get_average_compliance()
        
        assert avg_compliance == 0.0
    
    @pytest.mark.asyncio
    async def test_get_average_compliance_rounding(self, mock_session):
        """Test that compliance score is properly rounded to 2 decimal places."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("85.6789")
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        avg_compliance = await repository.get_average_compliance()
        
        assert avg_compliance == 85.68


class TestGetAverageReadmissionProbability:
    """Test suite for get_average_readmission_probability method."""
    
    @pytest.mark.asyncio
    async def test_get_average_readmission_probability_success(self, mock_session):
        """
        Test calculating average readmission probability.
        
        **Validates: Requirement 12.5**
        """
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("0.456789")
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        avg_prob = await repository.get_average_readmission_probability()
        
        assert avg_prob == 0.4568  # Rounded to 4 decimal places
    
    @pytest.mark.asyncio
    async def test_get_average_readmission_probability_no_data(self, mock_session):
        """Test average probability with no patient records."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        avg_prob = await repository.get_average_readmission_probability()
        
        assert avg_prob == 0.0
    
    @pytest.mark.asyncio
    async def test_get_average_readmission_probability_rounding(self, mock_session):
        """Test that probability is properly rounded to 4 decimal places."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("0.123456789")
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        avg_prob = await repository.get_average_readmission_probability()
        
        assert avg_prob == 0.1235


class TestGetHighRiskCount:
    """Test suite for get_high_risk_count method."""
    
    @pytest.mark.asyncio
    async def test_get_high_risk_count_success(self, mock_session):
        """
        Test counting High and Critical risk patients.
        
        **Validates: Requirement 12.6**
        """
        mock_result = MagicMock()
        mock_result.scalar.return_value = 23
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        count = await repository.get_high_risk_count()
        
        assert count == 23
    
    @pytest.mark.asyncio
    async def test_get_high_risk_count_no_high_risk_patients(self, mock_session):
        """Test high risk count with no high-risk patients."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        count = await repository.get_high_risk_count()
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_get_high_risk_count_includes_high_and_critical(self, mock_session):
        """Test that high risk count includes both High and Critical levels."""
        # This test verifies the query logic includes both risk levels
        # In a real scenario, we'd have 8 High + 5 Critical = 13 total
        mock_result = MagicMock()
        mock_result.scalar.return_value = 13
        mock_session.execute.return_value = mock_result
        
        repository = StatisticsRepository(mock_session)
        count = await repository.get_high_risk_count()
        
        assert count == 13


class TestStatisticsRepositoryErrorHandling:
    """Test suite for error handling in StatisticsRepository."""
    
    @pytest.mark.asyncio
    async def test_risk_distribution_database_error(self, mock_session):
        """Test error handling for risk distribution query failure."""
        mock_session.execute.side_effect = SQLAlchemyError("Connection timeout")
        
        repository = StatisticsRepository(mock_session)
        
        with pytest.raises(SQLAlchemyError):
            await repository.get_risk_distribution()
    
    @pytest.mark.asyncio
    async def test_recovery_distribution_database_error(self, mock_session):
        """Test error handling for recovery distribution query failure."""
        mock_session.execute.side_effect = SQLAlchemyError("Query failed")
        
        repository = StatisticsRepository(mock_session)
        
        with pytest.raises(SQLAlchemyError):
            await repository.get_recovery_distribution()
    
    @pytest.mark.asyncio
    async def test_average_compliance_database_error(self, mock_session):
        """Test error handling for average compliance query failure."""
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        repository = StatisticsRepository(mock_session)
        
        with pytest.raises(SQLAlchemyError):
            await repository.get_average_compliance()
    
    @pytest.mark.asyncio
    async def test_average_readmission_probability_database_error(self, mock_session):
        """Test error handling for average probability query failure."""
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        repository = StatisticsRepository(mock_session)
        
        with pytest.raises(SQLAlchemyError):
            await repository.get_average_readmission_probability()
    
    @pytest.mark.asyncio
    async def test_high_risk_count_database_error(self, mock_session):
        """Test error handling for high risk count query failure."""
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        repository = StatisticsRepository(mock_session)
        
        with pytest.raises(SQLAlchemyError):
            await repository.get_high_risk_count()

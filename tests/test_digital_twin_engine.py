"""
Unit tests for DigitalTwinEngine service.

Validates Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
"""

import pytest
from app.services.digital_twin_engine import DigitalTwinEngine, DeviationMetrics, HealthScores
from app.models.schemas import PatientRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_record(**overrides) -> PatientRecord:
    """Return a valid PatientRecord with sensible defaults."""
    base = {
        "patient_id": "P001",
        "age": 50,
        "gender": "Male",
        "bmi": 25.0,
        "smoking_status": "Never",
        "alcohol_consumption": "None",
        "disease_type": "Diabetes",
        "heart_rate": 80,
        "systolic_bp": 110,
        "diastolic_bp": 70,
        "spo2": 97.5,
        "respiratory_rate": 16,
        "body_temperature": 36.65,
        "expected_steps": 5000,
        "expected_sleep_hours": 8.0,
        "water_intake_goal": 2000,
        "actual_steps": 5000,
        "actual_sleep_hours": 8.0,
        "water_intake": 2000,
        "medication_taken": "Yes",
        "exercise_completed": "Yes",
        "diet_compliance": 100.0,
    }
    base.update(overrides)
    return PatientRecord(**base)


# ---------------------------------------------------------------------------
# Tests: compute_deviations
# ---------------------------------------------------------------------------

class TestComputeDeviations:
    """Tests for DigitalTwinEngine.compute_deviations."""

    @pytest.fixture
    def engine(self):
        return DigitalTwinEngine()

    @pytest.mark.asyncio
    async def test_step_deviation_computed_correctly(self, engine):
        """step_deviation = |expected_steps - actual_steps| (Req 5.1)."""
        record = make_record(expected_steps=5000, actual_steps=3000)
        metrics = await engine.compute_deviations(record)
        assert abs(metrics.step_deviation - 2000.0) < 0.01

    @pytest.mark.asyncio
    async def test_sleep_deviation_computed_correctly(self, engine):
        """sleep_deviation = |expected_sleep_hours - actual_sleep_hours| (Req 5.2)."""
        record = make_record(expected_sleep_hours=8.0, actual_sleep_hours=6.0)
        metrics = await engine.compute_deviations(record)
        assert abs(metrics.sleep_deviation - 2.0) < 0.01

    @pytest.mark.asyncio
    async def test_water_deviation_computed_correctly(self, engine):
        """water_deviation = |water_intake_goal - water_intake| (Req 5.3)."""
        record = make_record(water_intake_goal=2000, water_intake=1500)
        metrics = await engine.compute_deviations(record)
        assert abs(metrics.water_deviation - 500.0) < 0.01

    @pytest.mark.asyncio
    async def test_medication_violation_flagged_when_not_taken(self, engine):
        """medication_violation = True when medication_taken == 'No' (Req 5.4)."""
        record = make_record(medication_taken="No")
        metrics = await engine.compute_deviations(record)
        assert metrics.medication_violation is True

    @pytest.mark.asyncio
    async def test_medication_violation_not_flagged_when_taken(self, engine):
        """medication_violation = False when medication_taken == 'Yes' (Req 5.4)."""
        record = make_record(medication_taken="Yes")
        metrics = await engine.compute_deviations(record)
        assert metrics.medication_violation is False

    @pytest.mark.asyncio
    async def test_exercise_violation_flagged_when_not_completed(self, engine):
        """exercise_violation = True when exercise_completed == 'No' (Req 5.5)."""
        record = make_record(exercise_completed="No")
        metrics = await engine.compute_deviations(record)
        assert metrics.exercise_violation is True

    @pytest.mark.asyncio
    async def test_exercise_violation_not_flagged_when_completed(self, engine):
        """exercise_violation = False when exercise_completed == 'Yes' (Req 5.5)."""
        record = make_record(exercise_completed="Yes")
        metrics = await engine.compute_deviations(record)
        assert metrics.exercise_violation is False

    @pytest.mark.asyncio
    async def test_overall_deviation_score_in_range(self, engine):
        """overall_deviation_score must be in [0, 100] (Req 5.6)."""
        record = make_record()
        metrics = await engine.compute_deviations(record)
        assert 0.0 <= metrics.overall_deviation_score <= 100.0

    @pytest.mark.asyncio
    async def test_perfect_adherence_gives_zero_deviation(self, engine):
        """Perfect adherence should yield overall_deviation_score near 0.0 (Req 5.6)."""
        record = make_record()
        metrics = await engine.compute_deviations(record)
        assert metrics.overall_deviation_score < 1.0

    @pytest.mark.asyncio
    async def test_no_adherence_gives_high_deviation(self, engine):
        """Full non-compliance should yield a high overall_deviation_score (Req 5.6)."""
        record = make_record(
            medication_taken="No",
            exercise_completed="No",
            actual_steps=0,
            water_intake=0,
            diet_compliance=0.0,
            actual_sleep_hours=0.0,
        )
        metrics = await engine.compute_deviations(record)
        # Score = 100 - compliance, compliance ≈ 0 → score ≈ 100
        assert metrics.overall_deviation_score > 80.0

    @pytest.mark.asyncio
    async def test_returns_deviation_metrics_instance(self, engine):
        """compute_deviations must return a DeviationMetrics instance."""
        record = make_record()
        metrics = await engine.compute_deviations(record)
        assert isinstance(metrics, DeviationMetrics)


# ---------------------------------------------------------------------------
# Tests: compute_health_scores
# ---------------------------------------------------------------------------

class TestComputeHealthScores:
    """Tests for DigitalTwinEngine.compute_health_scores."""

    @pytest.fixture
    def engine(self):
        return DigitalTwinEngine()

    @pytest.mark.asyncio
    async def test_returns_health_scores_instance(self, engine):
        """compute_health_scores must return a HealthScores instance."""
        record = make_record()
        scores = await engine.compute_health_scores(record, [])
        assert isinstance(scores, HealthScores)

    @pytest.mark.asyncio
    async def test_ideal_health_score_is_100(self, engine):
        """Ideal health score should be 100.0 (Req 5.7)."""
        record = make_record()
        scores = await engine.compute_health_scores(record, [])
        assert abs(scores.ideal_health_score - 100.0) < 0.01

    @pytest.mark.asyncio
    async def test_real_health_score_in_range(self, engine):
        """Real health score must be in [0, 100] (Req 5.8)."""
        record = make_record()
        scores = await engine.compute_health_scores(record, [])
        assert 0.0 <= scores.real_health_score <= 100.0

    @pytest.mark.asyncio
    async def test_deviation_score_equals_abs_difference(self, engine):
        """deviation_score = |ideal - real| (Req 7.4)."""
        record = make_record()
        scores = await engine.compute_health_scores(record, [])
        expected_deviation = abs(scores.ideal_health_score - scores.real_health_score)
        assert abs(scores.deviation_score - expected_deviation) < 0.01

    @pytest.mark.asyncio
    async def test_deviation_score_in_range(self, engine):
        """deviation_score must be in [0, 100]."""
        record = make_record()
        scores = await engine.compute_health_scores(record, [])
        assert 0.0 <= scores.deviation_score <= 100.0

    @pytest.mark.asyncio
    async def test_recovery_score_in_range(self, engine):
        """recovery_score must be in [0, 100]."""
        record = make_record()
        scores = await engine.compute_health_scores(record, [])
        assert 0.0 <= scores.recovery_score <= 100.0

    @pytest.mark.asyncio
    async def test_no_historical_records_gives_neutral_recovery(self, engine):
        """With no history, recovery score should be the neutral baseline (50.0)."""
        record = make_record()
        scores = await engine.compute_health_scores(record, [])
        # Only the single current record is used → recovery calculator gets 1 point → returns 50
        assert abs(scores.recovery_score - 50.0) < 0.01

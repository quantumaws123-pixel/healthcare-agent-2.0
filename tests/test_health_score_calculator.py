"""
Unit tests for HealthScoreCalculator service.

Validates Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8
"""

import pytest
from app.services.health_score_calculator import HealthScoreCalculator, VITAL_RANGES
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
        # Vitals at mid-range (optimal)
        "heart_rate": 80,           # mid of (60,100)
        "systolic_bp": 105,         # mid of (90,120)
        "diastolic_bp": 70,         # mid of (60,80)
        "spo2": 97.5,               # mid of (95,100)
        "respiratory_rate": 16,     # mid of (12,20)
        "body_temperature": 36.65,  # mid of (36.1,37.2)
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
# Tests: Ideal Health Score
# ---------------------------------------------------------------------------

class TestIdealHealthScore:
    """Tests for calculate_ideal_health_score (Req 7.1)."""

    @pytest.fixture
    def calc(self):
        return HealthScoreCalculator()

    @pytest.mark.asyncio
    async def test_ideal_score_is_100(self, calc):
        """Ideal health score should be 100.0 (Req 7.1)."""
        record = make_record()
        score = await calc.calculate_ideal_health_score(record)
        assert abs(score - 100.0) < 0.01

    @pytest.mark.asyncio
    async def test_ideal_score_in_range(self, calc):
        """Ideal health score must be in [0, 100] (Req 7.8)."""
        record = make_record()
        score = await calc.calculate_ideal_health_score(record)
        assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# Tests: Real Health Score
# ---------------------------------------------------------------------------

class TestRealHealthScore:
    """Tests for calculate_real_health_score (Req 7.2, 7.3)."""

    @pytest.fixture
    def calc(self):
        return HealthScoreCalculator()

    @pytest.mark.asyncio
    async def test_optimal_vitals_and_perfect_compliance(self, calc):
        """Optimal vitals + 100% compliance should yield a high real health score."""
        record = make_record()
        score = await calc.calculate_real_health_score(record)
        # Should be close to 100 — at least 80
        assert score >= 80.0

    @pytest.mark.asyncio
    async def test_real_score_in_range(self, calc):
        """Real health score must always be in [0, 100] (Req 7.8)."""
        # Worst case vitals
        record = make_record(
            heart_rate=30,
            systolic_bp=60,
            diastolic_bp=40,
            spo2=70.0,
            respiratory_rate=8,
            body_temperature=35.0,
            medication_taken="No",
            exercise_completed="No",
            actual_steps=0,
            water_intake=0,
            diet_compliance=0.0,
        )
        score = await calc.calculate_real_health_score(record)
        assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_compliance_score_used_when_present(self, calc):
        """If compliance_score is set on the record it should be used directly."""
        record = make_record(compliance_score=50.0)
        score = await calc.calculate_real_health_score(record)
        # Vitals are optimal so vitals sub-score ≈ 100
        # 50% blend: 100 * 0.5 + 50 * 0.5 = 75
        assert 70.0 <= score <= 80.0

    @pytest.mark.asyncio
    async def test_worse_vitals_lower_score(self, calc):
        """Records with worse vitals should produce a lower real health score."""
        good = make_record()
        bad = make_record(
            heart_rate=180,
            systolic_bp=200,
            diastolic_bp=130,
            spo2=75.0,
            respiratory_rate=35,
            body_temperature=40.5,
        )
        good_score = await calc.calculate_real_health_score(good)
        bad_score = await calc.calculate_real_health_score(bad)
        assert good_score > bad_score


# ---------------------------------------------------------------------------
# Tests: Recovery Score
# ---------------------------------------------------------------------------

class TestRecoveryScore:
    """Tests for calculate_recovery_score (Req 7.5, 7.6, 7.7, 7.8)."""

    @pytest.fixture
    def calc(self):
        return HealthScoreCalculator()

    def _records_with_scores(self, scores) -> list:
        """Build records with specific real_health_score values."""
        records = []
        for s in scores:
            r = make_record(real_health_score=s)
            records.append(r)
        return records

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_50(self, calc):
        """Fewer than 2 data points should return neutral baseline 50.0."""
        records = self._records_with_scores([80.0])
        score = await calc.calculate_recovery_score(records)
        assert abs(score - 50.0) < 0.01

    @pytest.mark.asyncio
    async def test_empty_records_returns_50(self, calc):
        """No records returns baseline 50.0."""
        score = await calc.calculate_recovery_score([])
        assert abs(score - 50.0) < 0.01

    @pytest.mark.asyncio
    async def test_improving_trend_increases_recovery_score(self, calc):
        """Steadily increasing scores should produce recovery_score > 50 (Req 7.6)."""
        # Slope well above 1.0
        scores = [50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]
        records = self._records_with_scores(scores)
        score = await calc.calculate_recovery_score(records)
        assert score > 50.0

    @pytest.mark.asyncio
    async def test_declining_trend_decreases_recovery_score(self, calc):
        """Steadily declining scores should produce recovery_score < 50 (Req 7.7)."""
        scores = [80.0, 75.0, 70.0, 65.0, 60.0, 55.0, 50.0]
        records = self._records_with_scores(scores)
        score = await calc.calculate_recovery_score(records)
        assert score < 50.0

    @pytest.mark.asyncio
    async def test_stable_trend_near_50(self, calc):
        """Flat scores (slope ≈ 0) should produce recovery_score ≈ 50."""
        scores = [70.0, 70.0, 70.0, 70.0, 70.0]
        records = self._records_with_scores(scores)
        score = await calc.calculate_recovery_score(records)
        assert 45.0 <= score <= 55.0

    @pytest.mark.asyncio
    async def test_recovery_score_in_range(self, calc):
        """Recovery score must always be in [0, 100] (Req 7.8)."""
        # Very steep slope (extreme improvement)
        scores = [0.0, 20.0, 40.0, 60.0, 80.0, 100.0]
        records = self._records_with_scores(scores)
        score = await calc.calculate_recovery_score(records)
        assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_records_without_real_health_score_are_ignored(self, calc):
        """Records with real_health_score=None should be excluded from trend."""
        # Mix: 5 valid, 2 None
        valid = self._records_with_scores([60.0, 65.0, 70.0, 75.0, 80.0])
        null_records = [make_record(real_health_score=None) for _ in range(2)]
        records = null_records + valid
        score = await calc.calculate_recovery_score(records)
        # Should still compute from valid points (improving) → > 50
        assert score > 50.0

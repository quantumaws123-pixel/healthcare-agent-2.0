"""
Unit tests for PredictionSystem service.

Validates Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
from app.services.prediction_system import PredictionSystem
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
        "heart_rate": 75,
        "systolic_bp": 115,
        "diastolic_bp": 75,
        "spo2": 97.0,
        "respiratory_rate": 16,
        "body_temperature": 36.6,
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


def records_with_scores(scores: list[float]) -> list[PatientRecord]:
    """Build PatientRecords with specified real_health_score values."""
    return [make_record(real_health_score=s) for s in scores]


# ---------------------------------------------------------------------------
# Tests: classify_recovery_status
# ---------------------------------------------------------------------------

class TestClassifyRecoveryStatus:
    """Tests for PredictionSystem.classify_recovery_status (Req 8.1-8.6)."""

    @pytest.fixture
    def system(self):
        return PredictionSystem()

    @pytest.mark.asyncio
    async def test_recovered(self, system):
        """recovery_score > 85 AND trend='Increasing' → 'Recovered' (Req 8.1)."""
        status = await system.classify_recovery_status(90.0, "Increasing", "Low")
        assert status == "Recovered"

    @pytest.mark.asyncio
    async def test_improving(self, system):
        """70 < recovery_score <= 85 AND trend='Increasing' → 'Improving' (Req 8.2)."""
        status = await system.classify_recovery_status(75.0, "Increasing", "Low")
        assert status == "Improving"

    @pytest.mark.asyncio
    async def test_stable(self, system):
        """50 < recovery_score <= 70 AND trend='Stable' → 'Stable' (Req 8.3)."""
        status = await system.classify_recovery_status(60.0, "Stable", "Low")
        assert status == "Stable"

    @pytest.mark.asyncio
    async def test_delayed_recovery(self, system):
        """30 < recovery_score <= 50 AND trend='Declining' → 'Delayed Recovery' (Req 8.4)."""
        status = await system.classify_recovery_status(40.0, "Declining", "Medium")
        assert status == "Delayed Recovery"

    @pytest.mark.asyncio
    async def test_worsening(self, system):
        """15 < recovery_score <= 30 AND trend='Declining' → 'Worsening' (Req 8.5)."""
        status = await system.classify_recovery_status(20.0, "Declining", "Medium")
        assert status == "Worsening"

    @pytest.mark.asyncio
    async def test_critical_low_score(self, system):
        """recovery_score <= 15 → 'Critical' regardless of trend (Req 8.6)."""
        status = await system.classify_recovery_status(15.0, "Increasing", "Low")
        assert status == "Critical"

    @pytest.mark.asyncio
    async def test_critical_zero_score(self, system):
        """recovery_score == 0 → 'Critical' (Req 8.6)."""
        status = await system.classify_recovery_status(0.0, "Stable", "Low")
        assert status == "Critical"

    @pytest.mark.asyncio
    async def test_critical_risk_level_overrides(self, system):
        """risk_level == 'Critical' → 'Critical' even with high recovery score (Req 8.6)."""
        status = await system.classify_recovery_status(90.0, "Increasing", "Critical")
        assert status == "Critical"

    @pytest.mark.asyncio
    async def test_boundary_85_with_increasing(self, system):
        """recovery_score == 85 is NOT > 85, so not 'Recovered' → 'Improving'."""
        status = await system.classify_recovery_status(85.0, "Increasing", "Low")
        assert status == "Improving"

    @pytest.mark.asyncio
    async def test_boundary_70_with_increasing(self, system):
        """recovery_score == 70 is not > 70, so not 'Improving' (Req 8.2)."""
        status = await system.classify_recovery_status(70.0, "Increasing", "Low")
        # 70 is not in (70, 85] → falls to catch-all "Stable"
        assert status == "Stable"

    @pytest.mark.asyncio
    async def test_unmatched_combination_defaults_to_stable(self, system):
        """A combination that matches no rule should fall back to 'Stable'."""
        # e.g., recovery_score=75 and trend="Stable" — doesn't match Improving (needs Increasing)
        status = await system.classify_recovery_status(75.0, "Stable", "Low")
        assert status == "Stable"


# ---------------------------------------------------------------------------
# Tests: analyze_health_trend
# ---------------------------------------------------------------------------

class TestAnalyzeHealthTrend:
    """Tests for PredictionSystem.analyze_health_trend (Req 9.1-9.5)."""

    @pytest.fixture
    def system(self):
        return PredictionSystem()

    @pytest.mark.asyncio
    async def test_increasing_trend(self, system):
        """Steeply increasing scores → 'Increasing' (Req 9.2)."""
        # Slope ≈ 5.0 > 1.0
        rec = records_with_scores([50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0])
        trend = await system.analyze_health_trend(rec)
        assert trend == "Increasing"

    @pytest.mark.asyncio
    async def test_declining_trend(self, system):
        """Steeply declining scores → 'Declining' (Req 9.4)."""
        # Slope ≈ -5.0 < -1.0
        rec = records_with_scores([80.0, 75.0, 70.0, 65.0, 60.0, 55.0, 50.0])
        trend = await system.analyze_health_trend(rec)
        assert trend == "Declining"

    @pytest.mark.asyncio
    async def test_stable_trend(self, system):
        """Flat scores → 'Stable' (Req 9.3)."""
        rec = records_with_scores([70.0, 70.0, 70.0, 70.0, 70.0])
        trend = await system.analyze_health_trend(rec)
        assert trend == "Stable"

    @pytest.mark.asyncio
    async def test_fewer_than_3_points_returns_stable(self, system):
        """Fewer than 3 data points → 'Stable' (Req 9.5)."""
        trend = await system.analyze_health_trend(records_with_scores([70.0, 75.0]))
        assert trend == "Stable"

    @pytest.mark.asyncio
    async def test_empty_records_returns_stable(self, system):
        """No records → 'Stable' (Req 9.5)."""
        trend = await system.analyze_health_trend([])
        assert trend == "Stable"

    @pytest.mark.asyncio
    async def test_only_last_7_records_used(self, system):
        """Only the last 7 records are considered (Req 9.1)."""
        # First 10 records are declining; last 7 are steeply increasing
        declining = records_with_scores([90.0 - i * 5 for i in range(10)])
        increasing = records_with_scores([40.0 + i * 6 for i in range(7)])
        all_records = declining + increasing
        trend = await system.analyze_health_trend(all_records)
        assert trend == "Increasing"

    @pytest.mark.asyncio
    async def test_slope_threshold_boundary_just_above_1(self, system):
        """Slope slightly > 1.0 should be 'Increasing' (boundary test)."""
        # Use a clear upward slope > 1 per step
        rec = records_with_scores([60.0, 62.0, 64.0, 66.0, 68.0])
        trend = await system.analyze_health_trend(rec)
        assert trend == "Increasing"

    @pytest.mark.asyncio
    async def test_slope_threshold_boundary_just_below_minus_1(self, system):
        """Slope slightly < -1.0 should be 'Declining' (boundary test)."""
        rec = records_with_scores([68.0, 66.0, 64.0, 62.0, 60.0])
        trend = await system.analyze_health_trend(rec)
        assert trend == "Declining"

    @pytest.mark.asyncio
    async def test_records_without_scores_are_excluded(self, system):
        """Records with real_health_score=None should be ignored (Req 9.1)."""
        null_records = [make_record(real_health_score=None) for _ in range(4)]
        valid = records_with_scores([60.0, 65.0, 70.0])
        trend = await system.analyze_health_trend(null_records + valid)
        # Only 3 valid points — slope = 5 > 1 → Increasing
        assert trend == "Increasing"


# ---------------------------------------------------------------------------
# Tests: predict_readmission raises without engine
# ---------------------------------------------------------------------------

class TestPredictReadmission:
    """Tests for PredictionSystem.predict_readmission."""

    @pytest.mark.asyncio
    async def test_raises_without_inference_engine(self):
        """predict_readmission without an engine should raise RuntimeError."""
        system = PredictionSystem(inference_engine=None)
        record = make_record()
        with pytest.raises(RuntimeError, match="InferenceEngine"):
            await system.predict_readmission(record)

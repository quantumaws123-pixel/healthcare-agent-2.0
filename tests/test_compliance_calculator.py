"""
Unit tests for ComplianceCalculator service.

Validates Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
"""

import pytest
from app.services.compliance_calculator import ComplianceCalculator
from app.models.schemas import PatientRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_record(**overrides) -> PatientRecord:
    """Return a valid PatientRecord with sensible defaults, overridden by kwargs."""
    base = {
        "patient_id": "P001",
        "age": 50,
        "gender": "Male",
        "bmi": 25.0,
        "smoking_status": "Never",
        "alcohol_consumption": "None",
        "disease_type": "Diabetes",
        "heart_rate": 75,
        "systolic_bp": 120,
        "diastolic_bp": 78,
        "spo2": 98.0,
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestComplianceCalculatorScore:
    """Tests for calculate_compliance_score method."""

    @pytest.fixture
    def calc(self):
        return ComplianceCalculator()

    @pytest.mark.asyncio
    async def test_perfect_compliance_is_100(self, calc):
        """Full adherence across all components should yield 100.0 (Req 6.8)."""
        records = [make_record()]
        score = await calc.calculate_compliance_score(records)
        assert abs(score - 100.0) < 0.01

    @pytest.mark.asyncio
    async def test_zero_compliance_medication_and_exercise(self, calc):
        """No medication + no exercise + zero steps/water/diet should give a low score."""
        records = [make_record(
            medication_taken="No",
            exercise_completed="No",
            actual_steps=0,
            actual_sleep_hours=0.0,
            water_intake=0,
            diet_compliance=0.0,
        )]
        score = await calc.calculate_compliance_score(records)
        # At minimum: sleep deviation is large; score should be well below 50
        assert score < 50.0

    @pytest.mark.asyncio
    async def test_empty_records_raises(self, calc):
        """Empty patient_records should raise ValueError (Req 6.8 guard)."""
        with pytest.raises(ValueError, match="must not be empty"):
            await calc.calculate_compliance_score([])

    @pytest.mark.asyncio
    async def test_score_in_valid_range(self, calc):
        """Result must always be in [0, 100] (Req 6.8)."""
        records = [make_record(
            actual_steps=0,
            water_intake=0,
            diet_compliance=0.0,
            medication_taken="No",
            exercise_completed="No",
        )]
        score = await calc.calculate_compliance_score(records)
        assert 0.0 <= score <= 100.0

    @pytest.mark.asyncio
    async def test_window_trimming(self, calc):
        """Only the last window_days records are used."""
        # Create 10 records: first 7 bad, last 3 perfect
        bad = make_record(medication_taken="No", exercise_completed="No",
                          actual_steps=0, water_intake=0, diet_compliance=0.0)
        good = make_record()
        records = [bad] * 7 + [good] * 3
        score_3 = await calc.calculate_compliance_score(records, window_days=3)
        score_10 = await calc.calculate_compliance_score(records, window_days=10)
        # window=3 uses only the 3 perfect records → should be 100
        assert abs(score_3 - 100.0) < 0.01
        # window=10 uses all records → score should be lower
        assert score_10 < score_3


class TestMedicationCompliance:
    """Tests for _calculate_medication_compliance (Req 6.1)."""

    def setup_method(self):
        self.calc = ComplianceCalculator()

    def test_all_medication_taken(self):
        records = [make_record(medication_taken="Yes")] * 5
        result = self.calc._calculate_medication_compliance(records, len(records))
        assert abs(result - 100.0) < 0.01

    def test_no_medication_taken(self):
        records = [make_record(medication_taken="No")] * 5
        result = self.calc._calculate_medication_compliance(records, len(records))
        assert abs(result - 0.0) < 0.01

    def test_partial_medication(self):
        records = [make_record(medication_taken="Yes")] * 3 + \
                  [make_record(medication_taken="No")] * 2
        result = self.calc._calculate_medication_compliance(records, len(records))
        assert abs(result - 60.0) < 0.01


class TestExerciseCompliance:
    """Tests for _calculate_exercise_compliance (Req 6.2)."""

    def setup_method(self):
        self.calc = ComplianceCalculator()

    def test_all_exercise_completed(self):
        records = [make_record(exercise_completed="Yes")] * 4
        result = self.calc._calculate_exercise_compliance(records, len(records))
        assert abs(result - 100.0) < 0.01

    def test_no_exercise_completed(self):
        records = [make_record(exercise_completed="No")] * 4
        result = self.calc._calculate_exercise_compliance(records, len(records))
        assert abs(result - 0.0) < 0.01

    def test_partial_exercise(self):
        records = [make_record(exercise_completed="Yes")] * 1 + \
                  [make_record(exercise_completed="No")] * 3
        result = self.calc._calculate_exercise_compliance(records, len(records))
        assert abs(result - 25.0) < 0.01


class TestStepCompliance:
    """Tests for _calculate_step_compliance (Req 6.3)."""

    def setup_method(self):
        self.calc = ComplianceCalculator()

    def test_meets_step_goal(self):
        records = [make_record(actual_steps=5000, expected_steps=5000)]
        result = self.calc._calculate_step_compliance(records)
        assert abs(result - 100.0) < 0.01

    def test_exceeds_step_goal_caps_at_100(self):
        """Over-achieving the step goal should be capped at 100% (Req 6.3)."""
        records = [make_record(actual_steps=10000, expected_steps=5000)]
        result = self.calc._calculate_step_compliance(records)
        assert abs(result - 100.0) < 0.01

    def test_half_step_goal(self):
        records = [make_record(actual_steps=2500, expected_steps=5000)]
        result = self.calc._calculate_step_compliance(records)
        assert abs(result - 50.0) < 0.01

    def test_zero_expected_steps_defaults_to_100(self):
        records = [make_record(actual_steps=0, expected_steps=0)]
        result = self.calc._calculate_step_compliance(records)
        assert abs(result - 100.0) < 0.01


class TestSleepCompliance:
    """Tests for _calculate_sleep_compliance (Req 6.4)."""

    def setup_method(self):
        self.calc = ComplianceCalculator()

    def test_perfect_sleep(self):
        records = [make_record(actual_sleep_hours=8.0, expected_sleep_hours=8.0)]
        result = self.calc._calculate_sleep_compliance(records)
        assert abs(result - 100.0) < 0.01

    def test_sleep_deviation_reduces_score(self):
        # 50% deviation from expected → score = 100 - 50 = 50
        records = [make_record(actual_sleep_hours=4.0, expected_sleep_hours=8.0)]
        result = self.calc._calculate_sleep_compliance(records)
        assert abs(result - 50.0) < 0.01

    def test_large_sleep_deviation_clamped_at_zero(self):
        # Very large deviation should not go below 0
        records = [make_record(actual_sleep_hours=0.0, expected_sleep_hours=8.0)]
        result = self.calc._calculate_sleep_compliance(records)
        assert result >= 0.0

    def test_zero_expected_sleep_defaults_to_100(self):
        records = [make_record(actual_sleep_hours=8.0, expected_sleep_hours=0.0)]
        result = self.calc._calculate_sleep_compliance(records)
        assert abs(result - 100.0) < 0.01


class TestDietCompliance:
    """Tests for _calculate_diet_compliance (Req 6.5)."""

    def setup_method(self):
        self.calc = ComplianceCalculator()

    def test_perfect_diet(self):
        records = [make_record(diet_compliance=100.0)]
        result = self.calc._calculate_diet_compliance(records)
        assert abs(result - 100.0) < 0.01

    def test_zero_diet(self):
        records = [make_record(diet_compliance=0.0)]
        result = self.calc._calculate_diet_compliance(records)
        assert abs(result - 0.0) < 0.01

    def test_average_of_multiple_records(self):
        records = [make_record(diet_compliance=80.0), make_record(diet_compliance=60.0)]
        result = self.calc._calculate_diet_compliance(records)
        assert abs(result - 70.0) < 0.01


class TestWaterCompliance:
    """Tests for _calculate_water_compliance (Req 6.6)."""

    def setup_method(self):
        self.calc = ComplianceCalculator()

    def test_meets_water_goal(self):
        records = [make_record(water_intake=2000, water_intake_goal=2000)]
        result = self.calc._calculate_water_compliance(records)
        assert abs(result - 100.0) < 0.01

    def test_exceeds_water_goal_caps_at_100(self):
        """Drinking more than the goal is capped at 100% (Req 6.6)."""
        records = [make_record(water_intake=3000, water_intake_goal=2000)]
        result = self.calc._calculate_water_compliance(records)
        assert abs(result - 100.0) < 0.01

    def test_half_water_goal(self):
        records = [make_record(water_intake=1000, water_intake_goal=2000)]
        result = self.calc._calculate_water_compliance(records)
        assert abs(result - 50.0) < 0.01

    def test_zero_water_goal_defaults_to_100(self):
        records = [make_record(water_intake=0, water_intake_goal=0)]
        result = self.calc._calculate_water_compliance(records)
        assert abs(result - 100.0) < 0.01


class TestWeightedAggregation:
    """Tests for weighted aggregation (Req 6.7)."""

    def setup_method(self):
        self.calc = ComplianceCalculator()

    @pytest.mark.asyncio
    async def test_weights_sum_to_one(self):
        """Ensure all defined weights sum to 1.0 (Req 6.7)."""
        total = (
            ComplianceCalculator.MEDICATION_WEIGHT
            + ComplianceCalculator.EXERCISE_WEIGHT
            + ComplianceCalculator.STEPS_WEIGHT
            + ComplianceCalculator.SLEEP_WEIGHT
            + ComplianceCalculator.DIET_WEIGHT
            + ComplianceCalculator.WATER_WEIGHT
        )
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.asyncio
    async def test_only_medication_noncompliant(self):
        """Only medication = 0 → score reduced by MEDICATION_WEIGHT × 100."""
        records = [make_record(medication_taken="No")]
        score = await self.calc.calculate_compliance_score(records)
        # All other components are 100, medication is 0
        # Expected = 100 - 0.30 * 100 = 70
        expected = 100.0 - 100.0 * ComplianceCalculator.MEDICATION_WEIGHT
        assert abs(score - expected) < 0.5  # small tolerance for floating-point

"""
Unit tests for RecommendationEngine service.

Validates Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
"""

import pytest
from app.services.recommendation_engine import RecommendationEngine


class TestRecommendationEngine:
    """Tests for generate_recommendation method (Req 10.1-10.7)."""

    @pytest.fixture
    def engine(self):
        return RecommendationEngine()

    # -----------------------------------------------------------------------
    # Rule 5: Continue Current Treatment (priority 1, default)
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_continue_current_treatment_default(self, engine):
        """Low risk, good compliance, low deviation → 'Continue Current Treatment' (Req 10.1)."""
        rec = await engine.generate_recommendation(
            risk_level="Low",
            recovery_status="Recovered",
            compliance_score=85.0,
            deviation_score=20.0,
            readmission_probability=0.1,
        )
        assert rec == "Continue Current Treatment"

    @pytest.mark.asyncio
    async def test_continue_for_improving_low_risk(self, engine):
        """Low risk + Improving status → 'Continue Current Treatment' (Req 10.1)."""
        rec = await engine.generate_recommendation(
            risk_level="Low",
            recovery_status="Improving",
            compliance_score=75.0,
            deviation_score=15.0,
            readmission_probability=0.15,
        )
        assert rec == "Continue Current Treatment"

    # -----------------------------------------------------------------------
    # Rule 4: Increase Monitoring (priority 2)
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_increase_monitoring_medium_risk(self, engine):
        """risk_level = 'Medium' → 'Increase Monitoring' (Req 10.2)."""
        rec = await engine.generate_recommendation(
            risk_level="Medium",
            recovery_status="Stable",
            compliance_score=70.0,
            deviation_score=20.0,
            readmission_probability=0.45,
        )
        assert rec == "Increase Monitoring"

    @pytest.mark.asyncio
    async def test_increase_monitoring_low_compliance(self, engine):
        """compliance_score < 60 → 'Increase Monitoring' (Req 10.2)."""
        rec = await engine.generate_recommendation(
            risk_level="Low",
            recovery_status="Stable",
            compliance_score=55.0,
            deviation_score=20.0,
            readmission_probability=0.25,
        )
        assert rec == "Increase Monitoring"

    @pytest.mark.asyncio
    async def test_increase_monitoring_exactly_60_compliance_not_triggered(self, engine):
        """compliance_score == 60 is NOT < 60, so rule 4 doesn't trigger on that condition."""
        rec = await engine.generate_recommendation(
            risk_level="Low",
            recovery_status="Recovered",
            compliance_score=60.0,
            deviation_score=10.0,
            readmission_probability=0.05,
        )
        assert rec == "Continue Current Treatment"

    # -----------------------------------------------------------------------
    # Rule 3: Medication Adjustment (priority 3)
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_medication_adjustment_high_risk(self, engine):
        """risk_level = 'High' → 'Medication Adjustment' (Req 10.3)."""
        rec = await engine.generate_recommendation(
            risk_level="High",
            recovery_status="Stable",
            compliance_score=70.0,
            deviation_score=30.0,
            readmission_probability=0.65,
        )
        assert rec == "Medication Adjustment"

    @pytest.mark.asyncio
    async def test_medication_adjustment_high_deviation(self, engine):
        """deviation_score > 40 → 'Medication Adjustment' (Req 10.3)."""
        rec = await engine.generate_recommendation(
            risk_level="Low",
            recovery_status="Stable",
            compliance_score=70.0,
            deviation_score=41.0,
            readmission_probability=0.2,
        )
        assert rec == "Medication Adjustment"

    @pytest.mark.asyncio
    async def test_medication_adjustment_exactly_40_deviation_not_triggered(self, engine):
        """deviation_score == 40 is NOT > 40, so it shouldn't trigger rule 3 alone."""
        rec = await engine.generate_recommendation(
            risk_level="Low",
            recovery_status="Recovered",
            compliance_score=75.0,
            deviation_score=40.0,
            readmission_probability=0.1,
        )
        assert rec == "Continue Current Treatment"

    # -----------------------------------------------------------------------
    # Rule 2: Immediate Doctor Review (priority 4)
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_immediate_doctor_review_critical_risk(self, engine):
        """risk_level = 'Critical' → 'Immediate Doctor Review' (Req 10.4)."""
        rec = await engine.generate_recommendation(
            risk_level="Critical",
            recovery_status="Stable",
            compliance_score=70.0,
            deviation_score=20.0,
            readmission_probability=0.80,
        )
        assert rec == "Immediate Doctor Review"

    @pytest.mark.asyncio
    async def test_immediate_doctor_review_worsening(self, engine):
        """recovery_status = 'Worsening' → 'Immediate Doctor Review' (Req 10.4)."""
        rec = await engine.generate_recommendation(
            risk_level="Medium",
            recovery_status="Worsening",
            compliance_score=50.0,
            deviation_score=35.0,
            readmission_probability=0.50,
        )
        assert rec == "Immediate Doctor Review"

    @pytest.mark.asyncio
    async def test_immediate_doctor_review_critical_status(self, engine):
        """recovery_status = 'Critical' → 'Immediate Doctor Review' (Req 10.4)."""
        rec = await engine.generate_recommendation(
            risk_level="High",
            recovery_status="Critical",
            compliance_score=40.0,
            deviation_score=50.0,
            readmission_probability=0.70,
        )
        assert rec == "Immediate Doctor Review"

    # -----------------------------------------------------------------------
    # Rule 1: Hospital Readmission (priority 5)
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_hospital_readmission_high_probability(self, engine):
        """readmission_probability > 0.85 → 'Hospital Readmission' (Req 10.5)."""
        rec = await engine.generate_recommendation(
            risk_level="Critical",
            recovery_status="Critical",
            compliance_score=10.0,
            deviation_score=80.0,
            readmission_probability=0.90,
        )
        assert rec == "Hospital Readmission"

    @pytest.mark.asyncio
    async def test_hospital_readmission_exactly_085_not_triggered(self, engine):
        """readmission_probability == 0.85 is NOT > 0.85; should not trigger rule 1."""
        rec = await engine.generate_recommendation(
            risk_level="Critical",
            recovery_status="Critical",
            compliance_score=10.0,
            deviation_score=80.0,
            readmission_probability=0.85,
        )
        # Critical risk → Immediate Doctor Review (not Hospital Readmission)
        assert rec == "Immediate Doctor Review"

    # -----------------------------------------------------------------------
    # Rule prioritization (Req 10.6)
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_priority_hospital_over_immediate_review(self, engine):
        """Hospital Readmission (priority 5) beats Immediate Doctor Review (priority 4)."""
        rec = await engine.generate_recommendation(
            risk_level="Critical",
            recovery_status="Worsening",
            compliance_score=10.0,
            deviation_score=60.0,
            readmission_probability=0.95,  # triggers hospital readmission
        )
        assert rec == "Hospital Readmission"

    @pytest.mark.asyncio
    async def test_priority_immediate_review_over_medication_adjustment(self, engine):
        """Immediate Doctor Review (priority 4) beats Medication Adjustment (priority 3)."""
        rec = await engine.generate_recommendation(
            risk_level="Critical",   # triggers immediate doctor review
            recovery_status="Stable",
            compliance_score=70.0,
            deviation_score=50.0,   # also triggers medication adjustment
            readmission_probability=0.70,
        )
        assert rec == "Immediate Doctor Review"

    @pytest.mark.asyncio
    async def test_priority_medication_over_increase_monitoring(self, engine):
        """Medication Adjustment (priority 3) beats Increase Monitoring (priority 2)."""
        rec = await engine.generate_recommendation(
            risk_level="High",       # triggers medication adjustment
            recovery_status="Stable",
            compliance_score=55.0,  # also triggers increase monitoring
            deviation_score=30.0,
            readmission_probability=0.70,
        )
        assert rec == "Medication Adjustment"

    # -----------------------------------------------------------------------
    # Input validation
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_invalid_readmission_probability_raises(self, engine):
        """readmission_probability outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError, match="readmission_probability"):
            await engine.generate_recommendation(
                risk_level="Low",
                recovery_status="Stable",
                compliance_score=70.0,
                deviation_score=20.0,
                readmission_probability=1.5,
            )

    @pytest.mark.asyncio
    async def test_invalid_compliance_score_raises(self, engine):
        """compliance_score outside [0, 100] should raise ValueError."""
        with pytest.raises(ValueError, match="compliance_score"):
            await engine.generate_recommendation(
                risk_level="Low",
                recovery_status="Stable",
                compliance_score=-5.0,
                deviation_score=20.0,
                readmission_probability=0.3,
            )

    @pytest.mark.asyncio
    async def test_invalid_deviation_score_raises(self, engine):
        """deviation_score outside [0, 100] should raise ValueError."""
        with pytest.raises(ValueError, match="deviation_score"):
            await engine.generate_recommendation(
                risk_level="Low",
                recovery_status="Stable",
                compliance_score=70.0,
                deviation_score=110.0,
                readmission_probability=0.3,
            )

    # -----------------------------------------------------------------------
    # Recommendation labels match expected strings
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_all_recommendation_labels_are_valid(self, engine):
        """Each rule should return one of the five defined recommendation strings."""
        valid_labels = set(RecommendationEngine.RECOMMENDATIONS.values())
        test_cases = [
            ("Low", "Recovered", 85.0, 20.0, 0.1),
            ("Medium", "Stable", 70.0, 20.0, 0.45),
            ("Low", "Stable", 55.0, 20.0, 0.25),
            ("High", "Stable", 70.0, 30.0, 0.65),
            ("Critical", "Stable", 70.0, 20.0, 0.80),
            ("Critical", "Critical", 10.0, 80.0, 0.95),
        ]
        for risk, status, comp, dev, prob in test_cases:
            rec = await engine.generate_recommendation(
                risk_level=risk,
                recovery_status=status,
                compliance_score=comp,
                deviation_score=dev,
                readmission_probability=prob,
            )
            assert rec in valid_labels, f"Unexpected recommendation: {rec!r}"

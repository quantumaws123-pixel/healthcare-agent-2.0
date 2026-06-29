"""
Recommendation Engine for Healthcare Agent 2.0 Backend ML System.

This module implements a rule-based clinical decision support system that generates
prioritized doctor recommendations based on patient state and AI predictions.

Validates Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Rule-based system for generating prioritized clinical recommendations.

    Evaluates patient state and prediction outputs against a set of clinical rules
    ordered by severity. When multiple conditions are met simultaneously, the most
    severe (highest priority) recommendation is returned.

    Priority mapping (higher number = higher severity):
        1 - Continue Current Treatment  (default / low risk)
        2 - Increase Monitoring         (medium risk or low compliance)
        3 - Medication Adjustment       (high risk or large deviation)
        4 - Immediate Doctor Review     (critical risk or worsening status)
        5 - Hospital Readmission        (very high readmission probability)

    Validates Requirements 10.1–10.7
    """

    # Priority dictionary: priority level -> recommendation label.
    # Higher priority value = more severe recommendation.
    RECOMMENDATIONS: dict[int, str] = {
        1: "Continue Current Treatment",
        2: "Increase Monitoring",
        3: "Medication Adjustment",
        4: "Immediate Doctor Review",
        5: "Hospital Readmission",
    }

    # Thresholds used by the rule evaluation
    READMISSION_THRESHOLD: float = 0.85
    COMPLIANCE_LOW_THRESHOLD: float = 60.0
    DEVIATION_HIGH_THRESHOLD: float = 40.0

    async def generate_recommendation(
        self,
        risk_level: str,
        recovery_status: str,
        compliance_score: float,
        deviation_score: float,
        readmission_probability: float,
        patient_id: Optional[str] = None,
    ) -> str:
        """
        Generate a prioritized clinical recommendation for a patient.

        Rules are evaluated from highest to lowest priority. The first rule whose
        condition is satisfied determines the recommendation. This ensures that when
        multiple conditions are met the most clinically urgent action is returned.

        Rule evaluation order (highest severity first):

        1. Hospital Readmission  (priority 5)
           Condition: readmission_probability > 0.85
           Rationale: Extremely high predicted readmission risk requires immediate
                      hospital-level intervention.  (Requirement 10.5)

        2. Immediate Doctor Review  (priority 4)
           Condition: risk_level == "Critical"
                      OR recovery_status in {"Worsening", "Critical"}
           Rationale: Either the ML model classifies the patient as critical or
                      the recovery trajectory is deteriorating rapidly.
                      (Requirement 10.4)

        3. Medication Adjustment  (priority 3)
           Condition: risk_level == "High"
                      OR deviation_score > 40
           Rationale: High predicted risk or a significant gap between the ideal and
                      real twin suggests the current treatment plan is insufficient.
                      (Requirement 10.3)

        4. Increase Monitoring  (priority 2)
           Condition: risk_level == "Medium"
                      OR compliance_score < 60
           Rationale: Moderate risk or poor adherence warrants closer observation
                      without immediate intervention.  (Requirement 10.2)

        5. Continue Current Treatment  (priority 1)  — default
           Condition: all other conditions are false
                      (typically risk_level == "Low" and recovering/improving status)
           Rationale: Patient is progressing well; no change to the plan is needed.
                      (Requirement 10.1)

        Args:
            risk_level: ML-classified risk level – "Low", "Medium", "High", or "Critical".
            recovery_status: Classified recovery status – one of "Recovered", "Improving",
                "Stable", "Delayed Recovery", "Worsening", or "Critical".
            compliance_score: Weighted compliance score in [0, 100].
            deviation_score: Absolute deviation between ideal and real health scores, [0, 100].
            readmission_probability: Predicted probability of 30-day readmission, [0, 1].
            patient_id: Optional patient identifier used for structured audit logging.

        Returns:
            A recommendation string matching one of the values in RECOMMENDATIONS.

        Raises:
            ValueError: If any numeric argument is outside its expected range.
        """
        # --- Input validation ---
        if not 0.0 <= readmission_probability <= 1.0:
            raise ValueError(
                f"readmission_probability must be in [0, 1], got {readmission_probability}"
            )
        if not 0.0 <= compliance_score <= 100.0:
            raise ValueError(
                f"compliance_score must be in [0, 100], got {compliance_score}"
            )
        if not 0.0 <= deviation_score <= 100.0:
            raise ValueError(
                f"deviation_score must be in [0, 100], got {deviation_score}"
            )

        patient_context = f"patient_id={patient_id}" if patient_id else "patient_id=<unknown>"

        logger.debug(
            "Evaluating recommendation rules | %s | risk_level=%s | recovery_status=%s | "
            "compliance_score=%.2f | deviation_score=%.2f | readmission_probability=%.4f",
            patient_context,
            risk_level,
            recovery_status,
            compliance_score,
            deviation_score,
            readmission_probability,
        )

        # ------------------------------------------------------------------
        # Rule 1 – Hospital Readmission (priority 5)
        # Requirement 10.5
        # ------------------------------------------------------------------
        if readmission_probability > self.READMISSION_THRESHOLD:
            recommendation = self.RECOMMENDATIONS[5]
            logger.info(
                "Recommendation='%s' | %s | Reason: readmission_probability=%.4f > %.2f",
                recommendation,
                patient_context,
                readmission_probability,
                self.READMISSION_THRESHOLD,
            )
            return recommendation

        # ------------------------------------------------------------------
        # Rule 2 – Immediate Doctor Review (priority 4)
        # Requirement 10.4
        # ------------------------------------------------------------------
        if risk_level == "Critical" or recovery_status in {"Worsening", "Critical"}:
            recommendation = self.RECOMMENDATIONS[4]
            triggered_conditions = []
            if risk_level == "Critical":
                triggered_conditions.append(f"risk_level={risk_level!r}")
            if recovery_status in {"Worsening", "Critical"}:
                triggered_conditions.append(f"recovery_status={recovery_status!r}")
            logger.info(
                "Recommendation='%s' | %s | Reason: %s",
                recommendation,
                patient_context,
                ", ".join(triggered_conditions),
            )
            return recommendation

        # ------------------------------------------------------------------
        # Rule 3 – Medication Adjustment (priority 3)
        # Requirement 10.3
        # ------------------------------------------------------------------
        if risk_level == "High" or deviation_score > self.DEVIATION_HIGH_THRESHOLD:
            recommendation = self.RECOMMENDATIONS[3]
            triggered_conditions = []
            if risk_level == "High":
                triggered_conditions.append(f"risk_level={risk_level!r}")
            if deviation_score > self.DEVIATION_HIGH_THRESHOLD:
                triggered_conditions.append(
                    f"deviation_score={deviation_score:.2f} > {self.DEVIATION_HIGH_THRESHOLD}"
                )
            logger.info(
                "Recommendation='%s' | %s | Reason: %s",
                recommendation,
                patient_context,
                ", ".join(triggered_conditions),
            )
            return recommendation

        # ------------------------------------------------------------------
        # Rule 4 – Increase Monitoring (priority 2)
        # Requirement 10.2
        # ------------------------------------------------------------------
        if risk_level == "Medium" or compliance_score < self.COMPLIANCE_LOW_THRESHOLD:
            recommendation = self.RECOMMENDATIONS[2]
            triggered_conditions = []
            if risk_level == "Medium":
                triggered_conditions.append(f"risk_level={risk_level!r}")
            if compliance_score < self.COMPLIANCE_LOW_THRESHOLD:
                triggered_conditions.append(
                    f"compliance_score={compliance_score:.2f} < {self.COMPLIANCE_LOW_THRESHOLD}"
                )
            logger.info(
                "Recommendation='%s' | %s | Reason: %s",
                recommendation,
                patient_context,
                ", ".join(triggered_conditions),
            )
            return recommendation

        # ------------------------------------------------------------------
        # Rule 5 – Continue Current Treatment (priority 1, default)
        # Requirement 10.1
        # ------------------------------------------------------------------
        recommendation = self.RECOMMENDATIONS[1]
        logger.info(
            "Recommendation='%s' | %s | Reason: risk_level=%r, recovery_status=%r — "
            "no escalation conditions met",
            recommendation,
            patient_context,
            risk_level,
            recovery_status,
        )
        return recommendation

"""
Compliance Calculator Service for Healthcare Agent 2.0 Backend ML System.

Computes weighted compliance scores from patient adherence metrics across
medication, exercise, steps, sleep, diet, and water intake categories.

Validates Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
"""

import logging
from typing import List

from app.models.schemas import PatientRecord

logger = logging.getLogger(__name__)


class ComplianceCalculator:
    """
    Calculates weighted compliance score from patient adherence metrics.

    Each component represents how closely a patient followed their prescribed plan
    for a given time window. The final score is a weighted sum of all components.

    Weights (must sum to 1.0):
        - Medication : 30%  (Requirement 6.7)
        - Exercise   : 20%  (Requirement 6.7)
        - Steps      : 15%  (Requirement 6.7)
        - Sleep      : 15%  (Requirement 6.7)
        - Diet       : 10%  (Requirement 6.7)
        - Water      : 10%  (Requirement 6.7)
    """

    # Component weights — must sum to 1.0
    MEDICATION_WEIGHT: float = 0.30
    EXERCISE_WEIGHT: float = 0.20
    STEPS_WEIGHT: float = 0.15
    SLEEP_WEIGHT: float = 0.15
    DIET_WEIGHT: float = 0.10
    WATER_WEIGHT: float = 0.10

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    async def calculate_compliance_score(
        self,
        patient_records: List[PatientRecord],
        window_days: int = 7,
    ) -> float:
        """
        Compute the weighted overall compliance score over a sliding window.

        Algorithm (Requirement 6.7):
            1. medication  = (days medication_taken=="Yes") / total_days * 100
            2. exercise    = (days exercise_completed=="Yes") / total_days * 100
            3. steps       = min(100, avg(actual_steps / expected_steps) * 100)
            4. sleep       = 100 - avg(|actual - expected| / expected * 100)
            5. diet        = avg(diet_compliance field)
            6. water       = min(100, avg(water_intake / water_goal) * 100)
            7. overall     = sum(component * weight)

        Args:
            patient_records: Patient records for the analysis window.
                Records are trimmed to the most recent ``window_days`` entries.
            window_days: Maximum number of days to consider.

        Returns:
            Compliance score in [0, 100].

        Raises:
            ValueError: If ``patient_records`` is empty.
        """
        if not patient_records:
            raise ValueError("patient_records must not be empty")

        # Use the most recent window_days records
        records = patient_records[-window_days:]
        total_days = len(records)

        medication = self._calculate_medication_compliance(records, total_days)
        exercise = self._calculate_exercise_compliance(records, total_days)
        steps = self._calculate_step_compliance(records)
        sleep = self._calculate_sleep_compliance(records)
        diet = self._calculate_diet_compliance(records)
        water = self._calculate_water_compliance(records)

        overall = (
            medication * self.MEDICATION_WEIGHT
            + exercise * self.EXERCISE_WEIGHT
            + steps * self.STEPS_WEIGHT
            + sleep * self.SLEEP_WEIGHT
            + diet * self.DIET_WEIGHT
            + water * self.WATER_WEIGHT
        )

        # Clamp to [0, 100] to guard against floating-point edge cases
        result = max(0.0, min(100.0, overall))

        logger.debug(
            "Compliance score calculated: overall=%.2f "
            "(medication=%.2f, exercise=%.2f, steps=%.2f, "
            "sleep=%.2f, diet=%.2f, water=%.2f) over %d day(s)",
            result,
            medication,
            exercise,
            steps,
            sleep,
            diet,
            water,
            total_days,
        )

        return result

    # ------------------------------------------------------------------ #
    # Individual component calculations                                    #
    # ------------------------------------------------------------------ #

    def _calculate_medication_compliance(
        self,
        records: List[PatientRecord],
        total_days: int,
    ) -> float:
        """
        Medication compliance: percentage of days where medication was taken.

        Formula: (days with medication_taken="Yes") / total_days * 100

        Validates Requirement 6.1

        Args:
            records: Patient records to evaluate.
            total_days: Denominator for the percentage calculation.

        Returns:
            Score in [0, 100].
        """
        if total_days == 0:
            return 0.0
        days_taken = sum(1 for r in records if r.medication_taken == "Yes")
        return (days_taken / total_days) * 100.0

    def _calculate_exercise_compliance(
        self,
        records: List[PatientRecord],
        total_days: int,
    ) -> float:
        """
        Exercise compliance: percentage of days where exercise was completed.

        Formula: (days with exercise_completed="Yes") / total_days * 100

        Validates Requirement 6.2

        Args:
            records: Patient records to evaluate.
            total_days: Denominator for the percentage calculation.

        Returns:
            Score in [0, 100].
        """
        if total_days == 0:
            return 0.0
        days_completed = sum(1 for r in records if r.exercise_completed == "Yes")
        return (days_completed / total_days) * 100.0

    def _calculate_step_compliance(
        self,
        records: List[PatientRecord],
    ) -> float:
        """
        Step compliance: average ratio of actual to expected steps, capped at 100%.

        Formula: min(100, avg(actual_steps / expected_steps) * 100)

        Records where expected_steps is 0 are excluded to avoid division by zero.
        If all records have expected_steps == 0 the score defaults to 100.

        Validates Requirement 6.3

        Args:
            records: Patient records to evaluate.

        Returns:
            Score in [0, 100].
        """
        valid = [r for r in records if r.expected_steps > 0]
        if not valid:
            # No prescribed goal — treat as fully compliant
            return 100.0

        ratios = [r.actual_steps / r.expected_steps for r in valid]
        avg_ratio = sum(ratios) / len(ratios)
        return min(100.0, avg_ratio * 100.0)

    def _calculate_sleep_compliance(
        self,
        records: List[PatientRecord],
    ) -> float:
        """
        Sleep compliance: 100 minus the average percentage deviation from the target.

        Formula: 100 - avg(|expected_sleep_hours - actual_sleep_hours|
                             / expected_sleep_hours × 100)

        Records where expected_sleep_hours is 0 are excluded to avoid division by zero.
        If all records have expected_sleep_hours == 0 the score defaults to 100.
        The result is clamped to [0, 100] so that large deviations never go negative.

        Validates Requirement 6.4

        Args:
            records: Patient records to evaluate.

        Returns:
            Score in [0, 100].
        """
        valid = [r for r in records if r.expected_sleep_hours > 0]
        if not valid:
            # No prescribed goal — treat as fully compliant
            return 100.0

        deviations = [
            abs(r.expected_sleep_hours - r.actual_sleep_hours)
            / r.expected_sleep_hours
            * 100.0
            for r in valid
        ]
        avg_deviation = sum(deviations) / len(deviations)
        return max(0.0, 100.0 - avg_deviation)

    def _calculate_diet_compliance(
        self,
        records: List[PatientRecord],
    ) -> float:
        """
        Diet compliance: average of the diet_compliance field.

        The diet_compliance field already stores a percentage in [0, 100].

        Validates Requirement 6.5

        Args:
            records: Patient records to evaluate.

        Returns:
            Score in [0, 100].
        """
        if not records:
            return 0.0
        total = sum(r.diet_compliance for r in records)
        return total / len(records)

    def _calculate_water_compliance(
        self,
        records: List[PatientRecord],
    ) -> float:
        """
        Water intake compliance: average ratio of actual to goal intake, capped at 100%.

        Formula: min(100, avg(water_intake / water_intake_goal) * 100)

        Records where water_intake_goal is 0 are excluded to avoid division by zero.
        If all records have water_intake_goal == 0 the score defaults to 100.

        Validates Requirement 6.6

        Args:
            records: Patient records to evaluate.

        Returns:
            Score in [0, 100].
        """
        valid = [r for r in records if r.water_intake_goal > 0]
        if not valid:
            # No prescribed goal — treat as fully compliant
            return 100.0

        ratios = [r.water_intake / r.water_intake_goal for r in valid]
        avg_ratio = sum(ratios) / len(ratios)
        return min(100.0, avg_ratio * 100.0)

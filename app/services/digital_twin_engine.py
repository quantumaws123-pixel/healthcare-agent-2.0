"""
Digital Twin Engine for Healthcare Agent 2.0 Backend ML System.

Compares the Ideal Twin (doctor's prescribed plan) against the Real Twin
(actual patient behaviour) to compute deviation metrics and health scores.

Validates Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from app.models.schemas import PatientRecord
from app.services.compliance_calculator import ComplianceCalculator
from app.services.health_score_calculator import HealthScoreCalculator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class DeviationMetrics:
    """
    Deviation metrics produced by comparing the Ideal Twin against the
    Real Twin for a single patient record.

    Attributes:
        step_deviation:           Absolute difference between expected and
                                  actual daily steps (Requirement 5.1).
        sleep_deviation:          Absolute difference (in hours) between
                                  expected and actual sleep (Requirement 5.2).
        water_deviation:          Absolute difference (in mL) between the
                                  water intake goal and actual intake
                                  (Requirement 5.3).
        medication_violation:     True when medication was NOT taken as
                                  prescribed (Requirement 5.4).
        exercise_violation:       True when exercise was NOT completed as
                                  prescribed (Requirement 5.5).
        overall_deviation_score:  Aggregate deviation expressed as a value
                                  in [0, 100] — 0 = perfect adherence,
                                  100 = maximum possible deviation
                                  (Requirement 5.6).
    """

    step_deviation: float
    sleep_deviation: float
    water_deviation: float
    medication_violation: bool
    exercise_violation: bool
    overall_deviation_score: float


@dataclass
class HealthScores:
    """
    Health scores derived from the Ideal and Real Twin comparison.

    Attributes:
        ideal_health_score:  Theoretical health score assuming perfect
                             adherence (Requirement 5.7).
        real_health_score:   Actual health score based on measured vitals
                             and observed behaviour (Requirement 5.8).
        deviation_score:     |ideal - real|, normalised to [0, 100].
        recovery_score:      Trajectory-based score reflecting whether the
                             patient is improving or declining.
    """

    ideal_health_score: float
    real_health_score: float
    deviation_score: float
    recovery_score: float


# ---------------------------------------------------------------------------
# Deviation-score component weights
# ---------------------------------------------------------------------------

# These weights govern how each behavioural deviation contributes to the
# aggregated overall_deviation_score.  They must sum to 1.0.

_MEDICATION_WEIGHT: float = 0.30   # matches ComplianceCalculator.MEDICATION_WEIGHT
_EXERCISE_WEIGHT: float = 0.20    # matches ComplianceCalculator.EXERCISE_WEIGHT
_STEPS_WEIGHT: float = 0.15       # matches ComplianceCalculator.STEPS_WEIGHT
_SLEEP_WEIGHT: float = 0.15       # matches ComplianceCalculator.SLEEP_WEIGHT
_DIET_WEIGHT: float = 0.10        # used implicitly via compliance_score
_WATER_WEIGHT: float = 0.10       # matches ComplianceCalculator.WATER_WEIGHT


class DigitalTwinEngine:
    """
    Compares the Ideal Twin against the Real Twin to compute deviation
    metrics and health scores for a patient.

    The engine delegates compliance scoring to ``ComplianceCalculator`` and
    health score computation to ``HealthScoreCalculator``, then aggregates
    their outputs into a unified deviation picture.

    Design (from design.md):
        - compute_deviations  → DeviationMetrics
        - compute_health_scores → HealthScores
    """

    def __init__(
        self,
        compliance_calculator: Optional[ComplianceCalculator] = None,
        health_score_calculator: Optional[HealthScoreCalculator] = None,
    ) -> None:
        """
        Initialise the engine with optional injected collaborators.

        If no collaborators are provided the engine creates its own default
        instances, which is convenient for unit tests and standalone usage.

        Args:
            compliance_calculator:    Strategy for computing compliance scores.
            health_score_calculator:  Strategy for computing health scores.
        """
        self._compliance_calculator = compliance_calculator or ComplianceCalculator()
        self._health_score_calculator = health_score_calculator or HealthScoreCalculator()

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    async def compute_deviations(
        self,
        patient_record: PatientRecord,
    ) -> DeviationMetrics:
        """
        Compute deviation metrics between the Ideal Twin and the Real Twin.

        Algorithm:
            1. step_deviation    = |expected_steps − actual_steps|
            2. sleep_deviation   = |expected_sleep_hours − actual_sleep_hours|
            3. water_deviation   = |water_intake_goal − water_intake|
            4. medication_violation = (medication_taken == "No")
            5. exercise_violation   = (exercise_completed == "No")
            6. overall_deviation_score = 100 − compliance_score
               where compliance_score is obtained from ComplianceCalculator
               using the single record wrapped in a list (Requirement 5.6).

        The overall_deviation_score is 0 when the patient is perfectly
        compliant and 100 when fully non-compliant.  It is computed from
        the existing ComplianceCalculator so that the deviation aggregation
        mirrors the same weighted scheme used for compliance scoring.

        Validates Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6

        Args:
            patient_record: Current patient data for a single day.

        Returns:
            DeviationMetrics instance populated with all deviation fields.
        """
        # --- Requirement 5.1: Step deviation --------------------------------
        step_deviation = abs(
            patient_record.expected_steps - patient_record.actual_steps
        )

        # --- Requirement 5.2: Sleep deviation --------------------------------
        sleep_deviation = abs(
            patient_record.expected_sleep_hours - patient_record.actual_sleep_hours
        )

        # --- Requirement 5.3: Water intake deviation -------------------------
        water_deviation = abs(
            patient_record.water_intake_goal - patient_record.water_intake
        )

        # --- Requirement 5.4: Medication compliance violation ----------------
        medication_violation = patient_record.medication_taken == "No"

        # --- Requirement 5.5: Exercise compliance violation ------------------
        exercise_violation = patient_record.exercise_completed == "No"

        # --- Requirement 5.6: Aggregate deviation score ---------------------
        # Delegate to ComplianceCalculator for a consistent weighted score,
        # then invert: deviation = 100 − compliance.
        compliance_score = await self._compliance_calculator.calculate_compliance_score(
            patient_records=[patient_record],
            window_days=1,
        )
        overall_deviation_score = max(0.0, min(100.0, 100.0 - compliance_score))

        metrics = DeviationMetrics(
            step_deviation=float(step_deviation),
            sleep_deviation=float(sleep_deviation),
            water_deviation=float(water_deviation),
            medication_violation=medication_violation,
            exercise_violation=exercise_violation,
            overall_deviation_score=overall_deviation_score,
        )

        logger.debug(
            "Deviations for patient %s: steps=%.0f, sleep=%.2fh, "
            "water=%.0fmL, medication_violation=%s, exercise_violation=%s, "
            "overall_deviation_score=%.2f",
            patient_record.patient_id,
            metrics.step_deviation,
            metrics.sleep_deviation,
            metrics.water_deviation,
            metrics.medication_violation,
            metrics.exercise_violation,
            metrics.overall_deviation_score,
        )

        return metrics

    async def compute_health_scores(
        self,
        patient_record: PatientRecord,
        historical_records: List[PatientRecord],
    ) -> HealthScores:
        """
        Compute Ideal, Real, Deviation, and Recovery health scores.

        Algorithm:
            1. ideal_health_score   = HealthScoreCalculator.calculate_ideal_health_score(record)
            2. real_health_score    = HealthScoreCalculator.calculate_real_health_score(record)
            3. deviation_score      = |ideal_health_score − real_health_score|
               Clamped to [0, 100] (Requirement 7.4).
            4. recovery_score       = HealthScoreCalculator.calculate_recovery_score(historical_records)

        Validates Requirements 5.7, 5.8

        Args:
            patient_record:      Current day's patient data.
            historical_records:  Ordered list of past records (ascending day)
                                 used for recovery trend analysis.  May be
                                 empty, in which case a neutral recovery
                                 score of 50 is returned.

        Returns:
            HealthScores instance with all four score fields populated.
        """
        ideal_health_score = await self._health_score_calculator.calculate_ideal_health_score(
            patient_record
        )
        real_health_score = await self._health_score_calculator.calculate_real_health_score(
            patient_record
        )

        # Deviation between the two twins (Requirement 7.4)
        deviation_score = max(0.0, min(100.0, abs(ideal_health_score - real_health_score)))

        # Recovery trajectory (Requirement 7.5)
        # Append the current record to historical data so the trend includes
        # today's real_health_score if it has been computed.
        records_for_trend: List[PatientRecord] = list(historical_records)

        # Temporarily attach the newly computed real_health_score to the
        # current record so the recovery calculator can use it.
        patched_record = patient_record.model_copy(
            update={"real_health_score": real_health_score}
        )
        records_for_trend.append(patched_record)

        recovery_score = await self._health_score_calculator.calculate_recovery_score(
            records_for_trend
        )

        scores = HealthScores(
            ideal_health_score=ideal_health_score,
            real_health_score=real_health_score,
            deviation_score=deviation_score,
            recovery_score=recovery_score,
        )

        logger.debug(
            "Health scores for patient %s: ideal=%.2f, real=%.2f, "
            "deviation=%.2f, recovery=%.2f",
            patient_record.patient_id,
            scores.ideal_health_score,
            scores.real_health_score,
            scores.deviation_score,
            scores.recovery_score,
        )

        return scores

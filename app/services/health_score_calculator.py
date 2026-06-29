"""
Health Score Calculator Service for Healthcare Agent 2.0 Backend ML System.

Computes Ideal Health Score, Real Health Score, and Recovery Score from patient
vitals, compliance metrics, and historical health trend data.

Validates Requirements 7.1, 7.2, 7.3, 7.5
"""

import logging
import math
from typing import List, Optional

from app.models.schemas import PatientRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Normal vital-sign ranges used for normalization
# Keys must match PatientRecord vital field names.
# Tuple format: (lower_bound, upper_bound)
# ---------------------------------------------------------------------------
VITAL_RANGES: dict[str, tuple[float, float]] = {
    "heart_rate": (60.0, 100.0),         # beats per minute
    "systolic_bp": (90.0, 120.0),        # mmHg
    "diastolic_bp": (60.0, 80.0),        # mmHg
    "spo2": (95.0, 100.0),               # %
    "respiratory_rate": (12.0, 20.0),    # breaths per minute
    "body_temperature": (36.1, 37.2),    # °C
}

# Optimal (midpoint) values derived from VITAL_RANGES
VITAL_OPTIMAL: dict[str, float] = {
    key: (low + high) / 2.0
    for key, (low, high) in VITAL_RANGES.items()
}

# Weights for each vital group used in calculate_real_health_score.
# Blood pressure (systolic + diastolic) is split to sum to 25%.
# Total must equal 1.0.
_VITAL_WEIGHTS: dict[str, float] = {
    "heart_rate": 0.20,
    "systolic_bp": 0.125,    # BP (25%) split evenly over systolic/diastolic
    "diastolic_bp": 0.125,
    "spo2": 0.20,
    "respiratory_rate": 0.15,
    "body_temperature": 0.20,
}

# Blend ratio between vitals sub-score and compliance sub-score
_VITALS_BLEND: float = 0.50    # 50% vitals
_COMPLIANCE_BLEND: float = 0.50  # 50% compliance


class HealthScoreCalculator:
    """
    Calculates normalized health scores based on patient vitals and recovery
    trajectory.

    Three scores are produced:

    * **Ideal Health Score** – theoretical score assuming the patient follows
      the doctor's plan perfectly (100 % compliance, vitals at optimal values).

    * **Real Health Score** – actual score derived from measured vitals and
      the patient's current compliance.

    * **Recovery Score** – trajectory score derived from linear regression over
      the most recent 7–30 days of Real Health Scores.

    All scores are on a 0–100 scale (Requirement 7.8).
    """

    # Expose the module-level constants as class attributes so callers can
    # reference them as ``HealthScoreCalculator.VITAL_RANGES``.
    VITAL_RANGES: dict[str, tuple[float, float]] = VITAL_RANGES

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    async def calculate_ideal_health_score(
        self,
        patient_record: PatientRecord,
    ) -> float:
        """
        Compute the Ideal Health Score assuming perfect patient adherence.

        The ideal state assumes:
        - Every vital is at its optimal (midpoint of normal range) value.
        - The patient is 100 % compliant with the prescribed plan.

        Because both components are at their theoretical maximum the Ideal
        Health Score will always be 100.0 unless the patient's demographics
        (age / disease type) apply a penalty in a future extension.  The
        current implementation returns 100.0 as the baseline ideal.

        Validates Requirement 7.1

        Args:
            patient_record: Current patient data (demographics used for
                future age-adjusted range lookups).

        Returns:
            Ideal health score in [0, 100].
        """
        # Vital sub-score: every vital at optimal → each individual score = 100
        ideal_vital_score = 100.0

        # Compliance sub-score: perfect adherence
        ideal_compliance_score = 100.0

        score = (
            ideal_vital_score * _VITALS_BLEND
            + ideal_compliance_score * _COMPLIANCE_BLEND
        )

        result = max(0.0, min(100.0, score))

        logger.debug(
            "Ideal health score for patient %s: %.2f",
            patient_record.patient_id,
            result,
        )

        return result

    async def calculate_real_health_score(
        self,
        patient_record: PatientRecord,
    ) -> float:
        """
        Compute the Real Health Score from actual vital measurements and
        the patient's compliance.

        Algorithm (Requirement 7.2, 7.3):
            1. For each vital, normalize against normal range:
                   vital_score = 100 × (1 − |actual − optimal| / range_width)
               Clamp each vital_score to [0, 100].
            2. Compute weighted vitals sub-score using ``_VITAL_WEIGHTS``.
               Weights: HR 20 %, BP 25 % (systolic 12.5 % + diastolic 12.5 %),
               SpO2 20 %, RR 15 %, Temp 20 %.
            3. Use compliance_score if already populated on the record,
               otherwise fall back to estimating compliance from the single
               record's fields.
            4. Blend: 50 % vitals sub-score + 50 % compliance sub-score.

        Validates Requirements 7.2, 7.3

        Args:
            patient_record: Current patient data with measured vitals.

        Returns:
            Real health score in [0, 100].
        """
        vitals_sub_score = self._compute_vitals_score(patient_record)
        compliance_sub_score = self._get_or_estimate_compliance(patient_record)

        score = (
            vitals_sub_score * _VITALS_BLEND
            + compliance_sub_score * _COMPLIANCE_BLEND
        )

        result = max(0.0, min(100.0, score))

        logger.debug(
            "Real health score for patient %s: %.2f "
            "(vitals=%.2f, compliance=%.2f)",
            patient_record.patient_id,
            result,
            vitals_sub_score,
            compliance_sub_score,
        )

        return result

    async def calculate_recovery_score(
        self,
        historical_records: List[PatientRecord],
    ) -> float:
        """
        Compute Recovery Score by analysing the trend of Real Health Scores
        over the most recent 7–30 days.

        Algorithm (Requirement 7.5):
            1. Extract real_health_score values from up to the last 30 records,
               filtering out any records where the value is None.
            2. If fewer than 2 data points are available, return a neutral
               baseline score of 50.0.
            3. Fit a simple linear regression (ordinary least squares) to the
               series using day index as the x-variable.
            4. Normalise the slope to a [0, 100] score:
               - A slope of 0 maps to 50 (neutral / stable).
               - A positive slope shifts the score above 50 (improving).
               - A negative slope shifts the score below 50 (declining).
               - Extreme slopes (≥ +10 or ≤ −10 per day) saturate at 100 / 0.

        Requirement notes:
            - 7.6: Improving trend → Recovery_Score increases above 50.
            - 7.7: Declining trend → Recovery_Score decreases below 50.
            - 7.8: Result is on a 0–100 scale.

        Args:
            historical_records: Ordered list of patient records (ascending day
                order).  Only records with a populated ``real_health_score``
                field are used.

        Returns:
            Recovery score in [0, 100].
        """
        # Collect (index, real_health_score) pairs from the tail of the window
        window = historical_records[-30:] if len(historical_records) > 30 else historical_records
        scores: List[tuple[float, float]] = []
        for i, record in enumerate(window):
            if record.real_health_score is not None:
                scores.append((float(i), record.real_health_score))

        if len(scores) < 2:
            logger.debug(
                "Insufficient data points (%d) for recovery score regression; "
                "returning baseline 50.0",
                len(scores),
            )
            return 50.0

        slope = _linear_regression_slope(scores)

        # Map slope → [0, 100]:
        #   slope = 0  →  50
        #   slope = +10 → 100 (saturates)
        #   slope = -10 →   0 (saturates)
        # Linear mapping: score = 50 + slope × 5  (clamped)
        recovery_score = 50.0 + slope * 5.0
        result = max(0.0, min(100.0, recovery_score))

        logger.debug(
            "Recovery score from %d records: slope=%.4f → score=%.2f",
            len(scores),
            slope,
            result,
        )

        return result

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _compute_vitals_score(self, patient_record: PatientRecord) -> float:
        """
        Compute a weighted vital-signs sub-score in [0, 100].

        For each vital:
            vital_score = 100 × max(0, 1 − |actual − optimal| / range_width)

        Then combine with weights defined in ``_VITAL_WEIGHTS``.

        Args:
            patient_record: Record containing the actual vital measurements.

        Returns:
            Weighted vitals score in [0, 100].
        """
        vital_field_values: dict[str, float] = {
            "heart_rate": float(patient_record.heart_rate),
            "systolic_bp": float(patient_record.systolic_bp),
            "diastolic_bp": float(patient_record.diastolic_bp),
            "spo2": float(patient_record.spo2),
            "respiratory_rate": float(patient_record.respiratory_rate),
            "body_temperature": float(patient_record.body_temperature),
        }

        weighted_sum = 0.0
        for vital_name, actual_value in vital_field_values.items():
            low, high = VITAL_RANGES[vital_name]
            optimal = VITAL_OPTIMAL[vital_name]
            range_width = high - low

            if range_width == 0.0:
                # Degenerate range — treat as perfect
                individual_score = 100.0
            else:
                deviation_ratio = abs(actual_value - optimal) / range_width
                individual_score = max(0.0, 100.0 * (1.0 - deviation_ratio))

            weight = _VITAL_WEIGHTS[vital_name]
            weighted_sum += individual_score * weight

        return max(0.0, min(100.0, weighted_sum))

    @staticmethod
    def _get_or_estimate_compliance(patient_record: PatientRecord) -> float:
        """
        Return the pre-computed compliance score if available, otherwise
        estimate it from a single record's behavioural fields.

        Single-record estimation uses a simplified weighted check:
            - Medication (30%): 100 if taken, 0 otherwise.
            - Exercise (20%): 100 if completed, 0 otherwise.
            - Steps (15%): min(100, actual/expected × 100) or 100 if no goal.
            - Sleep (15%): 100 − |expected − actual| / expected × 100.
            - Diet (10%): diet_compliance field directly.
            - Water (10%): min(100, intake/goal × 100) or 100 if no goal.

        Args:
            patient_record: Current patient record.

        Returns:
            Compliance score in [0, 100].
        """
        if patient_record.compliance_score is not None:
            return patient_record.compliance_score

        # Medication
        med = 100.0 if patient_record.medication_taken == "Yes" else 0.0

        # Exercise
        exc = 100.0 if patient_record.exercise_completed == "Yes" else 0.0

        # Steps
        if patient_record.expected_steps > 0:
            steps = min(
                100.0,
                (patient_record.actual_steps / patient_record.expected_steps) * 100.0,
            )
        else:
            steps = 100.0

        # Sleep
        if patient_record.expected_sleep_hours > 0:
            sleep_dev = (
                abs(patient_record.expected_sleep_hours - patient_record.actual_sleep_hours)
                / patient_record.expected_sleep_hours
                * 100.0
            )
            sleep = max(0.0, 100.0 - sleep_dev)
        else:
            sleep = 100.0

        # Diet
        diet = patient_record.diet_compliance

        # Water
        if patient_record.water_intake_goal > 0:
            water = min(
                100.0,
                (patient_record.water_intake / patient_record.water_intake_goal) * 100.0,
            )
        else:
            water = 100.0

        estimated = (
            med * 0.30
            + exc * 0.20
            + steps * 0.15
            + sleep * 0.15
            + diet * 0.10
            + water * 0.10
        )

        return max(0.0, min(100.0, estimated))


# ---------------------------------------------------------------------------
# Utility: simple OLS linear regression slope
# ---------------------------------------------------------------------------

def _linear_regression_slope(points: List[tuple[float, float]]) -> float:
    """
    Compute the slope of the best-fit line through ``points`` using ordinary
    least-squares regression.

    Args:
        points: List of (x, y) pairs.  Must contain at least 2 entries.

    Returns:
        Slope (Δy / Δx).  Returns 0.0 if all x-values are identical.
    """
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)

    denominator = n * sum_x2 - sum_x ** 2
    if math.isclose(denominator, 0.0, abs_tol=1e-9):
        return 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return slope

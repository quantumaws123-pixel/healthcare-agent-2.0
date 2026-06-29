"""
Prediction System Service for Healthcare Agent 2.0 Backend ML System.

Classifies recovery status using rule-based scoring and analyzes health trends
using linear regression over 7-day real_health_score time-series data.

Validates Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 9.1, 9.2, 9.3, 9.4, 9.5
"""

import logging
import math
from typing import List, Optional, TYPE_CHECKING

from app.models.schemas import PatientRecord

if TYPE_CHECKING:
    from app.ml.inference_engine import InferenceEngine

logger = logging.getLogger(__name__)


class PredictionSystem:
    """
    Classifies recovery status and analyzes health trends for patient monitoring.

    Responsibilities:
    - ``classify_recovery_status``: Maps (recovery_score, health_trend, risk_level)
      to one of six textual statuses using rule-based classification.
    - ``analyze_health_trend``: Fits a simple OLS regression over the last 7 days
      of ``real_health_score`` data and maps the slope to "Increasing", "Stable",
      or "Declining".
    - ``predict_readmission``: Delegates to the injected ``InferenceEngine``.

    Validates Requirements 8.1 – 8.6, 9.1 – 9.5
    """

    def __init__(self, inference_engine: Optional["InferenceEngine"] = None) -> None:
        """
        Args:
            inference_engine: Optional ML inference engine used by
                ``predict_readmission``.  May be ``None`` when only the
                rule-based methods are needed (e.g., in unit tests).
        """
        self.inference_engine = inference_engine

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def classify_recovery_status(
        self,
        recovery_score: float,
        health_trend: str,
        risk_level: str,
    ) -> str:
        """
        Classify a patient's recovery status from their recovery score, health
        trend direction, and current risk level.

        Classification rules (evaluated in priority order):

        1. **Critical** – ``recovery_score <= 15`` *or* ``risk_level == "Critical"``
           (Requirement 8.6)
        2. **Recovered** – ``recovery_score > 85`` *and*
           ``health_trend == "Increasing"`` (Requirement 8.1)
        3. **Improving** – ``70 < recovery_score <= 85`` *and*
           ``health_trend == "Increasing"`` (Requirement 8.2)
        4. **Stable** – ``50 < recovery_score <= 70`` *and*
           ``health_trend == "Stable"`` (Requirement 8.3)
        5. **Delayed Recovery** – ``30 < recovery_score <= 50`` *and*
           ``health_trend == "Declining"`` (Requirement 8.4)
        6. **Worsening** – ``15 < recovery_score <= 30`` *and*
           ``health_trend == "Declining"`` (Requirement 8.5)
        7. **Stable** – catch-all fallback for scores/trends that do not match
           the above rules precisely.

        Args:
            recovery_score: Numeric recovery score on a 0–100 scale.
            health_trend: One of ``"Increasing"``, ``"Stable"``, or
                ``"Declining"``.
            risk_level: One of ``"Low"``, ``"Medium"``, ``"High"``, or
                ``"Critical"``.

        Returns:
            Recovery status string: one of ``"Recovered"``, ``"Improving"``,
            ``"Stable"``, ``"Delayed Recovery"``, ``"Worsening"``, or
            ``"Critical"``.
        """
        # Rule 1: Critical takes precedence over all other rules (Req 8.6)
        if recovery_score <= 15 or risk_level == "Critical":
            status = "Critical"

        # Rule 2: Recovered (Req 8.1)
        elif recovery_score > 85 and health_trend == "Increasing":
            status = "Recovered"

        # Rule 3: Improving (Req 8.2)
        elif 70 < recovery_score <= 85 and health_trend == "Increasing":
            status = "Improving"

        # Rule 4: Stable (Req 8.3)
        elif 50 < recovery_score <= 70 and health_trend == "Stable":
            status = "Stable"

        # Rule 5: Delayed Recovery (Req 8.4)
        elif 30 < recovery_score <= 50 and health_trend == "Declining":
            status = "Delayed Recovery"

        # Rule 6: Worsening (Req 8.5)
        elif 15 < recovery_score <= 30 and health_trend == "Declining":
            status = "Worsening"

        # Rule 7: Catch-all — score and trend combination not covered by the
        # six primary rules; default to "Stable" as the most neutral label.
        else:
            status = "Stable"

        logger.debug(
            "classify_recovery_status: score=%.2f, trend=%s, risk=%s → %s",
            recovery_score,
            health_trend,
            risk_level,
            status,
        )

        return status

    async def analyze_health_trend(
        self,
        historical_records: List[PatientRecord],
    ) -> str:
        """
        Analyze the direction of a patient's health over the last 7 days using
        linear regression on ``real_health_score`` data.

        Algorithm (Requirements 9.1 – 9.5):
            1. Take the most recent 7 records from ``historical_records``.
            2. Filter to those that have a non-``None`` ``real_health_score``.
            3. If fewer than 3 valid data points remain, return ``"Stable"``
               (Requirement 9.5).
            4. Fit a simple OLS regression (day index as *x*,
               ``real_health_score`` as *y*) and compute the slope.
            5. Classify the slope:
               - slope > 1.0  → ``"Increasing"``  (Requirement 9.2)
               - −1.0 ≤ slope ≤ 1.0  → ``"Stable"``  (Requirement 9.3)
               - slope < −1.0  → ``"Declining"``  (Requirement 9.4)

        Args:
            historical_records: Ordered list of patient records in ascending
                day order.  Only the last 7 entries are examined.  Records
                without a ``real_health_score`` value are ignored.

        Returns:
            ``"Increasing"``, ``"Stable"``, or ``"Declining"``.
        """
        # Step 1: take the most recent 7 records
        recent_window: List[PatientRecord] = (
            historical_records[-7:]
            if len(historical_records) > 7
            else historical_records
        )

        # Step 2: collect valid (index, real_health_score) pairs
        points: List[tuple[float, float]] = []
        for idx, record in enumerate(recent_window):
            if record.real_health_score is not None:
                points.append((float(idx), record.real_health_score))

        # Step 3: edge case — fewer than 3 data points (Req 9.5)
        if len(points) < 3:
            logger.debug(
                "analyze_health_trend: only %d valid data points available "
                "(need ≥ 3); defaulting to 'Stable'",
                len(points),
            )
            return "Stable"

        # Step 4: compute OLS slope
        slope = _linear_regression_slope(points)

        # Step 5: classify slope into trend label
        if slope > 1.0:
            trend = "Increasing"
        elif slope < -1.0:
            trend = "Declining"
        else:
            trend = "Stable"

        logger.debug(
            "analyze_health_trend: %d data points, slope=%.4f → %s",
            len(points),
            slope,
            trend,
        )

        return trend

    async def predict_readmission(self, patient_record: PatientRecord):
        """
        Generate a readmission prediction by delegating to the injected
        ``InferenceEngine``.

        Args:
            patient_record: Current patient data.

        Returns:
            ``PredictionResult`` from the inference engine.

        Raises:
            RuntimeError: If no inference engine was provided at construction.
        """
        if self.inference_engine is None:
            raise RuntimeError(
                "PredictionSystem requires an InferenceEngine to call "
                "predict_readmission.  Provide one at construction time."
            )
        return await self.inference_engine.predict(patient_record)


# ---------------------------------------------------------------------------
# Module-level utility: simple OLS linear regression slope
# ---------------------------------------------------------------------------


def _linear_regression_slope(points: List[tuple[float, float]]) -> float:
    """
    Compute the OLS slope of the best-fit line through *points*.

    Uses the closed-form formula:

        slope = (n·Σxy − Σx·Σy) / (n·Σx² − (Σx)²)

    Returns 0.0 if the denominator is effectively zero (all x-values
    identical, which can occur with a single repeated day index).

    Args:
        points: List of (x, y) pairs.  Must contain at least 2 entries.

    Returns:
        Slope value (Δy / Δx).
    """
    n = len(points)
    sum_x: float = sum(p[0] for p in points)
    sum_y: float = sum(p[1] for p in points)
    sum_xy: float = sum(p[0] * p[1] for p in points)
    sum_x2: float = sum(p[0] ** 2 for p in points)

    denominator = n * sum_x2 - sum_x ** 2
    if math.isclose(denominator, 0.0, abs_tol=1e-9):
        return 0.0

    return (n * sum_xy - sum_x * sum_y) / denominator

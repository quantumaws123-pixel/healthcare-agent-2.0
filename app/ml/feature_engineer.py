"""Feature engineering and transformations for Healthcare Agent 2.0 Backend ML System.

This module implements the data transformation pipeline for preparing patient
records for ML model training and inference.  It is responsible for:

- Missing value imputation (median for numerical, mode for categorical).
- One-hot encoding for categorical variables (Gender, Disease_Type,
  Smoking_Status, Alcohol_Consumption).
- Min-max and z-score normalization of numerical features.
- Derived feature creation (compliance_score, deviation_score, health_trend,
  recovery_score) by delegating to the corresponding service classes.

The ``FeatureEngineer`` class exposes both a stateful *fit/transform* API
(suitable for training pipelines) and a stateless *transform* API that
applies a previously fitted state to new inference data.

**Validates: Requirements 11.2, 11.3, 11.4, 11.5**
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Categorical columns that receive one-hot encoding (Requirement 11.3)
CATEGORICAL_COLUMNS: list[str] = [
    "gender",
    "disease_type",
    "smoking_status",
    "alcohol_consumption",
    "medication_taken",
    "exercise_completed",
]

#: Numerical columns subject to normalization (Requirement 11.4).
#: These are the raw vitals and plan-vs-actual behavioural columns.
NUMERICAL_COLUMNS: list[str] = [
    "age",
    "bmi",
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "respiratory_rate",
    "body_temperature",
    "expected_steps",
    "expected_sleep_hours",
    "water_intake_goal",
    "actual_steps",
    "actual_sleep_hours",
    "water_intake",
    "diet_compliance",
]

#: Derived score columns created during feature engineering (Requirement 11.5).
DERIVED_COLUMNS: list[str] = [
    "compliance_score",
    "deviation_score",
    "health_trend_encoded",
    "recovery_score",
]

# ---------------------------------------------------------------------------
# Imputation helpers
# ---------------------------------------------------------------------------


def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply missing value imputation to a copy of *df*.

    Strategy (Requirement 11.2):
    - **Numerical columns**: replace ``NaN`` with the column median.
    - **Categorical columns**: replace ``NaN`` with the column mode (most
      frequent value).  If the column is entirely ``NaN`` the value ``"Unknown"``
      is used as a safe fallback.

    The function operates on a *copy* of the input DataFrame so the original
    is not mutated.

    Args:
        df: Raw patient records as a DataFrame.

    Returns:
        DataFrame with missing values filled.

    **Validates: Requirements 11.2**
    """
    df = df.copy()

    for col in df.columns:
        if df[col].isna().any():
            if col in CATEGORICAL_COLUMNS or df[col].dtype == object:
                # Mode imputation for categorical
                mode_series = df[col].mode()
                fill_value: Any = mode_series.iloc[0] if not mode_series.empty else "Unknown"
                df[col] = df[col].fillna(fill_value)
                logger.debug("Imputed categorical column '%s' with mode '%s'.", col, fill_value)
            else:
                # Median imputation for numerical
                median_value: float = float(df[col].median())
                df[col] = df[col].fillna(median_value)
                logger.debug("Imputed numerical column '%s' with median %.4f.", col, median_value)

    return df


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------


def one_hot_encode(
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
    known_categories: Optional[dict[str, list[str]]] = None,
) -> pd.DataFrame:
    """
    Apply one-hot encoding to the specified categorical columns.

    Each input category value produces a binary column named
    ``{original_column}_{value}`` (e.g. ``gender_Male``, ``gender_Female``).
    The original column is dropped after encoding.

    When *known_categories* is provided (i.e. during inference when the
    encoder state from training is available), the function ensures that the
    resulting DataFrame contains exactly the expected dummy columns regardless
    of which categories appear in this particular batch.  Missing categories
    are added as zero-filled columns; extra categories are dropped.

    Args:
        df: Input DataFrame.
        columns: List of column names to encode.  Defaults to
            :data:`CATEGORICAL_COLUMNS`.
        known_categories: Mapping from column name to the ordered list of
            category values that were seen during training.  Pass ``None``
            during training (fit phase) and supply the fitted mapping during
            inference (transform phase).

    Returns:
        DataFrame with categorical columns replaced by one-hot columns.

    **Validates: Requirements 11.3**
    """
    if columns is None:
        columns = CATEGORICAL_COLUMNS

    df = df.copy()

    for col in columns:
        if col not in df.columns:
            logger.warning("Column '%s' not found in DataFrame; skipping encoding.", col)
            continue

        if known_categories and col in known_categories:
            # Inference mode: align to the training-time categories
            categories = known_categories[col]
            # Create a Categorical with the known categories so pd.get_dummies
            # produces one column per training-time category
            df[col] = pd.Categorical(df[col], categories=categories)

        dummies = pd.get_dummies(df[col], prefix=col)

        if known_categories and col in known_categories:
            # Ensure all expected columns exist (fill unseen with 0)
            expected_cols = [f"{col}_{cat}" for cat in known_categories[col]]
            for expected in expected_cols:
                if expected not in dummies.columns:
                    dummies[expected] = 0
            # Keep only the expected columns in training order
            dummies = dummies[expected_cols]

        df = df.drop(columns=[col])
        df = pd.concat([df, dummies], axis=1)

        logger.debug("One-hot encoded column '%s' into %d dummy columns.", col, len(dummies.columns))

    return df

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def minmax_normalize(
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
    feature_ranges: Optional[dict[str, tuple[float, float]]] = None,
) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
    """
    Apply min-max normalization to numerical columns, scaling each to [0, 1].

    Formula for each value *x* in column *c*:

        x_norm = (x - min_c) / (max_c - min_c)

    When ``max_c == min_c`` (constant column) the output is set to ``0.5``
    rather than dividing by zero.

    When *feature_ranges* is provided the supplied ranges are used instead of
    computing them from the data.  This is required during inference to apply
    the same scaling that was fitted on training data.

    Args:
        df: Input DataFrame.  All specified columns must be numeric.
        columns: Columns to normalize.  Defaults to :data:`NUMERICAL_COLUMNS`.
        feature_ranges: Pre-computed ``{column: (min, max)}`` mapping from a
            previous fit.  Pass ``None`` during training.

    Returns:
        Tuple of:
        - Normalized DataFrame (copy of input with specified columns scaled).
        - Fitted ``feature_ranges`` dict (same as input if provided; newly
          computed from data otherwise).

    **Validates: Requirements 11.4**
    """
    if columns is None:
        columns = NUMERICAL_COLUMNS

    df = df.copy()
    fitted_ranges: dict[str, tuple[float, float]] = {}

    for col in columns:
        if col not in df.columns:
            logger.debug("Column '%s' not found for min-max normalization; skipping.", col)
            continue

        if feature_ranges and col in feature_ranges:
            col_min, col_max = feature_ranges[col]
        else:
            col_min = float(df[col].min())
            col_max = float(df[col].max())

        fitted_ranges[col] = (col_min, col_max)
        col_range = col_max - col_min

        if math.isclose(col_range, 0.0, abs_tol=1e-9):
            # Constant feature — set to 0.5 (neutral midpoint)
            df[col] = 0.5
            logger.debug("Column '%s' is constant (min=max=%.4f); set to 0.5.", col, col_min)
        else:
            df[col] = (df[col] - col_min) / col_range

    return df, fitted_ranges


def zscore_normalize(
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
    feature_stats: Optional[dict[str, tuple[float, float]]] = None,
) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
    """
    Apply z-score normalization to numerical columns.

    Formula for each value *x* in column *c*:

        x_norm = (x - mean_c) / std_c

    When ``std_c == 0`` (constant column) the output is set to ``0.0``.

    When *feature_stats* is provided the supplied mean/std values are used
    instead of computing them from the data (inference-time usage).

    Args:
        df: Input DataFrame.  All specified columns must be numeric.
        columns: Columns to normalize.  Defaults to :data:`NUMERICAL_COLUMNS`.
        feature_stats: Pre-computed ``{column: (mean, std)}`` mapping.
            Pass ``None`` during training.

    Returns:
        Tuple of:
        - Normalized DataFrame.
        - Fitted ``feature_stats`` dict ``{column: (mean, std)}``.

    **Validates: Requirements 11.4**
    """
    if columns is None:
        columns = NUMERICAL_COLUMNS

    df = df.copy()
    fitted_stats: dict[str, tuple[float, float]] = {}

    for col in columns:
        if col not in df.columns:
            logger.debug("Column '%s' not found for z-score normalization; skipping.", col)
            continue

        if feature_stats and col in feature_stats:
            col_mean, col_std = feature_stats[col]
        else:
            col_mean = float(df[col].mean())
            col_std = float(df[col].std(ddof=0))

        fitted_stats[col] = (col_mean, col_std)

        if math.isclose(col_std, 0.0, abs_tol=1e-9):
            df[col] = 0.0
            logger.debug("Column '%s' has std≈0 (mean=%.4f); set to 0.0.", col, col_mean)
        else:
            df[col] = (df[col] - col_mean) / col_std

    return df, fitted_stats

# ---------------------------------------------------------------------------
# Derived feature creation helpers
# ---------------------------------------------------------------------------

#: Weights used for the inline compliance estimation (mirrors ComplianceCalculator)
_COMPLIANCE_WEIGHTS: dict[str, float] = {
    "medication": 0.30,
    "exercise": 0.20,
    "steps": 0.15,
    "sleep": 0.15,
    "diet": 0.10,
    "water": 0.10,
}

#: Mapping from textual health_trend labels to a numeric encoding for ML models
HEALTH_TREND_ENCODING: dict[str, float] = {
    "Declining": -1.0,
    "Stable": 0.0,
    "Increasing": 1.0,
}


def _estimate_compliance_score(row: pd.Series) -> float:
    """Estimate compliance score from a single patient row."""
    # Use pre-computed value if available
    if pd.notna(row.get("compliance_score")):
        val = float(row["compliance_score"])
        if 0.0 <= val <= 100.0:
            return val

    med = 100.0 if row.get("medication_taken") == "Yes" else 0.0
    exc = 100.0 if row.get("exercise_completed") == "Yes" else 0.0

    expected_steps = float(row.get("expected_steps") or 0)
    actual_steps = float(row.get("actual_steps") or 0)
    steps = min(100.0, (actual_steps / expected_steps) * 100.0) if expected_steps > 0 else 100.0

    expected_sleep = float(row.get("expected_sleep_hours") or 0)
    actual_sleep = float(row.get("actual_sleep_hours") or 0)
    if expected_sleep > 0:
        sleep_dev = abs(expected_sleep - actual_sleep) / expected_sleep * 100.0
        sleep = max(0.0, 100.0 - sleep_dev)
    else:
        sleep = 100.0

    diet = float(row.get("diet_compliance") or 0)

    water_goal = float(row.get("water_intake_goal") or 0)
    water_intake = float(row.get("water_intake") or 0)
    water = min(100.0, (water_intake / water_goal) * 100.0) if water_goal > 0 else 100.0

    score = (
        med * _COMPLIANCE_WEIGHTS["medication"]
        + exc * _COMPLIANCE_WEIGHTS["exercise"]
        + steps * _COMPLIANCE_WEIGHTS["steps"]
        + sleep * _COMPLIANCE_WEIGHTS["sleep"]
        + diet * _COMPLIANCE_WEIGHTS["diet"]
        + water * _COMPLIANCE_WEIGHTS["water"]
    )
    return max(0.0, min(100.0, score))


def _estimate_deviation_score(row: pd.Series) -> float:
    """Estimate deviation score from ideal vs actual values in a single row."""
    if pd.notna(row.get("deviation_score")):
        val = float(row["deviation_score"])
        if 0.0 <= val <= 100.0:
            return val

    deviations: list[float] = []

    # Steps deviation (normalised per 10 000 steps)
    expected_steps = float(row.get("expected_steps") or 0)
    actual_steps = float(row.get("actual_steps") or 0)
    if expected_steps > 0:
        deviations.append(min(100.0, abs(expected_steps - actual_steps) / expected_steps * 100.0))

    # Sleep deviation
    expected_sleep = float(row.get("expected_sleep_hours") or 0)
    actual_sleep = float(row.get("actual_sleep_hours") or 0)
    if expected_sleep > 0:
        deviations.append(min(100.0, abs(expected_sleep - actual_sleep) / expected_sleep * 100.0))

    # Water deviation
    water_goal = float(row.get("water_intake_goal") or 0)
    water_intake = float(row.get("water_intake") or 0)
    if water_goal > 0:
        deviations.append(min(100.0, abs(water_goal - water_intake) / water_goal * 100.0))

    # Medication non-compliance adds 100% deviation
    if row.get("medication_taken") == "No":
        deviations.append(100.0)
    else:
        deviations.append(0.0)

    # Exercise non-compliance adds 100% deviation
    if row.get("exercise_completed") == "No":
        deviations.append(100.0)
    else:
        deviations.append(0.0)

    if not deviations:
        return 0.0

    return max(0.0, min(100.0, sum(deviations) / len(deviations)))

def _compute_ols_slope(x: list[float], y: list[float]) -> float:
    """Compute the OLS regression slope for paired x, y lists."""
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    denom = n * sum_x2 - sum_x ** 2
    if math.isclose(denom, 0.0, abs_tol=1e-9):
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denom


def _classify_health_trend(slope: float, n_points: int) -> str:
    """Map an OLS slope to a health trend label (Requirements 9.2–9.5)."""
    if n_points < 3:
        return "Stable"
    if slope > 1.0:
        return "Increasing"
    if slope < -1.0:
        return "Declining"
    return "Stable"


def _estimate_health_trend_for_group(group: pd.DataFrame) -> pd.Series:
    """
    Compute health_trend and health_trend_encoded for a patient group sorted by day.

    Uses the last 7 real_health_score values available per patient.
    Returns a Series of health_trend_encoded values aligned to the group index.
    """
    group = group.sort_values("day") if "day" in group.columns else group

    # Use real_health_score if present, else fall back to zeros
    if "real_health_score" in group.columns:
        scores = group["real_health_score"].dropna().tolist()
    else:
        scores = []

    # Build running 7-day window for each row
    encoded_values: list[float] = []
    for i in range(len(group)):
        window_scores = scores[max(0, i - 6): i + 1]
        if len(window_scores) < 3:
            trend = "Stable"
        else:
            x = list(range(len(window_scores)))
            slope = _compute_ols_slope(x, window_scores)
            trend = _classify_health_trend(slope, len(window_scores))
        encoded_values.append(HEALTH_TREND_ENCODING[trend])

    return pd.Series(encoded_values, index=group.index)


def _estimate_recovery_score_for_group(group: pd.DataFrame) -> pd.Series:
    """
    Compute recovery_score for each row in a patient group using the last 30
    real_health_score values (mirrors HealthScoreCalculator.calculate_recovery_score).
    """
    group = group.sort_values("day") if "day" in group.columns else group

    if "real_health_score" in group.columns:
        scores = group["real_health_score"].dropna().tolist()
    else:
        scores = []

    recovery_values: list[float] = []
    for i in range(len(group)):
        # Take at most 30 previous scores up to this row
        window = scores[max(0, i - 29): i + 1]
        valid = [(float(j), s) for j, s in enumerate(window)]

        if len(valid) < 2:
            recovery_values.append(50.0)
        else:
            x = [p[0] for p in valid]
            y = [p[1] for p in valid]
            slope = _compute_ols_slope(x, y)
            # Score: 50 + slope * 5, clamped to [0, 100]
            recovery = max(0.0, min(100.0, 50.0 + slope * 5.0))
            recovery_values.append(recovery)

    return pd.Series(recovery_values, index=group.index)


def create_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived features (compliance_score, deviation_score,
    health_trend_encoded, recovery_score) and add them to the DataFrame.

    Existing column values are used when already populated; otherwise they
    are estimated from the raw behavioural fields.

    Health trend and recovery score require per-patient temporal context.
    When a ``patient_id`` column is present the records are grouped by patient
    and processed in day order.  When absent, each row is processed as an
    independent single-record patient.

    Args:
        df: Input DataFrame that must contain the raw behavioural fields.

    Returns:
        DataFrame with the four derived columns added (or updated).

    **Validates: Requirements 11.5**
    """
    df = df.copy()

    # --- compliance_score ---------------------------------------------------
    if "compliance_score" not in df.columns:
        df["compliance_score"] = np.nan
    df["compliance_score"] = df.apply(_estimate_compliance_score, axis=1)

    # --- deviation_score ----------------------------------------------------
    if "deviation_score" not in df.columns:
        df["deviation_score"] = np.nan
    df["deviation_score"] = df.apply(_estimate_deviation_score, axis=1)

    # --- health_trend_encoded and recovery_score (per-patient, temporal) ----
    if "health_trend_encoded" not in df.columns:
        df["health_trend_encoded"] = np.nan
    if "recovery_score" not in df.columns:
        df["recovery_score"] = np.nan

    if "patient_id" in df.columns:
        for pid, group in df.groupby("patient_id", sort=False):
            trend_encoded = _estimate_health_trend_for_group(group)
            df.loc[group.index, "health_trend_encoded"] = trend_encoded

            recovery = _estimate_recovery_score_for_group(group)
            df.loc[group.index, "recovery_score"] = recovery
    else:
        # No patient grouping available — treat each row independently
        df["health_trend_encoded"] = HEALTH_TREND_ENCODING["Stable"]
        df["recovery_score"] = 50.0

    logger.debug(
        "Derived features created for %d records. "
        "compliance_score: mean=%.2f, deviation_score: mean=%.2f, "
        "recovery_score: mean=%.2f",
        len(df),
        df["compliance_score"].mean(),
        df["deviation_score"].mean(),
        df["recovery_score"].mean(),
    )

    return df

# ---------------------------------------------------------------------------
# FeatureEngineer: stateful fit/transform pipeline
# ---------------------------------------------------------------------------


class FeatureEngineer:
    """
    Stateful feature engineering pipeline for ML training and inference.

    The workflow is:

    1. **Fit** (training time): Call :meth:`fit_transform` with the training
       DataFrame to impute, encode, normalize, and add derived features.
       The fitted state (category lists, normalization params) is stored on
       the instance.

    2. **Transform** (inference time): Call :meth:`transform` with new data
       to apply the same transformations using the fitted state.

    The ``normalization`` parameter selects the scaling strategy:
    - ``"minmax"`` (default): scales each numerical feature to [0, 1].
    - ``"zscore"``: standardises each feature to zero mean and unit variance.

    **Validates: Requirements 11.2, 11.3, 11.4, 11.5**

    Example::

        fe = FeatureEngineer(normalization="minmax")
        train_features = fe.fit_transform(train_df)
        inference_features = fe.transform(new_df)
    """

    def __init__(self, normalization: str = "minmax") -> None:
        """
        Args:
            normalization: Scaling strategy.  One of ``"minmax"`` or
                ``"zscore"``.

        Raises:
            ValueError: If *normalization* is not a supported strategy.
        """
        if normalization not in ("minmax", "zscore"):
            raise ValueError(
                f"Unsupported normalization strategy '{normalization}'. "
                "Choose 'minmax' or 'zscore'."
            )
        self.normalization: str = normalization

        # Fitted state — populated by fit_transform()
        self._is_fitted: bool = False
        self._known_categories: dict[str, list[str]] = {}
        self._minmax_ranges: dict[str, tuple[float, float]] = {}
        self._zscore_stats: dict[str, tuple[float, float]] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit the pipeline on *df* and return the transformed DataFrame.

        Steps:
        1. :func:`impute_missing_values` – fill NaN values.
        2. :func:`create_derived_features` – compute compliance, deviation,
           health trend, and recovery score.
        3. Record known category values for each categorical column.
        4. :func:`one_hot_encode` – encode categorical columns.
        5. Normalization – scale numerical columns according to the chosen
           strategy.

        Args:
            df: Training DataFrame.

        Returns:
            Transformed feature DataFrame ready for ML training.
        """
        logger.info("FeatureEngineer.fit_transform: processing %d records.", len(df))

        # Step 1: Impute
        df = impute_missing_values(df)

        # Step 2: Derived features (before encoding, so categorical fields exist)
        df = create_derived_features(df)

        # Step 3: Record known categories for reproducible encoding
        self._known_categories = {}
        for col in CATEGORICAL_COLUMNS:
            if col in df.columns:
                self._known_categories[col] = sorted(df[col].dropna().unique().tolist())

        # Step 4: One-hot encode
        df = one_hot_encode(df, columns=CATEGORICAL_COLUMNS)

        # Step 5: Normalize numerical columns
        df = self._apply_normalization(df, fit=True)

        self._is_fitted = True
        logger.info("FeatureEngineer.fit_transform complete. Output shape: %s", df.shape)
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the fitted pipeline transformations to new data.

        Must be called *after* :meth:`fit_transform`.

        Args:
            df: New data to transform.

        Returns:
            Transformed feature DataFrame aligned with the training schema.

        Raises:
            RuntimeError: If called before :meth:`fit_transform`.
        """
        if not self._is_fitted:
            raise RuntimeError(
                "FeatureEngineer.transform() called before fit_transform(). "
                "Call fit_transform() on training data first."
            )
        logger.info("FeatureEngineer.transform: processing %d records.", len(df))

        # Step 1: Impute
        df = impute_missing_values(df)

        # Step 2: Derived features
        df = create_derived_features(df)

        # Step 3: One-hot encode using known (training) categories
        df = one_hot_encode(
            df,
            columns=CATEGORICAL_COLUMNS,
            known_categories=self._known_categories,
        )

        # Step 4: Normalize using fitted parameters
        df = self._apply_normalization(df, fit=False)

        logger.info("FeatureEngineer.transform complete. Output shape: %s", df.shape)
        return df

    @property
    def is_fitted(self) -> bool:
        """``True`` once :meth:`fit_transform` has been called successfully."""
        return self._is_fitted

    @property
    def known_categories(self) -> dict[str, list[str]]:
        """Category lists per column discovered during training."""
        return dict(self._known_categories)

    @property
    def minmax_ranges(self) -> dict[str, tuple[float, float]]:
        """Min-max ranges per column fitted during training."""
        return dict(self._minmax_ranges)

    @property
    def zscore_stats(self) -> dict[str, tuple[float, float]]:
        """Mean and std per column fitted during training."""
        return dict(self._zscore_stats)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_normalization(self, df: pd.DataFrame, *, fit: bool) -> pd.DataFrame:
        """Apply the configured normalization strategy."""
        if self.normalization == "minmax":
            ranges = None if fit else self._minmax_ranges
            df, fitted = minmax_normalize(df, feature_ranges=ranges)
            if fit:
                self._minmax_ranges = fitted
        else:  # zscore
            stats = None if fit else self._zscore_stats
            df, fitted = zscore_normalize(df, feature_stats=stats)
            if fit:
                self._zscore_stats = fitted
        return df

"""Inference-time feature preprocessing for Healthcare Agent 2.0 Backend ML System.

This module provides the :class:`FeaturePreprocessor` class, which applies the
same scaling and encoding transformations at inference time that were fitted on
training data.  It is the inference-facing counterpart to
:class:`app.ml.feature_engineer.FeatureEngineer`.

Responsibilities
----------------
- **apply_scaling**: applies min-max or z-score normalization using
  parameters that were fit on training data.
- **apply_encoding**: applies one-hot encoding aligned to the
  category lists that were observed during training.
- **save / load**: serializes and deserializes the full preprocessing
  pipeline state to/from disk with :mod:`joblib`.

Consistency guarantee
~~~~~~~~~~~~~~~~~~~~~
All transformations delegate to the lower-level helpers already implemented in
:mod:`app.ml.feature_engineer`::

    minmax_normalize, zscore_normalize, one_hot_encode, impute_missing_values,
    create_derived_features

This ensures that training and inference always use identical transformation
logic (Requirement 4.7).

Typical usage
~~~~~~~~~~~~~
**Training side** (create and fit via :class:`~app.ml.feature_engineer.FeatureEngineer`)::

    from app.ml.feature_engineer import FeatureEngineer
    from app.ml.feature_preprocessor import FeaturePreprocessor

    fe = FeatureEngineer(normalization="minmax")
    fe.fit_transform(train_df)

    # Persist for later inference use
    preprocessor = FeaturePreprocessor.from_feature_engineer(fe)
    preprocessor.save("/path/to/preprocessor.joblib")

**Inference side** (load and apply)::

    preprocessor = FeaturePreprocessor.load("/path/to/preprocessor.joblib")
    feature_matrix = preprocessor.transform(new_df)

**Validates: Requirement 4.7**
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import joblib

from app.ml.feature_engineer import (
    CATEGORICAL_COLUMNS,
    NUMERICAL_COLUMNS,
    impute_missing_values,
    one_hot_encode,
    minmax_normalize,
    zscore_normalize,
    create_derived_features,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Default filename used when a directory path is given to save/load.
DEFAULT_PREPROCESSOR_FILENAME = "feature_preprocessor.joblib"

#: Supported normalization strategies.
SUPPORTED_NORMALIZATIONS = ("minmax", "zscore")


# ---------------------------------------------------------------------------
# FeaturePreprocessor
# ---------------------------------------------------------------------------


class FeaturePreprocessor:
    """
    Inference-time feature preprocessor that applies training-fitted transformations.

    The instance stores three pieces of fitted state that are captured at
    training time and must be reused exactly at inference time:

    ``normalization``
        Either ``"minmax"`` or ``"zscore"``.

    ``_known_categories``
        Mapping from categorical column name to the ordered list of category
        values seen during training.  Used by :meth:`apply_encoding` to
        guarantee the same dummy-column layout.

    ``_scaling_params``
        For **min-max**: ``{column: (min, max)}``.
        For **z-score**: ``{column: (mean, std)}``.

    **Validates: Requirement 4.7**

    Example::

        preprocessor = FeaturePreprocessor.load("preprocessor.joblib")
        features_df = preprocessor.transform(raw_df)
        X = features_df.to_numpy()
    """

    def __init__(
        self,
        normalization: str = "minmax",
        known_categories: Optional[dict[str, list[str]]] = None,
        scaling_params: Optional[dict[str, tuple[float, float]]] = None,
    ) -> None:
        """
        Args:
            normalization: Scaling strategy — ``"minmax"`` or ``"zscore"``.
            known_categories: Category lists per column from training.
            scaling_params: Fitted min/max ranges (minmax) or mean/std values
                (zscore) per numerical column.

        Raises:
            ValueError: If *normalization* is not a supported strategy.
        """
        if normalization not in SUPPORTED_NORMALIZATIONS:
            raise ValueError(
                f"Unsupported normalization strategy '{normalization}'. "
                f"Choose one of {SUPPORTED_NORMALIZATIONS}."
            )

        self.normalization: str = normalization
        self._known_categories: dict[str, list[str]] = known_categories or {}
        self._scaling_params: dict[str, tuple[float, float]] = scaling_params or {}

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_feature_engineer(cls, feature_engineer: Any) -> "FeaturePreprocessor":
        """
        Construct a :class:`FeaturePreprocessor` from a fitted
        :class:`~app.ml.feature_engineer.FeatureEngineer` instance.

        This is the canonical way to create a preprocessor after training so
        that inference always uses the same fitted state.

        Args:
            feature_engineer: A *fitted* ``FeatureEngineer`` instance (i.e.
                :meth:`~app.ml.feature_engineer.FeatureEngineer.fit_transform`
                has already been called on it).

        Returns:
            A new :class:`FeaturePreprocessor` ready for inference.

        Raises:
            RuntimeError: If *feature_engineer* has not been fitted yet.
        """
        if not feature_engineer.is_fitted:
            raise RuntimeError(
                "FeatureEngineer has not been fitted. "
                "Call fit_transform() on training data before creating a preprocessor."
            )

        normalization = feature_engineer.normalization
        known_categories = dict(feature_engineer.known_categories)

        if normalization == "minmax":
            scaling_params = dict(feature_engineer.minmax_ranges)
        else:
            scaling_params = dict(feature_engineer.zscore_stats)

        logger.info(
            "Created FeaturePreprocessor from FeatureEngineer "
            "(normalization=%s, %d categorical columns, %d numerical columns fitted).",
            normalization,
            len(known_categories),
            len(scaling_params),
        )
        return cls(
            normalization=normalization,
            known_categories=known_categories,
            scaling_params=scaling_params,
        )

    # ------------------------------------------------------------------
    # Core transform API
    # ------------------------------------------------------------------

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the full inference preprocessing pipeline to *df*.

        Steps (in order):

        1. :func:`~app.ml.feature_engineer.impute_missing_values` — fill NaN.
        2. :func:`~app.ml.feature_engineer.create_derived_features` — compute
           compliance, deviation, health_trend, recovery_score.
        3. :meth:`apply_encoding` — one-hot encode categoricals using the
           training-time category lists.
        4. :meth:`apply_scaling` — scale numerics using the fitted parameters.

        Args:
            df: Raw patient record(s) as a DataFrame.  Column names must
                match those used during training.

        Returns:
            Transformed feature DataFrame aligned with the training schema.

        Raises:
            RuntimeError: If fitted state (categories or scaling params) is
                empty (i.e. the preprocessor was not constructed from a fitted
                source).
        """
        if not self._known_categories and not self._scaling_params:
            raise RuntimeError(
                "FeaturePreprocessor has no fitted state. "
                "Load a saved preprocessor or construct one via "
                "FeaturePreprocessor.from_feature_engineer()."
            )

        logger.info("FeaturePreprocessor.transform: processing %d record(s).", len(df))

        # Step 1 – Impute missing values
        df = impute_missing_values(df)

        # Step 2 – Create derived features (compliance, deviation, trend, recovery)
        df = create_derived_features(df)

        # Step 3 – One-hot encode using training-time categories
        df = self.apply_encoding(df)

        # Step 4 – Scale numerics using fitted parameters
        df = self.apply_scaling(df)

        logger.info("FeaturePreprocessor.transform complete. Output shape: %s.", df.shape)
        return df

    def apply_scaling(
        self,
        df: pd.DataFrame,
        columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Apply the fitted scaling transformation to numerical columns.

        Dispatches to either min-max or z-score normalization depending on
        :attr:`normalization`, always using the pre-fitted parameters so that
        inference is consistent with training (Requirement 4.7, 11.4).

        When a column in *columns* is not present in *df*, it is silently
        skipped (matching the behavior of the underlying helper functions).

        Args:
            df: DataFrame whose numerical columns should be scaled.
            columns: Columns to scale.  Defaults to
                :data:`~app.ml.feature_engineer.NUMERICAL_COLUMNS`.

        Returns:
            DataFrame with the specified columns scaled in-place (copy).

        Raises:
            RuntimeError: If no scaling parameters are available.
        """
        if not self._scaling_params:
            raise RuntimeError(
                "No scaling parameters available. "
                "Ensure the preprocessor was constructed from a fitted FeatureEngineer "
                "or loaded from disk."
            )

        if columns is None:
            columns = NUMERICAL_COLUMNS

        if self.normalization == "minmax":
            df, _ = minmax_normalize(
                df,
                columns=columns,
                feature_ranges=self._scaling_params,
            )
            logger.debug(
                "apply_scaling (minmax): scaled %d column(s).",
                sum(1 for c in columns if c in df.columns),
            )
        else:  # zscore
            df, _ = zscore_normalize(
                df,
                columns=columns,
                feature_stats=self._scaling_params,
            )
            logger.debug(
                "apply_scaling (zscore): scaled %d column(s).",
                sum(1 for c in columns if c in df.columns),
            )

        return df

    def apply_encoding(
        self,
        df: pd.DataFrame,
        columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Apply one-hot encoding aligned to the training-time category lists.

        Delegates to :func:`~app.ml.feature_engineer.one_hot_encode` with the
        ``known_categories`` parameter set to the fitted mapping.  This
        guarantees that:

        - Any category not seen during training maps to an all-zero row.
        - Columns are always in the same order as produced during training.
        - No extra columns are added for unseen categories at inference time.

        Requirement 4.7, 11.3.

        Args:
            df: DataFrame containing the categorical columns to encode.
            columns: Columns to encode.  Defaults to
                :data:`~app.ml.feature_engineer.CATEGORICAL_COLUMNS`.

        Returns:
            DataFrame with categorical columns replaced by binary dummy columns.

        Raises:
            RuntimeError: If no known-categories mapping is available.
        """
        if not self._known_categories:
            raise RuntimeError(
                "No known-categories mapping available. "
                "Ensure the preprocessor was constructed from a fitted FeatureEngineer "
                "or loaded from disk."
            )

        if columns is None:
            columns = CATEGORICAL_COLUMNS

        df = one_hot_encode(
            df,
            columns=columns,
            known_categories=self._known_categories,
        )
        logger.debug(
            "apply_encoding: one-hot encoded %d categorical column(s).",
            len(columns),
        )
        return df

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> Path:
        """
        Serialize the preprocessor state to disk using :mod:`joblib`.

        If *path* is a directory (or ends with ``/``), the file is saved as
        ``{path}/{DEFAULT_PREPROCESSOR_FILENAME}``.  Otherwise *path* is used
        as the exact file path.

        The serialized payload is a plain dict so that it is not tightly
        coupled to the class definition and can be loaded without importing
        this module first.

        Args:
            path: Destination file path or directory.

        Returns:
            The resolved file path where the preprocessor was written.

        Example::

            saved_path = preprocessor.save("/models/v1/")
            # -> Path("/models/v1/feature_preprocessor.joblib")
        """
        path = Path(path)
        if path.is_dir() or str(path).endswith(("/", "\\")):
            path = path / DEFAULT_PREPROCESSOR_FILENAME

        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "normalization": self.normalization,
            "known_categories": self._known_categories,
            "scaling_params": self._scaling_params,
        }
        joblib.dump(payload, path)
        logger.info(
            "FeaturePreprocessor saved to '%s' "
            "(normalization=%s, %d categorical columns, %d scaling params).",
            path,
            self.normalization,
            len(self._known_categories),
            len(self._scaling_params),
        )
        return path

    @classmethod
    def load(cls, path: str | Path) -> "FeaturePreprocessor":
        """
        Deserialize a :class:`FeaturePreprocessor` from disk.

        If *path* is a directory, the loader looks for
        ``{path}/{DEFAULT_PREPROCESSOR_FILENAME}`` inside it.

        Args:
            path: File path or directory containing the saved preprocessor.

        Returns:
            A fully initialized :class:`FeaturePreprocessor` ready for
            inference.

        Raises:
            FileNotFoundError: If the serialized file does not exist.
            ValueError: If the loaded payload is missing required keys or
                contains an unsupported normalization strategy.

        Example::

            preprocessor = FeaturePreprocessor.load("/models/v1/preprocessor.joblib")
            features = preprocessor.transform(patient_df)
        """
        path = Path(path)
        if path.is_dir():
            path = path / DEFAULT_PREPROCESSOR_FILENAME

        if not path.exists():
            raise FileNotFoundError(
                f"FeaturePreprocessor file not found at '{path}'. "
                "Ensure the file exists and the path is correct."
            )

        payload: dict = joblib.load(path)

        # Validate payload structure
        required_keys = {"normalization", "known_categories", "scaling_params"}
        missing = required_keys - set(payload.keys())
        if missing:
            raise ValueError(
                f"Loaded preprocessor payload is missing keys: {missing}. "
                "The file may be corrupt or was saved with an incompatible version."
            )

        normalization: str = payload["normalization"]
        if normalization not in SUPPORTED_NORMALIZATIONS:
            raise ValueError(
                f"Loaded preprocessor has unsupported normalization strategy '{normalization}'. "
                f"Supported strategies: {SUPPORTED_NORMALIZATIONS}."
            )

        instance = cls(
            normalization=normalization,
            known_categories=payload["known_categories"],
            scaling_params=payload["scaling_params"],
        )
        logger.info(
            "FeaturePreprocessor loaded from '%s' "
            "(normalization=%s, %d categorical columns, %d scaling params).",
            path,
            instance.normalization,
            len(instance._known_categories),
            len(instance._scaling_params),
        )
        return instance

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    @property
    def known_categories(self) -> dict[str, list[str]]:
        """Read-only copy of the training-time category mapping."""
        return dict(self._known_categories)

    @property
    def scaling_params(self) -> dict[str, tuple[float, float]]:
        """
        Read-only copy of the fitted scaling parameters.

        For **minmax**, each entry is ``(min, max)``.
        For **zscore**, each entry is ``(mean, std)``.
        """
        return dict(self._scaling_params)

    @property
    def is_ready(self) -> bool:
        """
        ``True`` when the preprocessor has both encoding and scaling state.

        A preprocessor is "ready" when it was either loaded from disk or
        constructed via :meth:`from_feature_engineer`.
        """
        return bool(self._known_categories) and bool(self._scaling_params)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FeaturePreprocessor("
            f"normalization={self.normalization!r}, "
            f"categorical_columns={list(self._known_categories.keys())}, "
            f"scaling_columns={list(self._scaling_params.keys())}, "
            f"is_ready={self.is_ready})"
        )

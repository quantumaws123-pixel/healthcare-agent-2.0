"""Standalone SHAP explainability module for Healthcare Agent 2.0.

This module exposes a clean public API for SHAP-based feature attribution
without duplicating the implementation that lives in
:mod:`app.ml.inference_engine`.

Public surface
--------------
- :class:`SHAPExplainer`   — re-exported from :mod:`app.ml.inference_engine`
- :func:`initialize_explainer` — convenience factory that wires up a
  :class:`SHAPExplainer` with a background dataset sampled from *data*

Constants re-exported for callers that import from this module directly:
- :data:`SHAP_TIMEOUT_SECONDS`
- :data:`TOP_N_SHAP_FEATURES`
- :data:`SHAP_BACKGROUND_SAMPLES`

**Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7**
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

# Re-export the canonical implementation — single source of truth.
from app.ml.inference_engine import (  # noqa: F401
    SHAPExplainer,
    SHAP_TIMEOUT_SECONDS,
    TOP_N_SHAP_FEATURES,
    SHAP_BACKGROUND_SAMPLES,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SHAPExplainer",
    "initialize_explainer",
    "SHAP_TIMEOUT_SECONDS",
    "TOP_N_SHAP_FEATURES",
    "SHAP_BACKGROUND_SAMPLES",
]


def initialize_explainer(
    data: np.ndarray,
    feature_names: Optional[list[str]] = None,
    n_background_samples: int = SHAP_BACKGROUND_SAMPLES,
    random_state: int = 42,
) -> SHAPExplainer:
    """Create a :class:`SHAPExplainer` pre-loaded with a background dataset.

    Samples up to *n_background_samples* rows from *data* to form the
    background dataset used by ``shap.KernelExplainer`` (Requirement 14.6).
    When *data* has fewer rows than *n_background_samples* all rows are used.

    The returned explainer is ready to call :meth:`SHAPExplainer.explain`
    immediately — no further setup required.

    Algorithm (Requirement 14.1):
    1. Randomly sample up to :data:`SHAP_BACKGROUND_SAMPLES` rows from *data*.
    2. Construct a :class:`SHAPExplainer` with the sampled background array.
    3. Attach *feature_names* so SHAP output carries human-readable labels
       (Requirement 14.4).

    Args:
        data: 2-D array ``[n_samples, n_features]`` representing the full
            (or training) dataset from which background samples are drawn.
        feature_names: Ordered list of feature column names.  When provided
            the explainer returns named features in its output (Requirement
            14.4); defaults to ``None`` (generic ``feature_N`` labels used).
        n_background_samples: Number of background samples to draw.  Defaults
            to :data:`SHAP_BACKGROUND_SAMPLES` (100) per Requirement 14.6.
        random_state: Random seed for reproducible sampling.

    Returns:
        A configured :class:`SHAPExplainer` instance with the background
        dataset and feature names set.

    Raises:
        ValueError: If *data* is empty or not 2-dimensional.

    **Validates: Requirements 14.1, 14.6**
    """
    if data.ndim != 2:
        raise ValueError(
            f"data must be a 2-D array [n_samples, n_features]; "
            f"got shape {data.shape!r}."
        )
    if data.shape[0] == 0:
        raise ValueError("data must contain at least one sample.")

    n_samples = data.shape[0]
    actual_samples = min(n_samples, n_background_samples)

    if actual_samples < n_samples:
        rng = np.random.default_rng(random_state)
        indices = rng.choice(n_samples, size=actual_samples, replace=False)
        background = data[indices]
    else:
        background = data.copy()

    logger.info(
        "initialize_explainer: sampled %d / %d rows as SHAP background dataset.",
        actual_samples,
        n_samples,
    )

    explainer = SHAPExplainer(
        background_samples=background,
        feature_names=feature_names or [],
    )
    return explainer

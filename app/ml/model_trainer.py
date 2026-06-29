"""Model training logic for Healthcare Agent 2.0 Backend ML System.

This module implements training pipelines for four ML architectures used to
predict 30-day hospital readmission risk:

- Logistic Regression  (scikit-learn)
- Random Forest        (scikit-learn)
- XGBoost              (xgboost)
- LSTM                 (TensorFlow / Keras)

Each trainer function follows a common contract:
1. Accept a :class:`~app.ml.data_splitter.DataSplit` and the list of feature
   column names.
2. Train on the *train* split, optionally using *val* for early stopping.
3. Evaluate on the *test* split and return an :class:`EvaluationMetrics`
   dataclass.
4. Serialize the trained artefact to disk (joblib for classical models,
   TensorFlow SavedModel for LSTM).
5. Return a :class:`TrainingResult` containing the model object, evaluation
   metrics, and serialization path.

**Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6**
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default label column — binary readmission target
TARGET_COLUMN: str = "readmission_target"

#: Columns that must be dropped before constructing the feature matrix
_DROP_COLUMNS: list[str] = [
    TARGET_COLUMN,
    "patient_id",
    "patient_name",
    "day",
    "created_at",
    "updated_at",
    # Textual ML output columns — not raw features
    "risk_level",
    "health_trend",
    "recovery_status",
    "doctor_recommendation",
    # Probabilities / scores that are *outputs*, not inputs for training
    "readmission_probability",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class EvaluationMetrics:
    """Evaluation metrics computed on the held-out test split.

    All values are floats in [0, 1] except where noted.

    **Validates: Requirements 3.5**
    """

    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Return metrics as a plain dictionary (used for metadata serialization)."""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "auc_roc": self.auc_roc,
        }


@dataclass
class TrainingResult:
    """Container returned by every ``train_*`` function.

    Attributes:
        model:            The trained model object (scikit-learn estimator,
                          XGBoost Booster, or Keras Model).
        model_type:       Human-readable architecture label.
        model_version:    Semantic version string (e.g. ``"v1.0"``).
        metrics:          Evaluation metrics on the test split.
        model_path:       Absolute path where the model was serialized.
        metadata_path:    Absolute path to the accompanying JSON metadata file.
        feature_columns:  Ordered list of feature column names used at training.
        dataset_size:     Total number of records used across all splits.
        training_date:    UTC timestamp when training completed.
    """

    model: Any
    model_type: str
    model_version: str
    metrics: EvaluationMetrics
    model_path: Path
    metadata_path: Path
    feature_columns: list[str]
    dataset_size: int
    training_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _prepare_matrices(
    df: pd.DataFrame,
    feature_columns: Optional[list[str]] = None,
    target_column: str = TARGET_COLUMN,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Extract feature matrix *X* and label vector *y* from *df*.

    Args:
        df: DataFrame that includes a target column and feature columns.
        feature_columns: Explicit list of feature columns to use.  When
            ``None``, all columns except those in :data:`_DROP_COLUMNS` are
            used.
        target_column: Name of the binary target column (0/1).

    Returns:
        Tuple ``(X, y, used_feature_columns)``.

    Raises:
        ValueError: If *target_column* is missing from *df*.
    """
    if target_column not in df.columns:
        # Try to derive readmission_target from readmission_probability if absent
        if "readmission_probability" in df.columns:
            df = df.copy()
            df[target_column] = (df["readmission_probability"] >= 0.5).astype(int)
            logger.info(
                "Derived '%s' from 'readmission_probability' using threshold 0.5.",
                target_column,
            )
        else:
            raise ValueError(
                f"Target column '{target_column}' not found and "
                "'readmission_probability' is also absent — cannot derive labels."
            )

    y: np.ndarray = df[target_column].values.astype(int)

    if feature_columns is None:
        drop = set(_DROP_COLUMNS) | {target_column}
        feature_columns = [c for c in df.columns if c not in drop]

    # Keep only columns that actually exist in this split
    available = [c for c in feature_columns if c in df.columns]
    if len(available) < len(feature_columns):
        missing = set(feature_columns) - set(available)
        logger.warning("Feature columns missing from DataFrame: %s", missing)

    X: np.ndarray = df[available].values.astype(float)
    return X, y, available


def _compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> EvaluationMetrics:
    """Compute accuracy, precision, recall, F1, and AUC-ROC.

    Args:
        y_true: Ground-truth binary labels (0/1).
        y_pred: Predicted binary labels (0/1).
        y_prob: Predicted probabilities for the positive class.

    Returns:
        Populated :class:`EvaluationMetrics` instance.

    **Validates: Requirements 3.5**
    """
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        roc_auc_score,
    )

    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        auc_roc = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        # Only one class in test set — AUC undefined
        logger.warning("AUC-ROC undefined (single class in test set); defaulting to 0.5.")
        auc_roc = 0.5

    metrics = EvaluationMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1,
        auc_roc=auc_roc,
    )
    logger.info(
        "Evaluation — accuracy=%.4f precision=%.4f recall=%.4f f1=%.4f auc_roc=%.4f",
        accuracy, precision, recall, f1, auc_roc,
    )
    return metrics


def _save_metadata(
    model_path: Path,
    model_type: str,
    model_version: str,
    dataset_size: int,
    feature_columns: list[str],
    metrics: EvaluationMetrics,
    training_date: datetime,
) -> Path:
    """Write a JSON sidecar file next to the serialized model.

    The sidecar stores training metadata needed for the ``/model/info``
    endpoint and A/B testing comparisons.

    **Validates: Requirements 3.6, 16.4**

    Args:
        model_path: Path of the serialized model file.
        model_type: Architecture name string.
        model_version: Semantic version string.
        dataset_size: Total records across all splits.
        feature_columns: Ordered list of feature column names.
        metrics: Evaluation metrics on the test split.
        training_date: UTC timestamp of training completion.

    Returns:
        Path to the written metadata JSON file.
    """
    metadata = {
        "model_version": model_version,
        "model_type": model_type,
        "model_path": str(model_path),
        "training_date": training_date.isoformat(),
        "dataset_size": dataset_size,
        "feature_columns": feature_columns,
        "evaluation_metrics": metrics.to_dict(),
    }
    metadata_path = model_path.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Saved model metadata to '%s'.", metadata_path)
    return metadata_path


def _resolve_model_path(
    model_dir: str | Path,
    model_type: str,
    model_version: str,
    suffix: str,
) -> Path:
    """Return the full file path for a serialized model artefact.

    The directory is created if it does not already exist.

    Args:
        model_dir: Root directory for model artefacts.
        model_type: Architecture label used in the filename.
        model_version: Version string (e.g. ``"v1.0"``).
        suffix: File extension including the leading dot (e.g. ``".pkl"``).

    Returns:
        Resolved :class:`~pathlib.Path` object.
    """
    directory = Path(model_dir)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{model_type.lower().replace(' ', '_')}_{model_version}{suffix}"
    return directory / filename


# ---------------------------------------------------------------------------
# Logistic Regression trainer
# ---------------------------------------------------------------------------


def train_logistic_regression(
    data_split: "DataSplit",  # noqa: F821 — imported lazily to avoid circular deps
    *,
    feature_columns: Optional[list[str]] = None,
    model_version: str = "v1.0",
    model_dir: str | Path = "./models",
    max_iter: int = 1000,
    C: float = 1.0,
    class_weight: Optional[str] = "balanced",
    random_state: int = 42,
) -> TrainingResult:
    """Train a Logistic Regression classifier for readmission prediction.

    The model is trained on ``data_split.train`` and evaluated on
    ``data_split.test``.  The validation split is not used during training
    (Logistic Regression does not support early stopping natively), but can
    be used by the caller for threshold tuning or hyper-parameter search.

    The trained model is serialised to disk using :mod:`joblib` in the format
    ``logistic_regression_{version}.pkl`` inside *model_dir*.

    Args:
        data_split: Pre-split patient DataFrames produced by
            :func:`~app.ml.data_splitter.split_patient_data`.
        feature_columns: Explicit list of feature column names.  When
            ``None``, all non-target columns in the train DataFrame are used.
        model_version: Semantic version string for the serialised artefact.
        model_dir: Directory where model files are written.
        max_iter: Maximum iterations for the solver.
        C: Inverse regularisation strength (smaller → stronger regularisation).
        class_weight: ``"balanced"`` adjusts weights inversely proportional to
            class frequencies; ``None`` gives equal weight.
        random_state: Seed for reproducibility.

    Returns:
        :class:`TrainingResult` with the trained estimator, metrics, and paths.

    **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6**
    """
    import joblib
    from sklearn.linear_model import LogisticRegression

    logger.info("Training Logistic Regression (version=%s) …", model_version)

    X_train, y_train, feat_cols = _prepare_matrices(data_split.train, feature_columns)
    X_test, y_test, _ = _prepare_matrices(data_split.test, feat_cols)

    model = LogisticRegression(
        max_iter=max_iter,
        C=C,
        class_weight=class_weight,
        random_state=random_state,
        solver="lbfgs",
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    metrics = _compute_metrics(y_test, y_pred, y_prob)

    model_path = _resolve_model_path(model_dir, "logistic_regression", model_version, ".pkl")
    joblib.dump(model, model_path)
    logger.info("Logistic Regression model saved to '%s'.", model_path)

    dataset_size = len(data_split.train) + len(data_split.val) + len(data_split.test)
    training_date = datetime.now(timezone.utc)

    metadata_path = _save_metadata(
        model_path, "LogisticRegression", model_version,
        dataset_size, feat_cols, metrics, training_date,
    )

    return TrainingResult(
        model=model,
        model_type="LogisticRegression",
        model_version=model_version,
        metrics=metrics,
        model_path=model_path,
        metadata_path=metadata_path,
        feature_columns=feat_cols,
        dataset_size=dataset_size,
        training_date=training_date,
    )


# ---------------------------------------------------------------------------
# Random Forest trainer
# ---------------------------------------------------------------------------


def train_random_forest(
    data_split: "DataSplit",  # noqa: F821
    *,
    feature_columns: Optional[list[str]] = None,
    model_version: str = "v1.0",
    model_dir: str | Path = "./models",
    n_estimators: int = 200,
    max_depth: Optional[int] = None,
    min_samples_split: int = 2,
    class_weight: Optional[str] = "balanced",
    random_state: int = 42,
    n_jobs: int = -1,
) -> TrainingResult:
    """Train a Random Forest classifier for readmission prediction.

    Training uses ``data_split.train``; evaluation uses ``data_split.test``.
    The model is serialised with :mod:`joblib` as
    ``random_forest_{version}.pkl`` inside *model_dir*.

    Args:
        data_split: Pre-split patient DataFrames.
        feature_columns: Explicit feature column list.  ``None`` infers from
            the train DataFrame.
        model_version: Semantic version string.
        model_dir: Directory for model artefacts.
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree; ``None`` for fully grown trees.
        min_samples_split: Minimum samples required to split an internal node.
        class_weight: ``"balanced"`` compensates for class imbalance.
        random_state: Seed for reproducibility.
        n_jobs: Number of parallel jobs (``-1`` uses all CPU cores).

    Returns:
        :class:`TrainingResult` with the trained estimator, metrics, and paths.

    **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6**
    """
    import joblib
    from sklearn.ensemble import RandomForestClassifier

    logger.info("Training Random Forest (version=%s, n_estimators=%d) …", model_version, n_estimators)

    X_train, y_train, feat_cols = _prepare_matrices(data_split.train, feature_columns)
    X_test, y_test, _ = _prepare_matrices(data_split.test, feat_cols)

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        class_weight=class_weight,
        random_state=random_state,
        n_jobs=n_jobs,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    metrics = _compute_metrics(y_test, y_pred, y_prob)

    model_path = _resolve_model_path(model_dir, "random_forest", model_version, ".pkl")
    joblib.dump(model, model_path)
    logger.info("Random Forest model saved to '%s'.", model_path)

    dataset_size = len(data_split.train) + len(data_split.val) + len(data_split.test)
    training_date = datetime.now(timezone.utc)

    metadata_path = _save_metadata(
        model_path, "RandomForest", model_version,
        dataset_size, feat_cols, metrics, training_date,
    )

    return TrainingResult(
        model=model,
        model_type="RandomForest",
        model_version=model_version,
        metrics=metrics,
        model_path=model_path,
        metadata_path=metadata_path,
        feature_columns=feat_cols,
        dataset_size=dataset_size,
        training_date=training_date,
    )


# ---------------------------------------------------------------------------
# XGBoost trainer
# ---------------------------------------------------------------------------


def train_xgboost(
    data_split: "DataSplit",  # noqa: F821
    *,
    feature_columns: Optional[list[str]] = None,
    model_version: str = "v1.0",
    model_dir: str | Path = "./models",
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.05,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    early_stopping_rounds: int = 20,
    random_state: int = 42,
) -> TrainingResult:
    """Train an XGBoost gradient-boosted classifier for readmission prediction.

    The validation split is used for early stopping so that the final model
    is not overfit to the training data.  The test split is held out
    exclusively for final evaluation.

    The trained model is serialised with :mod:`joblib` as
    ``xgboost_{version}.pkl`` inside *model_dir*.

    Args:
        data_split: Pre-split patient DataFrames.
        feature_columns: Explicit feature column list.  ``None`` infers from
            the train DataFrame.
        model_version: Semantic version string.
        model_dir: Directory for model artefacts.
        n_estimators: Maximum number of boosting rounds.
        max_depth: Maximum tree depth.
        learning_rate: Step size shrinkage used to prevent overfitting.
        subsample: Subsample ratio of training instances per tree.
        colsample_bytree: Subsample ratio of features per tree.
        early_stopping_rounds: Stop boosting if validation metric does not
            improve for this many consecutive rounds.
        random_state: Seed for reproducibility.

    Returns:
        :class:`TrainingResult` with the trained estimator, metrics, and paths.

    **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6**
    """
    import joblib

    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise ImportError(
            "XGBoost is not installed. Run: pip install xgboost"
        ) from exc

    logger.info(
        "Training XGBoost (version=%s, n_estimators=%d, max_depth=%d) …",
        model_version, n_estimators, max_depth,
    )

    X_train, y_train, feat_cols = _prepare_matrices(data_split.train, feature_columns)
    X_val, y_val, _ = _prepare_matrices(data_split.val, feat_cols)
    X_test, y_test, _ = _prepare_matrices(data_split.test, feat_cols)

    # Compute scale_pos_weight from training set to handle class imbalance
    n_neg = int(np.sum(y_train == 0))
    n_pos = int(np.sum(y_train == 1))
    scale_pos_weight = (n_neg / n_pos) if n_pos > 0 else 1.0
    logger.debug("XGBoost scale_pos_weight=%.4f (neg=%d, pos=%d)", scale_pos_weight, n_neg, n_pos)

    model = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        scale_pos_weight=scale_pos_weight,
        random_state=random_state,
        use_label_encoder=False,
        eval_metric="logloss",
        early_stopping_rounds=early_stopping_rounds,
        verbosity=0,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    metrics = _compute_metrics(y_test, y_pred, y_prob)

    model_path = _resolve_model_path(model_dir, "xgboost", model_version, ".pkl")
    joblib.dump(model, model_path)
    logger.info("XGBoost model saved to '%s'.", model_path)

    dataset_size = len(data_split.train) + len(data_split.val) + len(data_split.test)
    training_date = datetime.now(timezone.utc)

    metadata_path = _save_metadata(
        model_path, "XGBoost", model_version,
        dataset_size, feat_cols, metrics, training_date,
    )

    return TrainingResult(
        model=model,
        model_type="XGBoost",
        model_version=model_version,
        metrics=metrics,
        model_path=model_path,
        metadata_path=metadata_path,
        feature_columns=feat_cols,
        dataset_size=dataset_size,
        training_date=training_date,
    )


# ---------------------------------------------------------------------------
# LSTM trainer
# ---------------------------------------------------------------------------


def _build_lstm_model(
    n_features: int,
    lstm_units: int,
    dropout_rate: float,
    learning_rate: float,
) -> "tf.keras.Model":
    """Construct a single-layer LSTM binary classifier.

    Architecture:
        Input → Reshape(1, n_features) → LSTM(units) → Dropout → Dense(1, sigmoid)

    The reshape layer presents each tabular patient record as a single
    time-step sequence so the LSTM kernel can be applied without requiring
    true sequential input.  For full temporal modelling see the multi-day
    variant in the roadmap.

    Args:
        n_features: Number of input features per sample.
        lstm_units: Number of LSTM hidden units.
        dropout_rate: Dropout fraction applied after the LSTM layer.
        learning_rate: Initial learning rate for the Adam optimiser.

    Returns:
        Compiled Keras ``Model`` ready for ``fit()``.
    """
    import tensorflow as tf  # noqa: PLC0415 — deferred to avoid startup cost

    inputs = tf.keras.Input(shape=(n_features,), name="features")
    x = tf.keras.layers.Reshape((1, n_features), name="reshape")(inputs)
    x = tf.keras.layers.LSTM(lstm_units, name="lstm")(x)
    x = tf.keras.layers.Dropout(dropout_rate, name="dropout")(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", name="readmission_prob")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="lstm_readmission")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train_lstm(
    data_split: "DataSplit",  # noqa: F821
    *,
    feature_columns: Optional[list[str]] = None,
    model_version: str = "v1.0",
    model_dir: str | Path = "./models",
    lstm_units: int = 64,
    dropout_rate: float = 0.3,
    learning_rate: float = 1e-3,
    epochs: int = 50,
    batch_size: int = 32,
    patience: int = 10,
) -> TrainingResult:
    """Train an LSTM neural network for readmission prediction.

    The validation split drives early stopping (via Keras
    ``EarlyStopping`` callback) to prevent overfitting.  The test split is
    held out exclusively for final evaluation.

    The trained model is saved as a TensorFlow SavedModel directory at
    ``{model_dir}/lstm_{version}_savedmodel/``.  A :mod:`joblib` pickle
    containing the feature column list is also written alongside so that
    inference code can reconstruct the input schema without accessing the
    training environment.

    Args:
        data_split: Pre-split patient DataFrames.
        feature_columns: Explicit feature column list.  ``None`` infers from
            the train DataFrame.
        model_version: Semantic version string.
        model_dir: Directory for model artefacts.
        lstm_units: Number of units in the LSTM layer.
        dropout_rate: Dropout fraction applied after LSTM.
        learning_rate: Initial learning rate for the Adam optimiser.
        epochs: Maximum training epochs.
        batch_size: Mini-batch size.
        patience: Early stopping patience (epochs without validation loss
            improvement before training halts).

    Returns:
        :class:`TrainingResult` with the compiled Keras model, metrics, and paths.

    **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6**
    """
    import joblib

    try:
        import tensorflow as tf
    except ImportError as exc:
        raise ImportError(
            "TensorFlow is not installed. Run: pip install tensorflow"
        ) from exc

    logger.info(
        "Training LSTM (version=%s, lstm_units=%d, epochs=%d) …",
        model_version, lstm_units, epochs,
    )

    X_train, y_train, feat_cols = _prepare_matrices(data_split.train, feature_columns)
    X_val, y_val, _ = _prepare_matrices(data_split.val, feat_cols)
    X_test, y_test, _ = _prepare_matrices(data_split.test, feat_cols)

    n_features = X_train.shape[1]
    keras_model = _build_lstm_model(n_features, lstm_units, dropout_rate, learning_rate)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=patience,
            restore_best_weights=True,
            verbose=0,
        )
    ]

    keras_model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=0,
    )

    y_prob = keras_model.predict(X_test, verbose=0).flatten()
    y_pred = (y_prob >= 0.5).astype(int)
    metrics = _compute_metrics(y_test, y_pred, y_prob)

    # Serialise as TensorFlow SavedModel
    saved_model_dir = (
        Path(model_dir)
        / f"lstm_{model_version}_savedmodel"
    )
    saved_model_dir.mkdir(parents=True, exist_ok=True)
    keras_model.save(str(saved_model_dir))
    logger.info("LSTM SavedModel saved to '%s'.", saved_model_dir)

    # Persist feature schema alongside the SavedModel
    schema_path = saved_model_dir / "feature_columns.pkl"
    joblib.dump(feat_cols, schema_path)
    logger.info("LSTM feature schema saved to '%s'.", schema_path)

    dataset_size = len(data_split.train) + len(data_split.val) + len(data_split.test)
    training_date = datetime.now(timezone.utc)

    # metadata_path lives next to the SavedModel directory
    metadata_path = _save_metadata(
        saved_model_dir / "model",  # base path for sidecar JSON
        "LSTM", model_version,
        dataset_size, feat_cols, metrics, training_date,
    )

    return TrainingResult(
        model=keras_model,
        model_type="LSTM",
        model_version=model_version,
        metrics=metrics,
        model_path=saved_model_dir,
        metadata_path=metadata_path,
        feature_columns=feat_cols,
        dataset_size=dataset_size,
        training_date=training_date,
    )


# ---------------------------------------------------------------------------
# Convenience: train all architectures and compare
# ---------------------------------------------------------------------------


def train_all_models(
    data_split: "DataSplit",  # noqa: F821
    *,
    feature_columns: Optional[list[str]] = None,
    model_version: str = "v1.0",
    model_dir: str | Path = "./models",
    include_lstm: bool = True,
) -> dict[str, TrainingResult]:
    """Train all supported architectures and return a comparison dict.

    This is a convenience wrapper that sequentially trains Logistic
    Regression, Random Forest, XGBoost, and (optionally) LSTM using default
    hyper-parameters.  Results are keyed by model type name.

    The caller can inspect each :class:`TrainingResult` to select the best
    model for production deployment (Requirement 3.7).

    Args:
        data_split: Pre-split patient DataFrames.
        feature_columns: Shared feature column list for all models.
        model_version: Semantic version string applied to all artefacts.
        model_dir: Root directory for all serialised models.
        include_lstm: Whether to include the LSTM (requires TensorFlow).

    Returns:
        Dict mapping model type names to their :class:`TrainingResult`.

    **Validates: Requirements 3.1, 3.7**
    """
    results: dict[str, TrainingResult] = {}

    trainers = [
        ("LogisticRegression", train_logistic_regression),
        ("RandomForest", train_random_forest),
        ("XGBoost", train_xgboost),
    ]

    for name, trainer_fn in trainers:
        try:
            result = trainer_fn(
                data_split,
                feature_columns=feature_columns,
                model_version=model_version,
                model_dir=model_dir,
            )
            results[name] = result
            logger.info(
                "Trained %s — AUC-ROC=%.4f  F1=%.4f",
                name, result.metrics.auc_roc, result.metrics.f1_score,
            )
        except Exception as exc:  # noqa: BLE001 — log and continue
            logger.error("Failed to train %s: %s", name, exc, exc_info=True)

    if include_lstm:
        try:
            result = train_lstm(
                data_split,
                feature_columns=feature_columns,
                model_version=model_version,
                model_dir=model_dir,
            )
            results["LSTM"] = result
            logger.info(
                "Trained LSTM — AUC-ROC=%.4f  F1=%.4f",
                result.metrics.auc_roc, result.metrics.f1_score,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to train LSTM: %s", exc, exc_info=True)

    # Log comparison summary
    if results:
        summary_lines = [
            f"  {name:25s} acc={r.metrics.accuracy:.4f}  "
            f"prec={r.metrics.precision:.4f}  rec={r.metrics.recall:.4f}  "
            f"f1={r.metrics.f1_score:.4f}  auc={r.metrics.auc_roc:.4f}"
            for name, r in results.items()
        ]
        logger.info("Model comparison:\n%s", "\n".join(summary_lines))

    return results

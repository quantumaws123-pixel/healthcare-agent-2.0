"""Model registry for Healthcare Agent 2.0 Backend ML System.

This module provides versioned model storage, retrieval, and metadata management
for trained ML models (Logistic Regression, Random Forest, XGBoost, LSTM).

It persists training metadata to the database via the ``MLModelDB`` ORM model
and serialises / deserialises model artefacts using joblib (classical models)
or TensorFlow's SavedModel format (LSTM).

**Validates: Requirements 16.1, 16.2, 16.4, 16.5**
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MLModelDB
from app.ml.model_trainer import EvaluationMetrics, TrainingResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default directory where model artefact files are stored on disk.
DEFAULT_MODEL_DIR: str = "./models"

#: Sentinel version string meaning "use the currently active model".
VERSION_LATEST: str = "latest"


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


class ModelRegistry:
    """Manages ML model versions, on-disk artefacts, and database metadata.

    The registry provides four primary operations:

    1. :meth:`save_model`  — persist a newly trained model and its metadata.
    2. :meth:`load_model`  — deserialise a model from disk by version.
    3. :meth:`list_models` — query all stored model versions from the database.
    4. :meth:`get_model_info` — retrieve metadata for the active (or a specific) model.

    Database operations are performed via an async ``AsyncSession`` that is
    provided at construction time (dependency-injected from FastAPI's session
    factory).  On-disk serialisation uses :mod:`joblib` for classical
    scikit-learn / XGBoost models and TensorFlow's SavedModel format for LSTM.

    **Validates: Requirements 16.1, 16.2, 16.4, 16.5**
    """

    def __init__(
        self,
        session: AsyncSession,
        model_dir: str | Path = DEFAULT_MODEL_DIR,
    ) -> None:
        """Initialise the registry.

        Args:
            session: Async SQLAlchemy session for database operations.
            model_dir: Root directory where model artefact files are stored.
                The directory is created automatically if it does not exist.
        """
        self.session = session
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # save_model
    # ------------------------------------------------------------------

    async def save_model(
        self,
        result: TrainingResult,
        *,
        set_active: bool = False,
    ) -> MLModelDB:
        """Persist a trained model and store its metadata in the database.

        Writes the model artefact to disk (if not already present at
        ``result.model_path``) and inserts a corresponding row into the
        ``ml_models`` table.  If a row with the same ``model_version`` already
        exists the operation is idempotent — the existing record is returned
        unchanged.

        When *set_active* is ``True`` the new model is marked as the active
        model and all other versions are deactivated atomically within the
        same transaction.

        Args:
            result: Completed :class:`~app.ml.model_trainer.TrainingResult`
                returned by one of the ``train_*`` functions.
            set_active: When ``True``, mark this version as the currently
                active model (deactivates all others).

        Returns:
            The persisted :class:`~app.database.models.MLModelDB` ORM instance.

        Raises:
            SQLAlchemyError: If the database operation fails.

        **Validates: Requirements 16.1, 16.4**
        """
        # ------------------------------------------------------------------
        # 1. Ensure the model artefact exists on disk
        # ------------------------------------------------------------------
        model_path = Path(result.model_path)
        if not model_path.exists():
            logger.warning(
                "Model path '%s' does not exist on disk — "
                "the TrainingResult may not have been serialised yet.",
                model_path,
            )

        # ------------------------------------------------------------------
        # 2. Check for an existing record with the same version
        # ------------------------------------------------------------------
        try:
            existing = await self._get_by_version(result.model_version)
            if existing is not None:
                logger.info(
                    "Model version '%s' already registered (model_id=%d); "
                    "skipping duplicate insert.",
                    result.model_version,
                    existing.model_id,
                )
                return existing

            # ------------------------------------------------------------------
            # 3. Deactivate all other versions if this one should be active
            # ------------------------------------------------------------------
            if set_active:
                await self._deactivate_all()

            # ------------------------------------------------------------------
            # 4. Insert new metadata row
            # ------------------------------------------------------------------
            metrics: EvaluationMetrics = result.metrics
            db_record = MLModelDB(
                model_version=result.model_version,
                model_type=result.model_type,
                model_path=str(model_path),
                training_date=result.training_date.replace(tzinfo=None)
                if result.training_date.tzinfo is not None
                else result.training_date,
                dataset_size=result.dataset_size,
                accuracy=round(metrics.accuracy, 4),
                precision=round(metrics.precision, 4),
                recall=round(metrics.recall, 4),
                f1_score=round(metrics.f1_score, 4),
                auc_roc=round(metrics.auc_roc, 4),
                is_active=set_active,
            )

            self.session.add(db_record)
            await self.session.flush()
            await self.session.refresh(db_record)

            logger.info(
                "Registered model version='%s' type='%s' "
                "dataset_size=%d is_active=%s (model_id=%d).",
                db_record.model_version,
                db_record.model_type,
                db_record.dataset_size,
                db_record.is_active,
                db_record.model_id,
            )
            return db_record

        except SQLAlchemyError:
            logger.error(
                "Failed to save model version '%s' to database.",
                result.model_version,
                exc_info=True,
            )
            raise

    # ------------------------------------------------------------------
    # load_model
    # ------------------------------------------------------------------

    async def load_model(
        self,
        version: str = VERSION_LATEST,
    ) -> tuple[Any, MLModelDB]:
        """Deserialise a trained model from disk.

        When *version* is ``"latest"`` the currently active model (``is_active
        = True``) is loaded.  If no active model exists, the most recently
        registered model is used.  Otherwise the model whose ``model_version``
        matches *version* exactly is loaded.

        The deserialisation method is chosen automatically based on the stored
        ``model_type``:

        - ``"LSTM"`` — loaded via ``tf.keras.models.load_model`` from a
          TensorFlow SavedModel directory.
        - All others — loaded via ``joblib.load`` from a ``.pkl`` file.

        Args:
            version: Semantic version string (e.g. ``"v1.0"``) or
                ``"latest"`` (default).

        Returns:
            A tuple ``(model_object, db_metadata)`` where *model_object* is
            the deserialised model and *db_metadata* is the corresponding
            :class:`~app.database.models.MLModelDB` ORM row.

        Raises:
            ValueError: If no matching model version is found in the database.
            FileNotFoundError: If the model artefact file is missing on disk.
            SQLAlchemyError: If the database query fails.

        **Validates: Requirements 16.2**
        """
        try:
            db_record = await self._resolve_version(version)
        except SQLAlchemyError:
            logger.error(
                "Database error while resolving model version '%s'.", version, exc_info=True
            )
            raise

        if db_record is None:
            raise ValueError(
                f"No model found for version='{version}'. "
                "Train and register a model first."
            )

        model_path = Path(db_record.model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model artefact not found on disk: '{model_path}'. "
                f"The file may have been moved or deleted."
            )

        model = self._deserialise(model_path, db_record.model_type)

        logger.info(
            "Loaded model version='%s' type='%s' from '%s'.",
            db_record.model_version,
            db_record.model_type,
            model_path,
        )
        return model, db_record

    # ------------------------------------------------------------------
    # list_models
    # ------------------------------------------------------------------

    async def list_models(
        self,
        *,
        active_only: bool = False,
        model_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[MLModelDB]:
        """Query all registered model versions from the database.

        Results are ordered by ``training_date`` descending (most recently
        trained first).

        Args:
            active_only: When ``True``, return only the active model(s).
            model_type: Optional filter — e.g. ``"XGBoost"`` or
                ``"RandomForest"``.
            limit: Maximum number of records to return (default: 100).

        Returns:
            List of :class:`~app.database.models.MLModelDB` ORM instances.

        Raises:
            SQLAlchemyError: If the database query fails.

        **Validates: Requirements 16.2, 16.5**
        """
        try:
            query = select(MLModelDB).order_by(desc(MLModelDB.training_date))

            if active_only:
                query = query.where(MLModelDB.is_active.is_(True))

            if model_type is not None:
                query = query.where(MLModelDB.model_type == model_type)

            query = query.limit(limit)

            result = await self.session.execute(query)
            records = list(result.scalars().all())

            logger.debug(
                "list_models returned %d record(s) "
                "(active_only=%s, model_type=%s, limit=%d).",
                len(records),
                active_only,
                model_type,
                limit,
            )
            return records

        except SQLAlchemyError:
            logger.error("Failed to list model versions.", exc_info=True)
            raise

    # ------------------------------------------------------------------
    # get_model_info
    # ------------------------------------------------------------------

    async def get_model_info(
        self,
        version: str = VERSION_LATEST,
    ) -> dict[str, Any]:
        """Return metadata for a model version in the ``/model/info`` format.

        The returned dictionary matches the schema expected by the
        ``GET /model/info`` API endpoint (Requirement 16.5).

        Args:
            version: Semantic version string or ``"latest"`` (default).

        Returns:
            Dictionary with keys: ``model_version``, ``model_type``,
            ``training_date``, ``dataset_size``, ``evaluation_metrics``.

        Raises:
            ValueError: If no matching model is found in the database.
            SQLAlchemyError: If the database query fails.

        **Validates: Requirements 16.4, 16.5**
        """
        try:
            db_record = await self._resolve_version(version)
        except SQLAlchemyError:
            logger.error(
                "Database error while fetching model info for version='%s'.",
                version,
                exc_info=True,
            )
            raise

        if db_record is None:
            raise ValueError(
                f"No model found for version='{version}'. "
                "Train and register a model first."
            )

        # Normalise training_date to ISO 8601 string
        training_date = db_record.training_date
        if isinstance(training_date, datetime):
            training_date_str = training_date.isoformat()
        else:
            training_date_str = str(training_date)

        return {
            "model_version": db_record.model_version,
            "model_type": db_record.model_type,
            "training_date": training_date_str,
            "dataset_size": db_record.dataset_size,
            "evaluation_metrics": {
                "accuracy": float(db_record.accuracy) if db_record.accuracy is not None else None,
                "precision": float(db_record.precision) if db_record.precision is not None else None,
                "recall": float(db_record.recall) if db_record.recall is not None else None,
                "f1_score": float(db_record.f1_score) if db_record.f1_score is not None else None,
                "auc_roc": float(db_record.auc_roc) if db_record.auc_roc is not None else None,
            },
        }

    # ------------------------------------------------------------------
    # activate_version
    # ------------------------------------------------------------------

    async def activate_version(self, version: str) -> MLModelDB:
        """Mark a specific model version as the active model.

        Deactivates all other versions atomically within the same transaction.

        Args:
            version: Semantic version string (e.g. ``"v1.2"``).

        Returns:
            The updated :class:`~app.database.models.MLModelDB` record.

        Raises:
            ValueError: If *version* is not found in the database.
            SQLAlchemyError: If the database operation fails.

        **Validates: Requirements 16.3, 16.7**
        """
        try:
            db_record = await self._get_by_version(version)
            if db_record is None:
                raise ValueError(
                    f"Cannot activate unknown model version='{version}'."
                )

            await self._deactivate_all()

            db_record.is_active = True
            await self.session.flush()
            await self.session.refresh(db_record)

            logger.info(
                "Activated model version='%s' (model_id=%d).",
                db_record.model_version,
                db_record.model_id,
            )
            return db_record

        except SQLAlchemyError:
            logger.error(
                "Failed to activate model version='%s'.", version, exc_info=True
            )
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_by_version(self, version: str) -> Optional[MLModelDB]:
        """Fetch a single MLModelDB row by exact model_version string."""
        query = select(MLModelDB).where(MLModelDB.model_version == version)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_active_model(self) -> Optional[MLModelDB]:
        """Return the currently active model, or None if none is active."""
        query = (
            select(MLModelDB)
            .where(MLModelDB.is_active.is_(True))
            .order_by(desc(MLModelDB.training_date))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_latest_model(self) -> Optional[MLModelDB]:
        """Return the most recently trained model regardless of active status."""
        query = (
            select(MLModelDB)
            .order_by(desc(MLModelDB.training_date))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _resolve_version(self, version: str) -> Optional[MLModelDB]:
        """Resolve a version string to an MLModelDB record.

        ``"latest"`` resolves to the active model (or the most recently
        trained model if none is active).  Any other string performs an
        exact match on ``model_version``.
        """
        if version == VERSION_LATEST:
            record = await self._get_active_model()
            if record is None:
                logger.info(
                    "No active model found; falling back to most recently trained model."
                )
                record = await self._get_latest_model()
            return record

        return await self._get_by_version(version)

    async def _deactivate_all(self) -> None:
        """Set ``is_active = False`` on every model in the database."""
        all_query = select(MLModelDB).where(MLModelDB.is_active.is_(True))
        result = await self.session.execute(all_query)
        active_records = result.scalars().all()
        for rec in active_records:
            rec.is_active = False
        if active_records:
            await self.session.flush()
            logger.debug(
                "Deactivated %d previously active model(s).", len(active_records)
            )

    @staticmethod
    def _deserialise(model_path: Path, model_type: str) -> Any:
        """Load a model artefact from disk.

        Args:
            model_path: Absolute path to the serialised artefact.
            model_type: Architecture label — ``"LSTM"`` triggers TensorFlow
                loading; all others use joblib.

        Returns:
            Deserialised model object.

        Raises:
            ImportError: If the required serialisation library is not installed.
            FileNotFoundError: If *model_path* does not exist.
        """
        if model_type == "LSTM":
            try:
                import tensorflow as tf  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "TensorFlow is required to load LSTM models. "
                    "Run: pip install tensorflow"
                ) from exc

            logger.debug("Loading LSTM SavedModel from '%s'.", model_path)
            return tf.keras.models.load_model(str(model_path))

        # Classical / XGBoost models serialised with joblib
        try:
            import joblib  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "joblib is required to load serialised models. "
                "Run: pip install joblib"
            ) from exc

        logger.debug("Loading model via joblib from '%s'.", model_path)
        return joblib.load(model_path)

    # ------------------------------------------------------------------
    # Convenience: register from metadata JSON sidecar
    # ------------------------------------------------------------------

    async def register_from_metadata_file(
        self,
        metadata_path: str | Path,
        *,
        set_active: bool = False,
    ) -> MLModelDB:
        """Register a model by reading its JSON metadata sidecar file.

        This method is useful when a model was trained offline and only the
        metadata JSON (written by :func:`~app.ml.model_trainer._save_metadata`)
        is available without a live :class:`~app.ml.model_trainer.TrainingResult`.

        Args:
            metadata_path: Path to the ``*.json`` sidecar file generated during
                training.
            set_active: When ``True``, mark this version as active.

        Returns:
            The persisted :class:`~app.database.models.MLModelDB` ORM instance.

        Raises:
            FileNotFoundError: If *metadata_path* does not exist.
            KeyError: If required metadata fields are missing from the JSON.
            SQLAlchemyError: If the database operation fails.

        **Validates: Requirements 16.1, 16.4**
        """
        metadata_path = Path(metadata_path)
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata sidecar file not found: '{metadata_path}'."
            )

        with metadata_path.open(encoding="utf-8") as fh:
            meta = json.load(fh)

        # Build a synthetic TrainingResult-like object from the JSON
        eval_meta = meta.get("evaluation_metrics", {})
        metrics = EvaluationMetrics(
            accuracy=float(eval_meta.get("accuracy", 0.0)),
            precision=float(eval_meta.get("precision", 0.0)),
            recall=float(eval_meta.get("recall", 0.0)),
            f1_score=float(eval_meta.get("f1_score", 0.0)),
            auc_roc=float(eval_meta.get("auc_roc", 0.0)),
        )

        training_date_raw = meta.get("training_date")
        if training_date_raw:
            training_date = datetime.fromisoformat(training_date_raw)
        else:
            training_date = datetime.now(timezone.utc)

        # Reconstruct a minimal TrainingResult for save_model
        from dataclasses import dataclass, field as dc_field

        @dataclass
        class _MetaResult:
            model: Any = None
            model_type: str = ""
            model_version: str = ""
            metrics: EvaluationMetrics = dc_field(default_factory=EvaluationMetrics)
            model_path: Path = Path(".")
            metadata_path: Path = Path(".")
            feature_columns: list[str] = dc_field(default_factory=list)
            dataset_size: int = 0
            training_date: datetime = dc_field(
                default_factory=lambda: datetime.now(timezone.utc)
            )

        synthetic = _MetaResult(
            model_type=meta["model_type"],
            model_version=meta["model_version"],
            metrics=metrics,
            model_path=Path(meta["model_path"]),
            metadata_path=metadata_path,
            feature_columns=meta.get("feature_columns", []),
            dataset_size=int(meta.get("dataset_size", 0)),
            training_date=training_date,
        )

        return await self.save_model(synthetic, set_active=set_active)  # type: ignore[arg-type]

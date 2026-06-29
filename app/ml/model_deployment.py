"""Model deployment utilities for Healthcare Agent 2.0 Backend ML System.

This module provides hot-swapping and A/B testing capabilities for ML models,
allowing new model versions to be loaded into the running server without a
restart and for traffic to be split between two model versions for comparison.

Key components
--------------
- :func:`reload_model`        — swap the active model in an :class:`InferenceEngine`
                                without restarting the server (Requirement 16.3).
- :class:`ABTestConfig`       — dataclass that defines a two-model A/B test with a
                                traffic-split percentage (Requirement 16.6).
- :func:`get_model_for_request` — selects which model version to use for a given
                                  request based on the A/B traffic split.
- :class:`DeploymentManager`  — holds the active deployment configuration and
                                 exposes a clean API for hot-swap and A/B management.

Design notes
------------
Deployment state is kept in an **in-memory dict** inside :class:`DeploymentManager`
(no additional database table is required).  The manager is intended to be used as
an application-level singleton (e.g. stored on ``app.state``).

Thread/concurrency safety
--------------------------
Python attribute assignment is atomic at the interpreter level, so replacing the
``InferenceEngine._model`` reference during a hot-swap is safe for concurrent async
request handlers.  In-flight requests that captured a reference to the old model
object will finish normally; new requests will pick up the new model automatically.

**Validates: Requirements 16.3, 16.6**
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any, Optional

from app.ml.inference_engine import InferenceEngine
from app.ml.model_registry import ModelRegistry, VERSION_LATEST

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# reload_model
# ---------------------------------------------------------------------------


async def reload_model(
    engine: InferenceEngine,
    registry: ModelRegistry,
    version: str = VERSION_LATEST,
) -> str:
    """Hot-swap the model loaded inside *engine* to a different *version*.

    Calls :meth:`InferenceEngine.load_model` under the hood so that the engine
    transitions to the new model atomically from the perspective of async
    request handlers.  No server restart is required (Requirement 16.3).

    Args:
        engine: The running :class:`InferenceEngine` whose model should be
            replaced.
        registry: The :class:`ModelRegistry` used to locate and deserialise the
            requested model version from disk.
        version: Target model version string (e.g. ``"v1.2"``) or
            ``"latest"`` (default) to load the currently active model.

    Returns:
        The version string of the newly loaded model as reported by the engine
        after the swap (``engine.model_version``).

    Raises:
        ValueError: If *version* is not found in the registry.
        FileNotFoundError: If the model artefact file is missing on disk.
        RuntimeError: If the registry raises an unexpected error during load.

    **Validates: Requirement 16.3**
    """
    logger.info(
        "reload_model: hot-swapping InferenceEngine to version='%s' …", version
    )
    previous_version = engine.model_version

    # Temporarily point the engine at the requested registry so load_model
    # fetches from the right source.
    original_registry = engine._registry  # noqa: SLF001
    engine._registry = registry  # noqa: SLF001
    try:
        await engine.load_model(version)
    except Exception:
        # Restore the original registry reference so the engine stays usable
        engine._registry = original_registry  # noqa: SLF001
        logger.error(
            "reload_model: failed to swap model; engine remains on version='%s'.",
            previous_version,
            exc_info=True,
        )
        raise

    new_version = engine.model_version
    logger.info(
        "reload_model: swap complete — version '%s' → '%s'.",
        previous_version,
        new_version,
    )
    return new_version  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# ABTestConfig
# ---------------------------------------------------------------------------


@dataclass
class ABTestConfig:
    """Configuration for a two-model A/B test.

    Defines which two model versions are under test and what fraction of
    incoming prediction requests should be routed to model B.

    Attributes:
        model_a_version: Version string for the control model (e.g. ``"v1.0"``).
        model_b_version: Version string for the challenger model (e.g. ``"v1.1"``).
        traffic_split: Percentage of requests (0–100) that should be directed
            to *model_b_version*.  The remaining ``100 - traffic_split`` percent
            go to *model_a_version*.

    Example::

        config = ABTestConfig(
            model_a_version="v1.0",
            model_b_version="v1.1",
            traffic_split=20,  # 20 % of requests → v1.1
        )

    **Validates: Requirement 16.6**
    """

    model_a_version: str
    model_b_version: str
    traffic_split: int = 50  # percent of requests routed to model B (0-100)

    def __post_init__(self) -> None:
        if not (0 <= self.traffic_split <= 100):
            raise ValueError(
                f"traffic_split must be between 0 and 100; got {self.traffic_split!r}."
            )


# ---------------------------------------------------------------------------
# get_model_for_request
# ---------------------------------------------------------------------------


def get_model_for_request(config: ABTestConfig) -> str:
    """Select a model version for a single request based on the A/B traffic split.

    Uses ``random.randint`` to produce a uniform draw in [1, 100] and compares
    it against ``config.traffic_split`` to decide which variant to serve.

    - If the draw ≤ ``traffic_split`` → returns ``model_b_version`` (challenger).
    - Otherwise → returns ``model_a_version`` (control).

    A ``traffic_split`` of 0 always returns model A; a value of 100 always
    returns model B.

    Args:
        config: Active :class:`ABTestConfig`.

    Returns:
        The model version string that should handle this request.

    **Validates: Requirement 16.6**
    """
    draw = random.randint(1, 100)
    chosen = config.model_b_version if draw <= config.traffic_split else config.model_a_version
    logger.debug(
        "get_model_for_request: draw=%d split=%d → version='%s'.",
        draw,
        config.traffic_split,
        chosen,
    )
    return chosen


# ---------------------------------------------------------------------------
# DeploymentManager
# ---------------------------------------------------------------------------


class DeploymentManager:
    """Manages the active model deployment configuration for the application.

    The manager keeps deployment state in an in-memory dictionary
    (``_state``) so no extra database table is needed.  It supports:

    - **Single-model deployment**: one version active, all traffic served by it.
    - **A/B test deployment**: two versions active, traffic split according to
      :class:`ABTestConfig`.

    Intended use
    ------------
    Instantiate once at application startup and store on ``app.state``::

        app.state.deployment_manager = DeploymentManager(engine, registry)

    Then use :meth:`hot_swap` or :meth:`configure_ab_test` to change the
    active configuration at runtime through admin API endpoints.

    **Validates: Requirements 16.3, 16.6**
    """

    def __init__(
        self,
        engine: InferenceEngine,
        registry: ModelRegistry,
    ) -> None:
        """Initialise the manager.

        Args:
            engine: The application's running :class:`InferenceEngine`.
            registry: The :class:`ModelRegistry` used for model loading.
        """
        self._engine = engine
        self._registry = registry

        # In-memory deployment state (no DB table)
        self._state: dict[str, Any] = {
            "mode": "single",         # "single" | "ab_test"
            "ab_config": None,        # ABTestConfig | None
            "active_version": engine.model_version,
        }

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> dict[str, Any]:
        """Read-only snapshot of the current deployment state dict."""
        return dict(self._state)

    @property
    def ab_config(self) -> Optional[ABTestConfig]:
        """The active :class:`ABTestConfig`, or ``None`` when not in A/B mode."""
        return self._state.get("ab_config")

    # ------------------------------------------------------------------
    # hot_swap
    # ------------------------------------------------------------------

    async def hot_swap(self, version: str = VERSION_LATEST) -> str:
        """Hot-swap the engine to a new model version without server restart.

        Clears any active A/B test and puts the manager back into
        single-model mode pointing at *version*.

        Args:
            version: Target model version or ``"latest"`` (default).

        Returns:
            The version string of the newly active model.

        Raises:
            ValueError / FileNotFoundError: Propagated from :func:`reload_model`.

        **Validates: Requirement 16.3**
        """
        new_version = await reload_model(self._engine, self._registry, version)
        self._state["mode"] = "single"
        self._state["ab_config"] = None
        self._state["active_version"] = new_version
        logger.info("DeploymentManager: hot-swap to version='%s' complete.", new_version)
        return new_version

    # ------------------------------------------------------------------
    # configure_ab_test
    # ------------------------------------------------------------------

    def configure_ab_test(
        self,
        model_a_version: str,
        model_b_version: str,
        traffic_split: int = 50,
    ) -> ABTestConfig:
        """Configure an A/B test between two model versions.

        The manager switches to ``"ab_test"`` mode.  Subsequent calls to
        :meth:`select_version_for_request` will use the stored config to
        route traffic probabilistically.

        Note: This method only updates the routing configuration.  The caller
        is responsible for ensuring both model versions are available in the
        registry.  Load the secondary engine / version separately if needed.

        Args:
            model_a_version: Version string for the control model.
            model_b_version: Version string for the challenger model.
            traffic_split: Percentage of requests (0–100) to route to model B.

        Returns:
            The newly created :class:`ABTestConfig`.

        **Validates: Requirement 16.6**
        """
        config = ABTestConfig(
            model_a_version=model_a_version,
            model_b_version=model_b_version,
            traffic_split=traffic_split,
        )
        self._state["mode"] = "ab_test"
        self._state["ab_config"] = config
        self._state["active_version"] = model_a_version  # control is the primary
        logger.info(
            "DeploymentManager: A/B test configured — "
            "model_a='%s' model_b='%s' split=%d%%.",
            model_a_version,
            model_b_version,
            traffic_split,
        )
        return config

    # ------------------------------------------------------------------
    # disable_ab_test
    # ------------------------------------------------------------------

    async def disable_ab_test(self, keep_version: Optional[str] = None) -> str:
        """Disable the active A/B test and revert to single-model mode.

        Args:
            keep_version: Which version to keep as the sole active model.
                Defaults to the control (``model_a_version``) when ``None``.
                Pass ``"b"`` to promote model B, or an explicit version string.

        Returns:
            The version string of the model left in service.

        **Validates: Requirement 16.6**
        """
        config: Optional[ABTestConfig] = self._state.get("ab_config")
        if config is None:
            logger.warning("DeploymentManager.disable_ab_test: no active A/B test.")
            return self._state.get("active_version") or VERSION_LATEST

        if keep_version is None or keep_version == "a":
            target_version = config.model_a_version
        elif keep_version == "b":
            target_version = config.model_b_version
        else:
            target_version = keep_version

        new_version = await self.hot_swap(target_version)
        logger.info(
            "DeploymentManager: A/B test disabled; serving version='%s'.",
            new_version,
        )
        return new_version

    # ------------------------------------------------------------------
    # select_version_for_request
    # ------------------------------------------------------------------

    def select_version_for_request(self) -> str:
        """Return the model version that should handle the current request.

        In single-model mode always returns the active version.
        In A/B test mode delegates to :func:`get_model_for_request`.

        Returns:
            A model version string.

        **Validates: Requirements 16.3, 16.6**
        """
        if self._state["mode"] == "ab_test" and self._state["ab_config"] is not None:
            return get_model_for_request(self._state["ab_config"])
        return self._state.get("active_version") or VERSION_LATEST

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"DeploymentManager("
            f"mode={self._state['mode']!r}, "
            f"active_version={self._state['active_version']!r})"
        )

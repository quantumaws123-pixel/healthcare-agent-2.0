"""
CORS (Cross-Origin Resource Sharing) middleware configuration for the
Healthcare Agent 2.0 Backend API.

Satisfies Requirement 1.9: The Backend_API SHALL handle CORS to allow
requests from the frontend application.

Origins can be extended via the CORS_ORIGINS environment variable
(comma-separated list).  When the variable is not set the module falls
back to the development defaults used by the Vite / React frontend.
"""

import os
import logging
from typing import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default origins shipped with the application
# ---------------------------------------------------------------------------

_DEFAULT_ORIGINS: list[str] = [
    "http://localhost:3000",   # Create React App / Next.js dev server
    "http://localhost:5173",   # Vite dev server (used by current frontend)
]


def _resolve_origins() -> list[str]:
    """
    Build the list of allowed CORS origins.

    Reads the ``CORS_ORIGINS`` environment variable (comma-separated).
    Falls back to ``_DEFAULT_ORIGINS`` when the variable is absent or
    empty.

    Returns:
        A deduplicated list of origin strings.
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        origins: list[str] = [o.strip() for o in raw.split(",") if o.strip()]
    else:
        origins = list(_DEFAULT_ORIGINS)

    # Remove duplicates while preserving insertion order
    seen: set[str] = set()
    unique: list[str] = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique.append(origin)

    return unique


def add_cors_middleware(app: FastAPI) -> None:
    """
    Attach CORS middleware to the FastAPI application.

    Configuration:
    - ``allow_origins``: loaded from the ``CORS_ORIGINS`` env var
      (defaults to localhost dev servers).
    - ``allow_credentials``: ``True`` — cookies / auth headers are
      forwarded so the frontend session management works correctly.
    - ``allow_methods``: all HTTP methods (``["*"]``).
    - ``allow_headers``: all headers (``["*"]``), including
      ``Authorization``, ``Content-Type``, and custom headers used by
      the frontend.

    Args:
        app: The FastAPI application instance to configure.
    """
    origins: Sequence[str] = _resolve_origins()

    logger.info(
        "Configuring CORS middleware with %d allowed origin(s): %s",
        len(origins),
        origins,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

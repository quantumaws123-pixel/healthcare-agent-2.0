"""
Structured JSON logging for the Healthcare Agent 2.0 Backend ML System.

Uses only Python's built-in ``logging`` module — no external logging
libraries are required.

Features:
- JSON-formatted log records with consistent field names
- Timestamp (ISO-8601), level, event/message, logger name, module,
  function, and line number in every record
- Optional ``context`` dict attached per-record or per-logger
- Configurable log level via the ``LOG_LEVEL`` environment variable
- Optional file output via the ``LOG_FILE`` environment variable

Satisfies Requirements 15.3, 15.4, 15.8.
"""

import json
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """
    Converts a :class:`logging.LogRecord` to a single-line JSON string.

    Output fields (always present):
        timestamp   – ISO-8601 UTC datetime
        level       – log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        event       – the formatted log message
        logger      – name of the logger that emitted the record
        module      – source module name
        function    – calling function name
        line        – line number in the source file

    Optional fields (added when present):
        context     – dict passed via ``extra={"context": {...}}``
        exc_info    – formatted exception traceback (when an exception is
                      attached to the record)
        extra_*     – any additional keys injected via ``extra=``
    """

    # Keys that are part of the standard LogRecord and should NOT be
    # re-emitted as generic extra fields.
    _SKIP_KEYS: frozenset[str] = frozenset({
        "args", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "message",
        "module", "msecs", "msg", "name", "pathname", "process",
        "processName", "relativeCreated", "stack_info", "taskName",
        "thread", "threadName",
    })

    def format(self, record: logging.LogRecord) -> str:
        # Render the message (applies % formatting to args)
        record.message = record.getMessage()

        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "event": record.message,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach exception traceback when present
        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_info"] = self.formatException(record.exc_info)
        elif record.exc_text:
            payload["exc_info"] = record.exc_text

        # Attach stack info when present
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        # Lift the ``context`` extra key to a top-level field
        context = getattr(record, "context", None)
        if context and isinstance(context, dict):
            payload["context"] = context

        # Forward any other extra keys (skip built-in LogRecord attrs)
        for key, value in record.__dict__.items():
            if key in self._SKIP_KEYS or key in ("message", "context"):
                continue
            if not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

def setup_logging(
    level: str | None = None,
    log_file: str | None = None,
    force: bool = False,
) -> None:
    """
    Configure root logger with structured JSON output.

    This function is idempotent — calling it multiple times without
    ``force=True`` is safe and will not duplicate handlers.

    Args:
        level:    Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to the ``LOG_LEVEL`` env var, then ``INFO``.
        log_file: Optional path to a rotating log file.  When provided a
                  ``RotatingFileHandler`` (10 MB, 5 backups) is added in
                  addition to the console handler.  Defaults to the
                  ``LOG_FILE`` env var.
        force:    When ``True``, remove existing handlers before adding new
                  ones.  Useful in test environments.
    """
    resolved_level_str: str = (
        level
        or os.getenv("LOG_LEVEL", "INFO")
    ).upper()

    numeric_level: int = getattr(logging, resolved_level_str, logging.INFO)

    root_logger = logging.getLogger()

    if root_logger.handlers and not force:
        # Already configured — nothing to do
        return

    if force:
        root_logger.handlers.clear()

    root_logger.setLevel(numeric_level)

    formatter = _JsonFormatter()

    # Console handler — writes to stdout so container runtimes capture it
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional rotating file handler
    resolved_log_file: str | None = log_file or os.getenv("LOG_FILE")
    if resolved_log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=resolved_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce verbosity from noisy third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str, context: dict[str, Any] | None = None) -> logging.Logger:
    """
    Return a named logger, optionally pre-seeded with context.

    When ``context`` is provided every log record emitted through the
    returned :class:`~logging.LoggerAdapter` will include the context
    dict as a top-level ``context`` field in the JSON output.

    Args:
        name:    Logger name — typically ``__name__`` of the calling module.
        context: Optional static key/value pairs to attach to all records
                 (e.g., ``{"service": "inference_engine", "model_version": "v1.2"}``).

    Returns:
        A :class:`logging.Logger` or :class:`logging.LoggerAdapter` with
        the requested name and context.

    Example::

        logger = get_logger(__name__, context={"patient_id": "P001"})
        logger.info("Prediction complete", extra={"risk_level": "High"})
    """
    base_logger = logging.getLogger(name)

    if context:
        return logging.LoggerAdapter(base_logger, extra={"context": context})

    return base_logger


# ---------------------------------------------------------------------------
# Module-level auto-setup
# ---------------------------------------------------------------------------
# Call setup_logging() when this module is first imported so that the
# application gets structured logging from the very first line of startup,
# even before app/main.py runs its own setup.  The idempotency guard in
# setup_logging() prevents double-initialisation.
setup_logging()

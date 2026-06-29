"""
Input sanitization utilities for the Healthcare Agent 2.0 Backend API.

Security layers implemented here:
  - XSS prevention via html.escape() and regex-based HTML tag stripping
  - Request payload size validation (max 1 MB)

SQL Injection prevention:
  This module does NOT need to sanitize SQL inputs directly because all
  database access is performed through SQLAlchemy's ORM or Core expression
  API, which uses parameterized queries / bound parameters exclusively.
  No raw string interpolation into SQL ever occurs in this codebase.

**Validates: Requirements 17.7, 17.8**
"""

import html
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 1 MB in bytes (Requirement 17.8)
MAX_REQUEST_BYTES: int = 1 * 1024 * 1024  # 1_048_576

# Matches any HTML/XML tag, e.g. <script>, </div>, <br/>, <!-- comment -->
_HTML_TAG_RE: re.Pattern[str] = re.compile(r"<[^>]*>", re.DOTALL)

# Matches common JavaScript event-handler attributes such as
# onerror="...", onclick='...', onload=..., etc.
_EVENT_HANDLER_RE: re.Pattern[str] = re.compile(
    r"\bon\w+\s*=\s*(?:[\"'][^\"']*[\"']|[^\s>]+)",
    re.IGNORECASE,
)

# Matches javascript: URIs often used in href/src attributes.
_JS_URI_RE: re.Pattern[str] = re.compile(r"javascript\s*:", re.IGNORECASE)


# ---------------------------------------------------------------------------
# XSS prevention
# ---------------------------------------------------------------------------

def strip_html_tags(value: str) -> str:
    """
    Remove all HTML/XML tags from *value* using a regex.

    This is a defence-in-depth measure applied **before** html.escape so
    that tag content is removed rather than rendered as escaped text to
    the end user.

    Args:
        value: Raw string that may contain HTML markup.

    Returns:
        The string with all HTML tags removed.

    Example::

        >>> strip_html_tags('<script>alert(1)</script>Hello')
        'Hello'
    """
    no_tags = _HTML_TAG_RE.sub("", value)
    # Also strip inline event handlers and javascript: URIs that might
    # survive tag removal when they appear outside of tag brackets.
    no_events = _EVENT_HANDLER_RE.sub("", no_tags)
    no_js_uri = _JS_URI_RE.sub("", no_events)
    return no_js_uri


def escape_html(value: str) -> str:
    """
    HTML-escape *value* so that any remaining special characters are safe
    to embed in HTML contexts.

    Uses Python's built-in :func:`html.escape` with ``quote=True`` to
    also escape single and double quote characters inside attribute
    values.

    Args:
        value: String to escape.

    Returns:
        HTML-safe string.

    Example::

        >>> escape_html('<b>hello & "world"</b>')
        '&lt;b&gt;hello &amp; &quot;world&quot;&lt;/b&gt;'
    """
    return html.escape(value, quote=True)


def sanitize_string(value: str) -> str:
    """
    Full XSS sanitization pipeline for a single string field.

    Steps applied in order:

    1. Strip HTML/XML tags with a regex.
    2. HTML-escape any remaining special characters.

    Args:
        value: Raw user-supplied string.

    Returns:
        Sanitized, HTML-safe string.

    **Validates: Requirement 17.7**
    """
    stripped = strip_html_tags(value)
    escaped = escape_html(stripped)
    return escaped


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.

    Non-string values are passed through unchanged.  Nested dicts and
    lists are traversed recursively.

    Args:
        data: Dictionary of potentially unsafe key/value pairs.

    Returns:
        New dictionary with all string values sanitized.

    **Validates: Requirement 17.7**
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        result[key] = _sanitize_value(value)
    return result


def _sanitize_value(value: Any) -> Any:
    """Recursively sanitize a single value of any supported type."""
    if isinstance(value, str):
        return sanitize_string(value)
    if isinstance(value, dict):
        return sanitize_dict(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Request size validation
# ---------------------------------------------------------------------------

def validate_request_size(content_length: int | None, body: bytes | None = None) -> bool:
    """
    Check whether the request payload is within the 1 MB limit.

    Accepts either the ``Content-Length`` header value **or** the actual
    request body bytes (or both).  When a ``Content-Length`` header is
    present it is checked first (cheap path); the body length is used as
    a fallback for chunked transfers where the header may be absent.

    Args:
        content_length: Value of the HTTP ``Content-Length`` header, or
                        ``None`` when the header is not present.
        body:           Raw request body bytes, or ``None`` when not yet
                        read.

    Returns:
        ``True`` if the payload is within the allowed limit (or the size
        cannot be determined), ``False`` if it exceeds 1 MB.

    **Validates: Requirement 17.8**
    """
    if content_length is not None and content_length > MAX_REQUEST_BYTES:
        logger.warning(
            "Request rejected: Content-Length %d exceeds max allowed %d bytes",
            content_length,
            MAX_REQUEST_BYTES,
        )
        return False

    if body is not None and len(body) > MAX_REQUEST_BYTES:
        logger.warning(
            "Request rejected: body size %d bytes exceeds max allowed %d bytes",
            len(body),
            MAX_REQUEST_BYTES,
        )
        return False

    return True


def assert_request_size(content_length: int | None, body: bytes | None = None) -> None:
    """
    Raise a :class:`ValueError` if the request payload exceeds 1 MB.

    Convenience wrapper around :func:`validate_request_size` for use in
    FastAPI request handlers or middleware.

    Args:
        content_length: HTTP ``Content-Length`` header value or ``None``.
        body:           Raw request body bytes or ``None``.

    Raises:
        ValueError: When the payload size exceeds the 1 MB limit.

    **Validates: Requirement 17.8**
    """
    if not validate_request_size(content_length, body):
        raise ValueError(
            f"Request payload exceeds the maximum allowed size of "
            f"{MAX_REQUEST_BYTES // (1024 * 1024)} MB."
        )

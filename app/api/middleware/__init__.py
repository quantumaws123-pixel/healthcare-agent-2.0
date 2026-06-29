"""
Middleware package for the Healthcare Agent 2.0 Backend API.
"""

from app.api.middleware.error_handler import register_exception_handlers
from app.api.middleware.cors import add_cors_middleware

__all__ = ["register_exception_handlers", "add_cors_middleware"]

"""
Exception hierarchy for Sage Finance OS.

Adapted from Jake's shared/errors.py — clean hierarchy with HTTP status codes
and structured error payloads for centralized handling.
"""

from __future__ import annotations


class SageError(Exception):
    """Base exception for all Sage Finance OS errors."""

    status_code: int = 500
    error_type: str = "internal_error"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error": self.error_type,
            "message": self.message,
            "details": self.details,
        }


# ── Client errors (4xx) ─────────────────────────────────────────

class ValidationError(SageError):
    status_code = 422
    error_type = "validation_error"


class NotFoundError(SageError):
    status_code = 404
    error_type = "not_found"


class AuthenticationError(SageError):
    status_code = 401
    error_type = "authentication_error"


class AuthorizationError(SageError):
    status_code = 403
    error_type = "authorization_error"


class ConflictError(SageError):
    status_code = 409
    error_type = "conflict"


class RateLimitError(SageError):
    status_code = 429
    error_type = "rate_limit_exceeded"


# ── Server errors (5xx) ─────────────────────────────────────────

class DatabaseError(SageError):
    status_code = 500
    error_type = "database_error"


class ExternalServiceError(SageError):
    status_code = 502
    error_type = "external_service_error"


class ServiceUnavailableError(SageError):
    status_code = 503
    error_type = "service_unavailable"


# ── Domain errors ────────────────────────────────────────────────

class PipelineError(SageError):
    status_code = 500
    error_type = "pipeline_error"


class QualityGateError(SageError):
    status_code = 422
    error_type = "quality_gate_failed"


class ConnectorError(ExternalServiceError):
    error_type = "connector_error"


class KillSwitchError(SageError):
    status_code = 403
    error_type = "kill_switch_active"

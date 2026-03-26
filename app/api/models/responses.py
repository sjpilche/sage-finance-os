"""
Standard response envelope — adapted from Jake's backend/api/models/responses.py.

All API responses use this envelope for consistency:
    { "data": T, "meta": { "generated_at", "refreshed_at", "is_stale", ... } }
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMetadata(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    refreshed_at: datetime | None = None
    is_stale: bool = False
    version: str = "1.0"
    correlation_id: str | None = None


class StandardResponse(BaseModel, Generic[T]):
    """Envelope for all API responses."""

    data: T
    meta: ResponseMetadata = Field(default_factory=ResponseMetadata)
    errors: list[str] = Field(default_factory=list)

    @classmethod
    def ok(cls, data: Any, **meta_kwargs) -> "StandardResponse":
        return cls(data=data, meta=ResponseMetadata(**meta_kwargs))

    @classmethod
    def error(cls, message: str) -> "StandardResponse":
        return cls(data=None, errors=[message])


def wrap_response(
    data: Any,
    refreshed_at: datetime | None = None,
    is_stale: bool = False,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for routes that return plain dicts."""
    meta = ResponseMetadata(
        refreshed_at=refreshed_at,
        is_stale=is_stale,
        correlation_id=correlation_id,
    )
    return {
        "data": data,
        "meta": meta.model_dump(mode="json"),
    }

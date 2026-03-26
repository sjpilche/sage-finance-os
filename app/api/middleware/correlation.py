"""
Correlation ID middleware — generates a unique request ID for every request.

Adapted from Jake's correlation middleware. Sets X-Request-ID header on
responses and makes the ID available via contextvars for structured logging.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context var accessible from anywhere in the request lifecycle
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use incoming X-Request-ID if present, otherwise generate one
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(req_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

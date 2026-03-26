"""
Authentication middleware — adapted from Jake.

Supports two auth methods:
1. Bearer JWT token (for human users)
2. X-API-Key header (for service-to-service calls)

In development mode, auth can be bypassed via ENVIRONMENT=development.
"""

from __future__ import annotations

import logging

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.tokens import verify_token
from app.config import Settings, get_settings
from app.core.errors import AuthenticationError

log = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# Paths that never require auth
_PUBLIC_PATHS = frozenset({"/health", "/health/deep", "/docs", "/openapi.json"})


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    x_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Authenticate the request via JWT or API key. Returns identity dict."""
    # Skip auth for public endpoints
    if request.url.path in _PUBLIC_PATHS:
        return {"sub": "anonymous", "auth_method": "none"}

    # Dev passthrough
    if settings.ENVIRONMENT == "development" and not credentials and not x_api_key:
        return {"sub": "dev-user", "auth_method": "dev_passthrough"}

    # Try API key first
    if x_api_key:
        if x_api_key == settings.API_KEY:
            return {"sub": "api-client", "auth_method": "api_key"}
        raise AuthenticationError("Invalid API key")

    # Try Bearer JWT
    if credentials:
        payload = verify_token(credentials.credentials)
        return {
            "sub": payload.get("sub", "unknown"),
            "auth_method": "jwt",
            "claims": payload,
        }

    raise AuthenticationError("No authentication credentials provided")

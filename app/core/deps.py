"""
FastAPI dependency injection — shared request-scoped dependencies.
"""

from __future__ import annotations

from typing import AsyncGenerator

import asyncpg
from fastapi import Depends, Header

from app.config import Settings, get_settings
from app.core.db import get_pool
from app.core.errors import AuthenticationError


async def require_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Yield an async DB connection for the duration of a request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def require_api_key(
    x_api_key: str = Header(None),
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate API key from X-API-Key header. Returns the key if valid."""
    if not x_api_key:
        raise AuthenticationError("Missing X-API-Key header")
    if x_api_key != settings.API_KEY:
        raise AuthenticationError("Invalid API key")
    return x_api_key

"""
Async database connection pool (asyncpg) — for API layer.

Adapted from Jake's backend/database/connection.py.
Provides a managed async pool with JSON codec support.
"""

from __future__ import annotations

import json
import logging

import asyncpg

from app.config import get_settings

log = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Set up JSON codec on each new connection."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def get_pool() -> asyncpg.Pool:
    """Return the singleton connection pool, creating it on first call."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=settings.DB_POOL_MIN,
            max_size=settings.DB_POOL_MAX,
            command_timeout=settings.DB_COMMAND_TIMEOUT,
            init=_init_connection,
        )
        log.info("async_pool_created min_size=%d max_size=%d", settings.DB_POOL_MIN, settings.DB_POOL_MAX)
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        log.info("async_pool_closed")


async def acquire():
    """Acquire a connection from the pool (async context manager)."""
    pool = await get_pool()
    return pool.acquire()

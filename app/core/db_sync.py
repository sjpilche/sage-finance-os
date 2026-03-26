"""
Sync database connection pool (psycopg2) — for pipeline layer.

Adapted from DataClean's core/db.py. Pipeline steps run synchronously
inside a thread (dispatched via asyncio.to_thread from the API layer).

Usage:
    with get_cursor() as cur:
        cur.execute("SELECT ...")
        rows = cur.fetchall()

    with get_write_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT ...")
        conn.commit()
"""

from __future__ import annotations

import logging
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool as pg_pool

from app.config import get_settings

log = logging.getLogger(__name__)

_pool: pg_pool.ThreadedConnectionPool | None = None


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    """Return the singleton sync pool, creating on first call."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = pg_pool.ThreadedConnectionPool(
            minconn=settings.DB_SYNC_POOL_MIN,
            maxconn=settings.DB_SYNC_POOL_MAX,
            dsn=settings.DATABASE_URL_SYNC,
        )
        log.info(
            "sync_pool_created",
            min_size=settings.DB_SYNC_POOL_MIN,
            max_size=settings.DB_SYNC_POOL_MAX,
        )
    return _pool


def close_sync_pool() -> None:
    """Gracefully close the sync connection pool."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        log.info("sync_pool_closed")


@contextmanager
def get_cursor():
    """Read-only cursor with autocommit. Connection returned to pool on exit."""
    p = _get_pool()
    conn = p.getconn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            yield cur
    finally:
        p.putconn(conn)


@contextmanager
def get_write_connection():
    """Writable connection — caller must explicitly commit.

    Usage:
        with get_write_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
            conn.commit()
    """
    p = _get_pool()
    conn = p.getconn()
    try:
        conn.autocommit = False
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)

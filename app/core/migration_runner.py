"""
SQL-file migration runner.

Runs numbered .sql files from sql/migrations/ in order.
Tracks applied migrations in platform.schema_migrations.
Each file should be idempotent (CREATE TABLE IF NOT EXISTS, etc.).
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

import psycopg2

from app.config import get_settings

log = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "sql" / "migrations"
MAX_RETRIES = 5
INITIAL_BACKOFF_S = 1

_BOOTSTRAP_SQL = """
CREATE SCHEMA IF NOT EXISTS platform;

CREATE TABLE IF NOT EXISTS platform.schema_migrations (
    migration_id    TEXT PRIMARY KEY,
    filename        TEXT NOT NULL,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def _get_migration_files() -> list[tuple[str, Path]]:
    """Return sorted list of (migration_id, path) from the migrations directory."""
    if not MIGRATIONS_DIR.exists():
        return []

    pattern = re.compile(r"^(\d{3}_.+)\.sql$")
    files = []
    for f in sorted(MIGRATIONS_DIR.iterdir()):
        m = pattern.match(f.name)
        if m:
            files.append((m.group(1), f))
    return files


def _connect_with_retry(dsn: str) -> psycopg2.extensions.connection:
    """Connect to PostgreSQL with exponential backoff retry."""
    backoff = INITIAL_BACKOFF_S
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = psycopg2.connect(dsn)
            if attempt > 1:
                log.info("db_connected attempt=%d", attempt)
            return conn
        except psycopg2.OperationalError as e:
            if attempt == MAX_RETRIES:
                log.error("db_connect_failed attempts=%d error=%s", MAX_RETRIES, e)
                raise
            log.warning("db_connect_retry attempt=%d/%d backoff=%ds error=%s", attempt, MAX_RETRIES, backoff, e)
            time.sleep(backoff)
            backoff *= 2


def run_migrations(dsn: str | None = None) -> int:
    """Apply all pending migrations. Returns count of newly applied migrations."""
    if dsn is None:
        dsn = get_settings().DATABASE_URL_SYNC

    conn = _connect_with_retry(dsn)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            # Ensure the tracking table exists
            cur.execute(_BOOTSTRAP_SQL)

            # Get already-applied migrations
            cur.execute("SELECT migration_id FROM platform.schema_migrations")
            applied = {row[0] for row in cur.fetchall()}

        files = _get_migration_files()
        applied_count = 0

        for migration_id, filepath in files:
            if migration_id in applied:
                continue

            log.info("applying_migration", migration_id=migration_id, file=filepath.name)
            sql = filepath.read_text(encoding="utf-8")

            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO platform.schema_migrations (migration_id, filename) "
                    "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (migration_id, filepath.name),
                )

            applied_count += 1
            log.info("migration_applied", migration_id=migration_id)

        if applied_count == 0:
            log.info("no_pending_migrations")
        else:
            log.info("migrations_complete", count=applied_count)

        return applied_count

    finally:
        conn.close()

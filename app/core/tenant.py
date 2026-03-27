"""
RunContext — immutable context threaded through all pipeline steps.

Adapted from DataClean's core/tenant.py. Simplified for single-tenant V1:
- No schema-per-tenant isolation
- No plan tiers
- Keeps the core lifecycle: create_run, update_status, complete, fail
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# Schema names (shared, single set)
SCHEMAS = {
    "platform": "platform",
    "staging": "staging",
    "contract": "contract",
    "audit": "audit",
    "workflow": "workflow",
    "semantic": "semantic",
}


@dataclass
class RunContext:
    """Immutable context bag threaded through all pipeline steps."""

    run_id: str
    tenant_id: str
    source_type: str = "sage_intacct"
    connection_id: str | None = None
    mode: str = "full"  # "full" or "incremental"
    schemas: dict[str, str] = field(default_factory=lambda: dict(SCHEMAS))
    started_at: datetime | None = None

    def schema(self, name: str) -> str:
        """Return the actual schema name for logical name."""
        return self.schemas.get(name, name)


def create_run(
    conn,
    tenant_id: str,
    source_type: str = "sage_intacct",
    connection_id: str | None = None,
    mode: str = "full",
) -> RunContext:
    """Create a new data run and return a RunContext."""
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO platform.data_runs
                (run_id, tenant_id, connection_id, source_type, mode, status, started_at)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s)
            """,
            (run_id, tenant_id, connection_id, source_type, mode, now),
        )
    conn.commit()

    log.info("run_created run_id=%s tenant_id=%s source_type=%s mode=%s", run_id, tenant_id, source_type, mode)

    return RunContext(
        run_id=run_id,
        tenant_id=tenant_id,
        source_type=source_type,
        connection_id=connection_id,
        mode=mode,
        started_at=now,
    )


def update_run_status(conn, run_id: str, status: str) -> None:
    """Update the run status in platform.data_runs."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE platform.data_runs SET status = %s WHERE run_id = %s",
            (status, run_id),
        )
    conn.commit()
    log.info("run_status_updated run_id=%s status=%s", run_id, status)


def complete_run(conn, run_id: str, summary: dict | None = None) -> None:
    """Mark run as complete with optional summary."""
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE platform.data_runs
            SET status = 'complete', completed_at = %s, summary = %s
            WHERE run_id = %s
            """,
            (now, json.dumps(summary) if summary else None, run_id),
        )
    conn.commit()
    log.info("run_completed run_id=%s", run_id)


def fail_run(conn, run_id: str, error_message: str) -> None:
    """Mark run as failed."""
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE platform.data_runs
            SET status = 'failed', completed_at = %s, error_message = %s
            WHERE run_id = %s
            """,
            (now, error_message[:2000], run_id),
        )
    conn.commit()
    log.error("run_failed run_id=%s error=%s", run_id, error_message[:200])

"""
Sync endpoints — trigger and monitor Sage Intacct data syncs.

POST   /v1/sync/trigger         — Trigger a new sync run
GET    /v1/sync/runs             — List recent sync runs
GET    /v1/sync/runs/{run_id}    — Get run detail
GET    /v1/sync/schema           — Get available objects from Sage Intacct
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.models.responses import wrap_response
from app.core.deps import require_db
from app.core.errors import NotFoundError, ValidationError
from app.ingestion.connectors.sage_intacct import SageIntacctConnector
from app.ingestion.connectors.sage_intacct.objects import OBJECT_CATALOG, OBJECT_NAMES

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/sync", tags=["sync"])

_DEFAULT_TENANT = "default"


class SyncTrigger(BaseModel):
    connection_id: str
    objects: list[str] | None = None  # None = all objects
    mode: str = "full"  # "full" or "incremental"


async def _get_default_tenant_id(conn: asyncpg.Connection) -> str:
    row = await conn.fetchrow(
        "SELECT tenant_id FROM platform.tenants WHERE slug = $1", _DEFAULT_TENANT
    )
    if not row:
        raise ValidationError("Default tenant not found")
    return str(row["tenant_id"])


@router.post("/trigger")
async def trigger_sync(body: SyncTrigger, conn: asyncpg.Connection = Depends(require_db)):
    """
    Trigger a new sync run. Extracts data from Sage Intacct and stages
    raw records for pipeline processing.

    This is an async operation — returns the run_id immediately.
    Use GET /v1/sync/runs/{run_id} to monitor progress.
    """
    tenant_id = await _get_default_tenant_id(conn)

    # Validate connection exists
    conn_row = await conn.fetchrow(
        "SELECT connection_id, credentials, status FROM platform.connections WHERE connection_id = $1",
        UUID(body.connection_id),
    )
    if not conn_row:
        raise NotFoundError(f"Connection {body.connection_id} not found")
    if conn_row["status"] != "active":
        raise ValidationError(f"Connection is not active (status: {conn_row['status']}). Test it first.")

    # Validate requested objects
    objects = body.objects or OBJECT_NAMES
    invalid = [o for o in objects if o not in OBJECT_CATALOG]
    if invalid:
        raise ValidationError(f"Unknown objects: {invalid}. Valid: {sorted(OBJECT_NAMES)}")

    creds = json.loads(conn_row["credentials"]) if conn_row["credentials"] else {}

    # Launch pipeline in background thread
    async def _run_pipeline():
        """Background pipeline task — extract + write to contract tables."""
        from app.core.db_sync import get_write_connection
        from app.pipeline.runner import run_pipeline

        try:
            with get_write_connection() as sync_conn:
                result = run_pipeline(
                    conn=sync_conn,
                    tenant_id=tenant_id,
                    connection_id=body.connection_id,
                    credentials=creds,
                    objects=objects,
                    mode=body.mode,
                )
            log.info("sync: pipeline result — %s", result.get("status"))
        except Exception as e:
            log.error("sync: pipeline failed — %s", e, exc_info=True)

    asyncio.create_task(_run_pipeline())

    # Return immediately — pipeline runs in background
    run_id = "pending"  # actual run_id created by pipeline runner

    return wrap_response({
        "run_id": run_id,
        "status": "extracting",
        "objects": objects,
        "mode": body.mode,
        "message": "Sync started. Monitor via GET /v1/sync/runs/{run_id}",
    })


@router.get("/runs")
async def list_runs(
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(require_db),
):
    """List recent sync runs."""
    tenant_id = await _get_default_tenant_id(conn)

    rows = await conn.fetch(
        """
        SELECT run_id, connection_id, source_type, mode, status,
               started_at, completed_at, summary, error_message
        FROM platform.data_runs
        WHERE tenant_id = $1
        ORDER BY started_at DESC
        LIMIT $2
        """,
        tenant_id, limit,
    )

    runs = [
        {
            "run_id": str(r["run_id"]),
            "connection_id": str(r["connection_id"]) if r["connection_id"] else None,
            "source_type": r["source_type"],
            "mode": r["mode"],
            "status": r["status"],
            "started_at": r["started_at"].isoformat(),
            "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
            "summary": r["summary"],
            "error_message": r["error_message"],
        }
        for r in rows
    ]

    return wrap_response(runs)


@router.get("/runs/{run_id}")
async def get_run(run_id: UUID, conn: asyncpg.Connection = Depends(require_db)):
    """Get sync run detail."""
    row = await conn.fetchrow(
        """
        SELECT run_id, connection_id, source_type, mode, status,
               started_at, completed_at, summary, error_message
        FROM platform.data_runs
        WHERE run_id = $1
        """,
        run_id,
    )
    if not row:
        raise NotFoundError(f"Run {run_id} not found")

    return wrap_response({
        "run_id": str(row["run_id"]),
        "connection_id": str(row["connection_id"]) if row["connection_id"] else None,
        "source_type": row["source_type"],
        "mode": row["mode"],
        "status": row["status"],
        "started_at": row["started_at"].isoformat(),
        "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
        "summary": row["summary"],
        "error_message": row["error_message"],
    })


@router.get("/schema")
async def get_schema(
    connection_id: str = Query(..., description="Connection UUID"),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Get available Sage Intacct objects with estimated row counts."""
    conn_row = await conn.fetchrow(
        "SELECT credentials FROM platform.connections WHERE connection_id = $1",
        UUID(connection_id),
    )
    if not conn_row:
        raise NotFoundError(f"Connection {connection_id} not found")

    creds = json.loads(conn_row["credentials"]) if conn_row["credentials"] else {}

    def _get_schema():
        connector = SageIntacctConnector(config=creds)
        return connector.get_schema()

    schema = await asyncio.to_thread(_get_schema)
    return wrap_response(schema)


def _get_watermark_sync(creds: dict, tenant_id: str, connection_id: str, object_name: str) -> str | None:
    """Sync helper to get watermark (runs in thread, uses sync DB)."""
    from app.core.db_sync import get_cursor
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT last_value FROM platform.watermarks
                WHERE tenant_id = %s AND connection_id = %s AND object_name = %s
                """,
                (tenant_id, connection_id, object_name),
            )
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None

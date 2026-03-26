"""
Platform endpoints — data freshness, scheduler status, kill switch.

GET  /v1/platform/freshness          — Data freshness per object
GET  /v1/platform/scheduler          — Scheduled job status
GET  /v1/platform/kill-switch        — Kill switch status
POST /v1/platform/kill-switch/activate   — Activate kill switch
POST /v1/platform/kill-switch/deactivate — Deactivate kill switch
GET  /v1/platform/events             — Recent events
"""

from __future__ import annotations

import asyncio
import logging

import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.models.responses import wrap_response
from app.core.deps import require_db
from app.core.errors import ValidationError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/platform", tags=["platform"])

_DEFAULT_TENANT = "default"


async def _get_default_tenant_id(conn: asyncpg.Connection) -> str:
    row = await conn.fetchrow("SELECT tenant_id FROM platform.tenants WHERE slug = $1", _DEFAULT_TENANT)
    if not row:
        raise ValidationError("Default tenant not found")
    return str(row["tenant_id"])


@router.get("/freshness")
async def data_freshness(conn: asyncpg.Connection = Depends(require_db)):
    """Data freshness per Sage Intacct object — last sync time and staleness."""
    tenant_id = await _get_default_tenant_id(conn)

    rows = await conn.fetch(
        """
        SELECT object_name, last_value, last_sync_at, row_count,
               EXTRACT(EPOCH FROM (now() - last_sync_at)) / 3600 AS hours_since
        FROM platform.watermarks
        WHERE tenant_id = $1
        ORDER BY object_name
        """,
        tenant_id,
    )

    objects = []
    for r in rows:
        hours = float(r["hours_since"]) if r["hours_since"] else None
        objects.append({
            "object_name": r["object_name"],
            "last_sync_at": r["last_sync_at"].isoformat() if r["last_sync_at"] else None,
            "hours_since_sync": round(hours, 1) if hours else None,
            "is_stale": hours > 8 if hours else True,
            "row_count": r["row_count"],
        })

    # Overall freshness
    last_sync = await conn.fetchval(
        "SELECT MAX(completed_at) FROM platform.data_runs WHERE tenant_id = $1 AND status = 'complete'",
        tenant_id,
    )

    return wrap_response({
        "last_sync": last_sync.isoformat() if last_sync else None,
        "objects": objects,
    })


@router.get("/scheduler")
async def scheduler_status():
    """Get scheduled job status."""
    from app.workflows.scheduler import get_job_status
    return wrap_response(get_job_status())


class KillSwitchAction(BaseModel):
    scope: str = "global"
    mode: str = "hard"
    reason: str = ""
    actor: str = "api"


@router.get("/kill-switch")
async def kill_switch_status(conn: asyncpg.Connection = Depends(require_db)):
    """Get kill switch status for all scopes."""
    rows = await conn.fetch(
        """
        SELECT scope, mode, is_active, activated_by, reason, activated_at, deactivated_at
        FROM workflow.kill_switch_rules
        ORDER BY scope
        """
    )
    return wrap_response([dict(r) for r in rows])


@router.post("/kill-switch/activate")
async def activate_kill_switch(body: KillSwitchAction):
    """Activate the kill switch."""
    from app.workflows.kill_switch import activate
    from app.core.db_sync import get_write_connection

    def _activate():
        with get_write_connection() as sc:
            return activate(sc, body.scope, body.mode, body.reason, body.actor)

    result = await asyncio.to_thread(_activate)
    return wrap_response(result)


@router.post("/kill-switch/deactivate")
async def deactivate_kill_switch(body: KillSwitchAction):
    """Deactivate the kill switch."""
    from app.workflows.kill_switch import deactivate
    from app.core.db_sync import get_write_connection

    def _deactivate():
        with get_write_connection() as sc:
            return deactivate(sc, body.scope, body.actor, body.reason)

    result = await asyncio.to_thread(_deactivate)
    return wrap_response(result)


@router.get("/events")
async def list_events(
    limit: int = Query(50, ge=1, le=500),
    event_type: str | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """List recent events from the event bus."""
    conditions = []
    params = []
    idx = 1

    if event_type:
        conditions.append(f"event_type = ${idx}")
        params.append(event_type)
        idx += 1

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = await conn.fetch(
        f"""
        SELECT event_id, event_type, source, payload, created_at
        FROM workflow.events {where}
        ORDER BY created_at DESC
        LIMIT ${idx}
        """,
        *params, limit,
    )

    return wrap_response([dict(r) for r in rows])

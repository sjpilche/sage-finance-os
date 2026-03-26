"""
Quality endpoints — scorecards, DQ results, certificates.

GET  /v1/quality/scorecards          — List scorecards
GET  /v1/quality/scorecards/{run_id} — Get scorecard for a run
GET  /v1/quality/checks/{run_id}     — Get DQ check results for a run
GET  /v1/quality/certificates        — List certificates
POST /v1/quality/quarantine/{run_id}/release — Release a quarantined run
"""

from __future__ import annotations

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.models.responses import wrap_response
from app.core.deps import require_db
from app.core.errors import NotFoundError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/quality", tags=["quality"])


@router.get("/scorecards")
async def list_scorecards(
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(require_db),
):
    """List recent scorecards."""
    rows = await conn.fetch(
        """
        SELECT scorecard_id, run_id, tenant_id, accuracy, completeness,
               consistency, validity, uniqueness, timeliness, composite,
               gate_status, created_at
        FROM audit.scorecard_results
        ORDER BY created_at DESC
        LIMIT $1
        """,
        limit,
    )
    return wrap_response([dict(r) for r in rows])


@router.get("/scorecards/{run_id}")
async def get_scorecard(run_id: UUID, conn: asyncpg.Connection = Depends(require_db)):
    """Get scorecard for a specific run."""
    row = await conn.fetchrow(
        """
        SELECT scorecard_id, run_id, tenant_id, accuracy, completeness,
               consistency, validity, uniqueness, timeliness, composite,
               gate_status, created_at
        FROM audit.scorecard_results
        WHERE run_id = $1
        """,
        run_id,
    )
    if not row:
        raise NotFoundError(f"No scorecard for run {run_id}")
    return wrap_response(dict(row))


@router.get("/checks/{run_id}")
async def get_dq_checks(run_id: UUID, conn: asyncpg.Connection = Depends(require_db)):
    """Get DQ check results for a specific run."""
    rows = await conn.fetch(
        """
        SELECT result_id, object_name, check_name, passed, severity, details, created_at
        FROM platform.dq_results
        WHERE run_id = $1
        ORDER BY severity DESC, object_name, check_name
        """,
        run_id,
    )
    if not rows:
        raise NotFoundError(f"No DQ results for run {run_id}")

    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])

    return wrap_response({
        "run_id": str(run_id),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total > 0 else 1.0,
        "checks": [dict(r) for r in rows],
    })


@router.get("/certificates")
async def list_certificates(
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(require_db),
):
    """List recent certificates."""
    rows = await conn.fetch(
        """
        SELECT certificate_id, run_id, tenant_id, signature,
               scorecard_snapshot, issued_at
        FROM audit.certificates
        ORDER BY issued_at DESC
        LIMIT $1
        """,
        limit,
    )
    return wrap_response([dict(r) for r in rows])


class QuarantineRelease(BaseModel):
    approver: str
    reason: str


@router.post("/quarantine/{run_id}/release")
async def release_quarantine(
    run_id: UUID,
    body: QuarantineRelease,
    conn: asyncpg.Connection = Depends(require_db),
):
    """Release a quarantined run (requires approver + reason)."""
    import asyncio
    from app.core.db_sync import get_write_connection
    from app.trust.circuit_breaker import release_quarantine as _release

    # Get tenant_id for the run
    row = await conn.fetchrow(
        "SELECT tenant_id FROM platform.data_runs WHERE run_id = $1", run_id,
    )
    if not row:
        raise NotFoundError(f"Run {run_id} not found")

    tenant_id = str(row["tenant_id"])

    def _do_release():
        with get_write_connection() as sync_conn:
            return _release(sync_conn, str(run_id), tenant_id, body.approver, body.reason)

    result = await asyncio.to_thread(_do_release)
    return wrap_response(result)

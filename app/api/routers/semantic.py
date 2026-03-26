"""
Semantic layer endpoints — metrics, KPIs, financial statements.

GET  /v1/semantic/metrics           — List all metric definitions
GET  /v1/semantic/kpis              — Get computed KPIs
POST /v1/semantic/kpis/compute      — Trigger KPI computation
GET  /v1/semantic/financials/pl     — Income Statement
GET  /v1/semantic/financials/bs     — Balance Sheet (placeholder)
GET  /v1/semantic/periods           — Period status
POST /v1/semantic/periods/close     — Close a period
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date

import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.models.responses import wrap_response
from app.core.deps import require_db
from app.core.errors import ValidationError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/semantic", tags=["semantic"])

_DEFAULT_TENANT = "default"


async def _get_default_tenant_id(conn: asyncpg.Connection) -> str:
    row = await conn.fetchrow(
        "SELECT tenant_id FROM platform.tenants WHERE slug = $1", _DEFAULT_TENANT
    )
    if not row:
        raise ValidationError("Default tenant not found")
    return str(row["tenant_id"])


@router.get("/metrics")
async def list_metrics():
    """List all metric definitions from the registry."""
    from app.semantic.metric_registry import METRICS, get_metrics_by_category

    by_category = get_metrics_by_category()
    result = {}
    for category, metrics in by_category.items():
        result[category] = [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "unit": m.unit,
                "direction": m.direction,
            }
            for m in metrics
        ]

    return wrap_response({
        "total": len(METRICS),
        "categories": result,
    })


@router.get("/kpis")
async def get_kpis(
    fiscal_year: int | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Get computed KPI values."""
    tenant_id = await _get_default_tenant_id(conn)

    from app.semantic.kpi_engine import get_kpis as _get_kpis
    from app.core.db_sync import get_cursor

    def _fetch():
        with get_cursor() as cur:
            # Reuse the sync cursor approach since kpi_engine uses sync
            pass

    # Use async query directly
    conditions = ["tenant_id = $1"]
    params: list = [tenant_id]
    idx = 2

    if fiscal_year:
        conditions.append(f"fiscal_year = ${idx}")
        params.append(fiscal_year)
        idx += 1

    where = " AND ".join(conditions)

    rows = await conn.fetch(
        f"""
        SELECT metric_name, fiscal_year, fiscal_period, value, unit, computed_at
        FROM semantic.computed_kpis
        WHERE {where}
        ORDER BY metric_name, fiscal_year, fiscal_period
        """,
        *params,
    )

    from app.semantic.metric_registry import METRICS

    kpis = []
    for r in rows:
        metric_def = METRICS.get(r["metric_name"])
        kpis.append({
            "metric_name": r["metric_name"],
            "display_name": metric_def.display_name if metric_def else r["metric_name"],
            "category": metric_def.category if metric_def else "unknown",
            "direction": metric_def.direction if metric_def else "neutral",
            "fiscal_year": r["fiscal_year"],
            "fiscal_period": r["fiscal_period"],
            "value": float(r["value"]) if r["value"] is not None else None,
            "unit": r["unit"],
            "computed_at": r["computed_at"].isoformat() if r["computed_at"] else None,
        })

    return wrap_response(kpis)


class ComputeKPIs(BaseModel):
    fiscal_year: int
    fiscal_period: int | None = None


@router.post("/kpis/compute")
async def compute_kpis(
    body: ComputeKPIs,
    conn: asyncpg.Connection = Depends(require_db),
):
    """Trigger KPI computation for a fiscal year/period."""
    tenant_id = await _get_default_tenant_id(conn)

    from app.semantic.kpi_engine import compute_all_kpis
    from app.core.db_sync import get_write_connection

    def _compute():
        with get_write_connection() as sync_conn:
            return compute_all_kpis(
                sync_conn, tenant_id,
                fiscal_year=body.fiscal_year,
                fiscal_period=body.fiscal_period,
            )

    results = await asyncio.to_thread(_compute)

    computed = {k: v for k, v in results.items() if v is not None}
    return wrap_response({
        "fiscal_year": body.fiscal_year,
        "fiscal_period": body.fiscal_period,
        "computed": len(computed),
        "total_metrics": len(results),
        "kpis": computed,
    })


@router.get("/financials/pl")
async def get_income_statement(
    fiscal_year: int = Query(...),
    fiscal_period: int | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Generate an income statement from GL data."""
    tenant_id = await _get_default_tenant_id(conn)

    from app.semantic.kpi_engine import build_income_statement
    from app.core.db_sync import get_cursor

    def _build():
        with get_cursor() as cur:
            # Need the connection, not cursor — get from pool
            pass

    from app.core.db_sync import get_write_connection

    def _build_pl():
        with get_write_connection() as sync_conn:
            return build_income_statement(sync_conn, tenant_id, fiscal_year, fiscal_period)

    lines = await asyncio.to_thread(_build_pl)

    return wrap_response({
        "statement": "income_statement",
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "lines": lines,
    })


@router.get("/financials/bs")
async def get_balance_sheet(
    fiscal_year: int = Query(...),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Balance sheet — placeholder, same pattern as P&L."""
    tenant_id = await _get_default_tenant_id(conn)

    # For V1, return TB-based balance sheet summary
    rows = await conn.fetch(
        """
        SELECT c.account_type,
               COALESCE(SUM(tb.ending_balance), 0) AS total
        FROM contract.trial_balance tb
        JOIN contract.chart_of_accounts c
            ON tb.account_number = c.account_number AND tb.tenant_id = c.tenant_id
        WHERE tb.tenant_id = $1
        GROUP BY c.account_type
        ORDER BY c.account_type
        """,
        tenant_id,
    )

    sections = {r["account_type"]: float(r["total"]) for r in rows}

    return wrap_response({
        "statement": "balance_sheet",
        "fiscal_year": fiscal_year,
        "sections": sections,
        "total_assets": sections.get("Asset", 0),
        "total_liabilities": sections.get("Liability", 0),
        "total_equity": sections.get("Equity", 0),
    })


@router.get("/periods")
async def list_periods(
    fiscal_year: int | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """List period statuses."""
    tenant_id = await _get_default_tenant_id(conn)

    conditions = ["tenant_id = $1"]
    params: list = [tenant_id]
    idx = 2

    if fiscal_year:
        conditions.append(f"fiscal_year = ${idx}")
        params.append(fiscal_year)

    where = " AND ".join(conditions)

    rows = await conn.fetch(
        f"""
        SELECT fiscal_year, fiscal_period, status, closed_by, closed_at
        FROM semantic.period_status
        WHERE {where}
        ORDER BY fiscal_year DESC, fiscal_period DESC
        """,
        *params,
    )

    return wrap_response([dict(r) for r in rows])


class PeriodClose(BaseModel):
    fiscal_year: int
    fiscal_period: int
    actor: str


@router.post("/periods/close")
async def close_period(
    body: PeriodClose,
    conn: asyncpg.Connection = Depends(require_db),
):
    """Close a fiscal period."""
    tenant_id = await _get_default_tenant_id(conn)

    from app.semantic.period_engine import set_period_status
    from app.core.db_sync import get_write_connection

    def _close():
        with get_write_connection() as sync_conn:
            set_period_status(sync_conn, tenant_id, body.fiscal_year, body.fiscal_period, "closed", body.actor)

    await asyncio.to_thread(_close)

    return wrap_response({
        "fiscal_year": body.fiscal_year,
        "fiscal_period": body.fiscal_period,
        "status": "closed",
        "actor": body.actor,
    })

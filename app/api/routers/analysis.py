"""
Analysis endpoints — aging, variance, profitability, close support.

GET  /v1/analysis/aging/ar              — AR aging summary
GET  /v1/analysis/aging/ap              — AP aging summary
GET  /v1/analysis/aging/ar/by-customer  — AR aging by customer
GET  /v1/analysis/variance              — Budget vs actual variance
GET  /v1/analysis/profitability         — Profitability by dimension
GET  /v1/analysis/close-checklist       — Period close readiness
"""

from __future__ import annotations

import asyncio
import logging

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.api.models.responses import wrap_response
from app.core.deps import require_db
from app.core.errors import ValidationError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/analysis", tags=["analysis"])

_DEFAULT_TENANT = "default"


async def _get_default_tenant_id(conn: asyncpg.Connection) -> str:
    row = await conn.fetchrow("SELECT tenant_id FROM platform.tenants WHERE slug = $1", _DEFAULT_TENANT)
    if not row:
        raise ValidationError("Default tenant not found")
    return str(row["tenant_id"])


@router.get("/aging/ar")
async def ar_aging(conn: asyncpg.Connection = Depends(require_db)):
    """AR aging summary by bucket."""
    tenant_id = await _get_default_tenant_id(conn)
    from app.analysis.aging import get_ar_aging
    from app.core.db_sync import get_cursor

    def _run():
        with get_cursor() as cur:
            # Need connection not cursor — use write_connection for consistency
            pass
    from app.core.db_sync import get_write_connection

    def _compute():
        with get_write_connection() as sc:
            return get_ar_aging(sc, tenant_id)

    result = await asyncio.to_thread(_compute)
    return wrap_response(result)


@router.get("/aging/ap")
async def ap_aging(conn: asyncpg.Connection = Depends(require_db)):
    """AP aging summary by bucket."""
    tenant_id = await _get_default_tenant_id(conn)
    from app.analysis.aging import get_ap_aging
    from app.core.db_sync import get_write_connection

    def _compute():
        with get_write_connection() as sc:
            return get_ap_aging(sc, tenant_id)

    result = await asyncio.to_thread(_compute)
    return wrap_response(result)


@router.get("/aging/ar/by-customer")
async def ar_aging_by_customer(
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(require_db),
):
    """AR aging by customer — top customers by outstanding balance."""
    tenant_id = await _get_default_tenant_id(conn)
    from app.analysis.aging import get_ar_aging_by_customer
    from app.core.db_sync import get_write_connection

    def _compute():
        with get_write_connection() as sc:
            return get_ar_aging_by_customer(sc, tenant_id, limit)

    result = await asyncio.to_thread(_compute)
    return wrap_response(result)


@router.get("/variance")
async def variance_report(
    fiscal_year: int = Query(...),
    fiscal_period: int | None = Query(None),
    threshold_pct: float = Query(10.0),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Budget vs actual variance analysis."""
    tenant_id = await _get_default_tenant_id(conn)
    from app.analysis.variance import get_variance_report
    from app.core.db_sync import get_write_connection

    def _compute():
        with get_write_connection() as sc:
            return get_variance_report(sc, tenant_id, fiscal_year, fiscal_period, threshold_pct)

    result = await asyncio.to_thread(_compute)
    return wrap_response(result)


@router.get("/profitability")
async def profitability(
    fiscal_year: int = Query(...),
    dimension: str = Query("dimension_1", description="dimension_1 (dept), dimension_2 (location), dimension_3 (class)"),
    fiscal_period: int | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Profitability analysis by GL dimension."""
    if dimension not in ("dimension_1", "dimension_2", "dimension_3"):
        raise ValidationError(f"Invalid dimension: {dimension}. Use dimension_1, dimension_2, or dimension_3")

    tenant_id = await _get_default_tenant_id(conn)
    from app.analysis.profitability import get_profitability_by_dimension
    from app.core.db_sync import get_write_connection

    def _compute():
        with get_write_connection() as sc:
            return get_profitability_by_dimension(sc, tenant_id, fiscal_year, dimension, fiscal_period)

    result = await asyncio.to_thread(_compute)
    return wrap_response(result)


@router.get("/close-checklist")
async def close_checklist(
    fiscal_year: int = Query(...),
    fiscal_period: int = Query(...),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Period close readiness checklist."""
    tenant_id = await _get_default_tenant_id(conn)
    from app.analysis.close_support import get_close_checklist
    from app.core.db_sync import get_write_connection

    def _compute():
        with get_write_connection() as sc:
            return get_close_checklist(sc, tenant_id, fiscal_year, fiscal_period)

    result = await asyncio.to_thread(_compute)
    return wrap_response(result)

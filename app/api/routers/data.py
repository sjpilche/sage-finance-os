"""
Data query endpoints — browse canonical financial data.

GET /v1/data/gl          — GL journal entries
GET /v1/data/tb          — Trial balance
GET /v1/data/ap          — AP invoices
GET /v1/data/ar          — AR invoices
GET /v1/data/vendors     — Vendor master
GET /v1/data/customers   — Customer master
GET /v1/data/coa         — Chart of accounts
GET /v1/data/summary     — Row counts per table
"""

from __future__ import annotations

import logging
from datetime import date

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.api.models.responses import wrap_response
from app.core.deps import require_db

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/data", tags=["data"])


@router.get("/summary")
async def data_summary(conn: asyncpg.Connection = Depends(require_db)):
    """Row counts per contract table."""
    tables = [
        "contract.gl_entry", "contract.trial_balance",
        "contract.ap_invoice", "contract.ar_invoice",
        "contract.vendor", "contract.customer",
        "contract.chart_of_accounts", "contract.department",
        "contract.project", "contract.employee", "contract.budget_line",
    ]
    counts = {}
    for table in tables:
        try:
            row = await conn.fetchval(f"SELECT count(*) FROM {table}")
            counts[table.split(".")[1]] = row
        except Exception:
            counts[table.split(".")[1]] = 0

    return wrap_response(counts)


@router.get("/gl")
async def get_gl_entries(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    account: str | None = Query(None, description="Filter by account_number"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    dimension_1: str | None = Query(None, description="Filter by dimension_1 (department)"),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Query GL journal entries with optional filters."""
    conditions = []
    params = []
    idx = 1

    if account:
        conditions.append(f"account_number = ${idx}")
        params.append(account)
        idx += 1
    if date_from:
        conditions.append(f"posting_date >= ${idx}")
        params.append(date_from)
        idx += 1
    if date_to:
        conditions.append(f"posting_date <= ${idx}")
        params.append(date_to)
        idx += 1
    if dimension_1:
        conditions.append(f"dimension_1 = ${idx}")
        params.append(dimension_1)
        idx += 1

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Get total count
    count = await conn.fetchval(
        f"SELECT count(*) FROM contract.gl_entry {where}", *params
    )

    # Get rows
    rows = await conn.fetch(
        f"""
        SELECT gl_entry_id, posting_date, document_number, description,
               account_number, amount, debit_amount, credit_amount,
               currency_code, dimension_1, dimension_2, dimension_3,
               source_module, fiscal_year, fiscal_period, created_at
        FROM contract.gl_entry {where}
        ORDER BY posting_date DESC, created_at DESC
        LIMIT ${idx} OFFSET ${idx + 1}
        """,
        *params, limit, offset,
    )

    return wrap_response({
        "total": count,
        "limit": limit,
        "offset": offset,
        "rows": [dict(r) for r in rows],
    })


@router.get("/tb")
async def get_trial_balance(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Query trial balance."""
    count = await conn.fetchval("SELECT count(*) FROM contract.trial_balance")
    rows = await conn.fetch(
        """
        SELECT tb_id, as_of_date, account_number, account_name,
               beginning_balance, total_debits, total_credits, ending_balance,
               currency_code, created_at
        FROM contract.trial_balance
        ORDER BY account_number
        LIMIT $1 OFFSET $2
        """,
        limit, offset,
    )

    return wrap_response({
        "total": count,
        "limit": limit,
        "offset": offset,
        "rows": [dict(r) for r in rows],
    })


@router.get("/ap")
async def get_ap_invoices(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    vendor: str | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Query AP invoices."""
    conditions = []
    params = []
    idx = 1

    if status:
        conditions.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    if vendor:
        conditions.append(f"vendor_code = ${idx}")
        params.append(vendor)
        idx += 1

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    count = await conn.fetchval(
        f"SELECT count(*) FROM contract.ap_invoice {where}", *params
    )
    rows = await conn.fetch(
        f"""
        SELECT ap_invoice_id, vendor_code, invoice_number, invoice_date, due_date,
               total_amount, paid_amount, balance, currency_code, status, description, created_at
        FROM contract.ap_invoice {where}
        ORDER BY due_date DESC NULLS LAST
        LIMIT ${idx} OFFSET ${idx + 1}
        """,
        *params, limit, offset,
    )

    return wrap_response({
        "total": count,
        "limit": limit,
        "offset": offset,
        "rows": [dict(r) for r in rows],
    })


@router.get("/ar")
async def get_ar_invoices(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    customer: str | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Query AR invoices."""
    conditions = []
    params = []
    idx = 1

    if status:
        conditions.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    if customer:
        conditions.append(f"customer_code = ${idx}")
        params.append(customer)
        idx += 1

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    count = await conn.fetchval(
        f"SELECT count(*) FROM contract.ar_invoice {where}", *params
    )
    rows = await conn.fetch(
        f"""
        SELECT ar_invoice_id, customer_code, invoice_number, invoice_date, due_date,
               total_amount, paid_amount, balance, currency_code, status, description, created_at
        FROM contract.ar_invoice {where}
        ORDER BY due_date DESC NULLS LAST
        LIMIT ${idx} OFFSET ${idx + 1}
        """,
        *params, limit, offset,
    )

    return wrap_response({
        "total": count,
        "limit": limit,
        "offset": offset,
        "rows": [dict(r) for r in rows],
    })


@router.get("/vendors")
async def get_vendors(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Query vendor master."""
    count = await conn.fetchval("SELECT count(*) FROM contract.vendor")
    rows = await conn.fetch(
        """
        SELECT vendor_id, vendor_code, vendor_name, status, payment_terms,
               contact_email, created_at
        FROM contract.vendor
        ORDER BY vendor_name
        LIMIT $1 OFFSET $2
        """,
        limit, offset,
    )

    return wrap_response({
        "total": count,
        "limit": limit,
        "offset": offset,
        "rows": [dict(r) for r in rows],
    })


@router.get("/customers")
async def get_customers(
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Query customer master."""
    count = await conn.fetchval("SELECT count(*) FROM contract.customer")
    rows = await conn.fetch(
        """
        SELECT customer_id, customer_code, customer_name, status, payment_terms,
               contact_email, credit_limit, created_at
        FROM contract.customer
        ORDER BY customer_name
        LIMIT $1 OFFSET $2
        """,
        limit, offset,
    )

    return wrap_response({
        "total": count,
        "limit": limit,
        "offset": offset,
        "rows": [dict(r) for r in rows],
    })


@router.get("/coa")
async def get_chart_of_accounts(
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    account_type: str | None = Query(None),
    conn: asyncpg.Connection = Depends(require_db),
):
    """Query chart of accounts."""
    conditions = []
    params = []
    idx = 1

    if account_type:
        conditions.append(f"account_type = ${idx}")
        params.append(account_type)
        idx += 1

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    count = await conn.fetchval(
        f"SELECT count(*) FROM contract.chart_of_accounts {where}", *params
    )
    rows = await conn.fetch(
        f"""
        SELECT coa_id, account_number, account_name, account_type,
               normal_balance, is_active, parent_account, created_at
        FROM contract.chart_of_accounts {where}
        ORDER BY account_number
        LIMIT ${idx} OFFSET ${idx + 1}
        """,
        *params, limit, offset,
    )

    return wrap_response({
        "total": count,
        "limit": limit,
        "offset": offset,
        "rows": [dict(r) for r in rows],
    })

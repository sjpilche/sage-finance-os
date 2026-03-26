"""
contract.writer
===============
Batch writers for canonical contract tables. Each writer takes a list of
transformed records and bulk-inserts into the appropriate table.

Uses psycopg2.extras.execute_values for fast bulk inserts.
Idempotent: skips if run_id already has rows in the target table.

Adapted from DataClean's contract/writer.py — simplified, CRM removed.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from decimal import Decimal

from psycopg2.extras import execute_values

log = logging.getLogger(__name__)


# -- Helpers -------------------------------------------------------------------


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_date(value) -> date | None:
    """Parse a date-like value to a Python date."""
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return value if isinstance(value, date) else value.date()
    s = str(value).strip()
    # Try common formats
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19], fmt).date()
        except ValueError:
            continue
    return None


def _fiscal_year(posting_date) -> int | None:
    d = _to_date(posting_date)
    return d.year if d else None


def _to_json(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _check_idempotent(conn, table: str, run_id: str) -> bool:
    """Return True if this run_id already has rows in the table (skip re-insert)."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM {table} WHERE run_id = %s LIMIT 1", (run_id,))
        if cur.fetchone():
            log.info("writer: skipping %s — run_id %s already written", table, run_id)
            return True
    return False


# -- GL Entries ----------------------------------------------------------------


def write_gl_entries(conn, tenant_id: str, run_id: str, records: list[dict]) -> int:
    """Batch-insert GL entries into contract.gl_entry."""
    if not records or _check_idempotent(conn, "contract.gl_entry", run_id):
        return 0

    cols = (
        "tenant_id", "run_id", "posting_date", "document_number", "description",
        "account_number", "amount", "debit_amount", "credit_amount",
        "currency_code", "dimension_1", "dimension_2", "dimension_3",
        "source_module", "fiscal_year", "fiscal_period",
    )
    values = []
    for r in records:
        amount = _to_decimal(r.get("amount", 0))
        debit = _to_decimal(r.get("debit_amount", 0))
        credit = _to_decimal(r.get("credit_amount", 0))
        pd = _to_date(r.get("posting_date"))

        values.append((
            tenant_id, run_id, pd,
            r.get("document_number", ""), r.get("description", ""),
            r.get("account_number", ""), amount, debit, credit,
            r.get("currency_code", "USD"),
            r.get("dimension_1", ""), r.get("dimension_2", ""), r.get("dimension_3", ""),
            r.get("source_module", ""),
            _fiscal_year(pd), None,
        ))

    sql = f"INSERT INTO contract.gl_entry ({', '.join(cols)}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=1000)
    conn.commit()

    log.info("writer: gl_entry — %d rows inserted (run=%s)", len(values), run_id)
    return len(values)


# -- Trial Balance -------------------------------------------------------------


def write_trial_balance(conn, tenant_id: str, run_id: str, records: list[dict]) -> int:
    """Batch-insert trial balance rows into contract.trial_balance."""
    if not records or _check_idempotent(conn, "contract.trial_balance", run_id):
        return 0

    cols = (
        "tenant_id", "run_id", "account_number", "account_name",
        "beginning_balance", "total_debits", "total_credits", "ending_balance",
        "currency_code",
    )
    values = []
    for r in records:
        values.append((
            tenant_id, run_id,
            r.get("account_number", ""), r.get("account_name", ""),
            _to_decimal(r.get("beginning_balance", 0)),
            _to_decimal(r.get("total_debits", 0)),
            _to_decimal(r.get("total_credits", 0)),
            _to_decimal(r.get("ending_balance", 0)),
            r.get("currency_code", "USD"),
        ))

    sql = f"INSERT INTO contract.trial_balance ({', '.join(cols)}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=1000)
    conn.commit()

    log.info("writer: trial_balance — %d rows inserted (run=%s)", len(values), run_id)
    return len(values)


# -- AP Invoices ---------------------------------------------------------------


def write_ap_invoices(conn, tenant_id: str, run_id: str, records: list[dict]) -> int:
    if not records or _check_idempotent(conn, "contract.ap_invoice", run_id):
        return 0

    cols = (
        "tenant_id", "run_id", "vendor_code", "invoice_number",
        "invoice_date", "due_date", "total_amount", "paid_amount", "balance",
        "currency_code", "status", "description",
    )
    values = []
    for r in records:
        total = _to_decimal(r.get("total_amount", 0))
        paid = _to_decimal(r.get("paid_amount", 0))
        values.append((
            tenant_id, run_id,
            r.get("vendor_code", ""), r.get("invoice_number", ""),
            _to_date(r.get("invoice_date")), _to_date(r.get("due_date")),
            total, paid, total - paid,
            r.get("currency_code", "USD"),
            _map_status(r.get("status", "")),
            r.get("description", ""),
        ))

    sql = f"INSERT INTO contract.ap_invoice ({', '.join(cols)}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=1000)
    conn.commit()

    log.info("writer: ap_invoice — %d rows inserted (run=%s)", len(values), run_id)
    return len(values)


# -- AR Invoices ---------------------------------------------------------------


def write_ar_invoices(conn, tenant_id: str, run_id: str, records: list[dict]) -> int:
    if not records or _check_idempotent(conn, "contract.ar_invoice", run_id):
        return 0

    cols = (
        "tenant_id", "run_id", "customer_code", "invoice_number",
        "invoice_date", "due_date", "total_amount", "paid_amount", "balance",
        "currency_code", "status", "description",
    )
    values = []
    for r in records:
        total = _to_decimal(r.get("total_amount", 0))
        paid = _to_decimal(r.get("paid_amount", r.get("amount_collected", 0)))
        values.append((
            tenant_id, run_id,
            r.get("customer_code", ""), r.get("invoice_number", ""),
            _to_date(r.get("invoice_date")), _to_date(r.get("due_date")),
            total, paid, total - paid,
            r.get("currency_code", "USD"),
            _map_status(r.get("status", "")),
            r.get("description", ""),
        ))

    sql = f"INSERT INTO contract.ar_invoice ({', '.join(cols)}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=1000)
    conn.commit()

    log.info("writer: ar_invoice — %d rows inserted (run=%s)", len(values), run_id)
    return len(values)


# -- Vendors -------------------------------------------------------------------


def write_vendors(conn, tenant_id: str, run_id: str, records: list[dict]) -> int:
    if not records:
        return 0

    cols = (
        "tenant_id", "run_id", "vendor_code", "vendor_name",
        "status", "payment_terms", "contact_email", "address",
    )
    values = []
    for r in records:
        values.append((
            tenant_id, run_id,
            r.get("vendor_code", ""), r.get("vendor_name", ""),
            r.get("status", "active"), r.get("payment_terms", ""),
            r.get("contact_email", ""), _to_json(r.get("address")),
        ))

    # Upsert: update on conflict with vendor_code
    sql = f"""
    INSERT INTO contract.vendor ({', '.join(cols)})
    VALUES %s
    ON CONFLICT (tenant_id, vendor_code)
    DO UPDATE SET
        vendor_name = EXCLUDED.vendor_name,
        status = EXCLUDED.status,
        payment_terms = EXCLUDED.payment_terms,
        contact_email = EXCLUDED.contact_email,
        address = EXCLUDED.address,
        run_id = EXCLUDED.run_id,
        updated_at = now()
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=1000)
    conn.commit()

    log.info("writer: vendor — %d rows upserted (run=%s)", len(values), run_id)
    return len(values)


# -- Customers -----------------------------------------------------------------


def write_customers(conn, tenant_id: str, run_id: str, records: list[dict]) -> int:
    if not records:
        return 0

    cols = (
        "tenant_id", "run_id", "customer_code", "customer_name",
        "status", "payment_terms", "contact_email", "credit_limit", "address",
    )
    values = []
    for r in records:
        cl = r.get("credit_limit")
        values.append((
            tenant_id, run_id,
            r.get("customer_code", ""), r.get("customer_name", ""),
            r.get("status", "active"), r.get("payment_terms", ""),
            r.get("contact_email", ""),
            _to_decimal(cl) if cl is not None else None,
            _to_json(r.get("address")),
        ))

    sql = f"""
    INSERT INTO contract.customer ({', '.join(cols)})
    VALUES %s
    ON CONFLICT (tenant_id, customer_code)
    DO UPDATE SET
        customer_name = EXCLUDED.customer_name,
        status = EXCLUDED.status,
        payment_terms = EXCLUDED.payment_terms,
        contact_email = EXCLUDED.contact_email,
        credit_limit = EXCLUDED.credit_limit,
        address = EXCLUDED.address,
        run_id = EXCLUDED.run_id,
        updated_at = now()
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=1000)
    conn.commit()

    log.info("writer: customer — %d rows upserted (run=%s)", len(values), run_id)
    return len(values)


# -- Chart of Accounts ---------------------------------------------------------


def write_chart_of_accounts(conn, tenant_id: str, run_id: str, records: list[dict]) -> int:
    if not records:
        return 0

    cols = (
        "tenant_id", "run_id", "account_number", "account_name",
        "account_type", "normal_balance", "is_active", "parent_account",
    )
    values = []
    for r in records:
        acct_type = _map_account_type(r.get("account_type", "Other"))
        values.append((
            tenant_id, run_id,
            r.get("account_number", ""), r.get("account_name", ""),
            acct_type,
            r.get("normal_balance", "debit"),
            r.get("is_active", True),
            r.get("parent_account", ""),
        ))

    sql = f"""
    INSERT INTO contract.chart_of_accounts ({', '.join(cols)})
    VALUES %s
    ON CONFLICT (tenant_id, entity_id, account_number)
    DO UPDATE SET
        account_name = EXCLUDED.account_name,
        account_type = EXCLUDED.account_type,
        normal_balance = EXCLUDED.normal_balance,
        is_active = EXCLUDED.is_active,
        parent_account = EXCLUDED.parent_account,
        run_id = EXCLUDED.run_id,
        updated_at = now()
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=1000)
    conn.commit()

    log.info("writer: chart_of_accounts — %d rows upserted (run=%s)", len(values), run_id)
    return len(values)


# -- Dispatch Table ------------------------------------------------------------


OBJECT_WRITERS = {
    "gl_entry": write_gl_entries,
    "chart_of_accounts": write_chart_of_accounts,
    "trial_balance": write_trial_balance,
    "ap_invoice": write_ap_invoices,
    "ar_invoice": write_ar_invoices,
    "vendor": write_vendors,
    "customer": write_customers,
}


def write_all(conn, tenant_id: str, run_id: str, data: dict[str, list[dict]]) -> dict[str, int]:
    """
    Write all objects to contract tables.

    Parameters
    ----------
    data: dict mapping canonical object name to list of record dicts.
          e.g. {"gl_entry": [...], "vendor": [...]}

    Returns
    -------
    dict of {object_name: rows_written}
    """
    counts = {}
    for object_name, records in data.items():
        writer = OBJECT_WRITERS.get(object_name)
        if writer is None:
            log.warning("writer: no writer for object %s — skipping %d records", object_name, len(records))
            continue
        counts[object_name] = writer(conn, tenant_id, run_id, records)
    return counts


# -- Helpers -------------------------------------------------------------------


def _map_status(raw: str) -> str:
    """Normalize Intacct status values to contract CHECK constraint values."""
    s = raw.strip().lower()
    if s in ("paid", "closed"):
        return "paid"
    if s in ("partial", "partiallypaid"):
        return "partial"
    if s in ("void", "voided", "reversed"):
        return "void"
    return "open"


def _map_account_type(raw: str) -> str:
    """Normalize account type to CHECK constraint values."""
    s = raw.strip()
    valid = {"Asset", "Liability", "Equity", "Revenue", "Expense", "Other"}
    # Intacct uses lowercase sometimes
    for v in valid:
        if s.lower() == v.lower():
            return v
    # Intacct-specific mappings
    mapping = {
        "incomestatement": "Revenue",
        "balancesheet": "Asset",
        "income statement": "Revenue",
        "balance sheet": "Asset",
    }
    return mapping.get(s.lower(), "Other")

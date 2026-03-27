#!/usr/bin/env python3
"""
Seed demo data for Sage Finance OS.

Populates all tables with realistic sample financial data so every UI page
renders with charts, tables, KPIs, and meaningful analytics.

Usage:
    python scripts/seed_demo_data.py

Requires: DATABASE_URL_SYNC env var or local PostgreSQL at localhost:5432.
"""

from __future__ import annotations

import json
import os
import random
import uuid
from datetime import date, datetime, timedelta, timezone

import psycopg2

# ── Config ──────────────────────────────────────────────────────────────
DSN = os.getenv("DATABASE_URL_SYNC", "postgresql://sage:sage@localhost:5432/sage_finance")
TENANT_SLUG = "default"
TENANT_NAME = "Acme Corp"
ENTITY_CODE = "ACME-US"
ENTITY_NAME = "Acme Corporation — US Operations"
FISCAL_YEAR = 2026
SEED_RUN_ID = str(uuid.uuid4())

random.seed(42)  # Reproducible demo data


# ── Helpers ─────────────────────────────────────────────────────────────
def uid() -> str:
    return str(uuid.uuid4())


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))


def rand_amount(lo: float, hi: float) -> float:
    return round(random.uniform(lo, hi), 2)


# ── Chart of Accounts ───────────────────────────────────────────────────
ACCOUNTS = [
    # Assets
    ("1000", "Cash and Equivalents", "Asset", "debit"),
    ("1100", "Accounts Receivable", "Asset", "debit"),
    ("1200", "Inventory", "Asset", "debit"),
    ("1300", "Prepaid Expenses", "Asset", "debit"),
    ("1500", "Fixed Assets — Equipment", "Asset", "debit"),
    ("1510", "Fixed Assets — Furniture", "Asset", "debit"),
    ("1600", "Accumulated Depreciation", "Asset", "credit"),
    # Liabilities
    ("2000", "Accounts Payable", "Liability", "credit"),
    ("2100", "Accrued Expenses", "Liability", "credit"),
    ("2200", "Short-Term Debt", "Liability", "credit"),
    ("2300", "Deferred Revenue", "Liability", "credit"),
    ("2500", "Long-Term Debt", "Liability", "credit"),
    # Equity
    ("3000", "Common Stock", "Equity", "credit"),
    ("3100", "Retained Earnings", "Equity", "credit"),
    ("3200", "Additional Paid-In Capital", "Equity", "credit"),
    # Revenue
    ("4000", "Product Revenue", "Revenue", "credit"),
    ("4100", "Service Revenue", "Revenue", "credit"),
    ("4200", "Subscription Revenue", "Revenue", "credit"),
    ("4300", "Consulting Revenue", "Revenue", "credit"),
    ("4900", "Other Revenue", "Revenue", "credit"),
    # Expenses
    ("5000", "Cost of Goods Sold", "Expense", "debit"),
    ("5100", "Direct Labor", "Expense", "debit"),
    ("6000", "Salaries & Wages", "Expense", "debit"),
    ("6100", "Employee Benefits", "Expense", "debit"),
    ("6200", "Payroll Taxes", "Expense", "debit"),
    ("6300", "Rent & Occupancy", "Expense", "debit"),
    ("6400", "Utilities", "Expense", "debit"),
    ("6500", "Office Supplies", "Expense", "debit"),
    ("6600", "Marketing & Advertising", "Expense", "debit"),
    ("6700", "Travel & Entertainment", "Expense", "debit"),
    ("6800", "Professional Services", "Expense", "debit"),
    ("6900", "Depreciation Expense", "Expense", "debit"),
    ("7000", "Insurance", "Expense", "debit"),
    ("7100", "Software & Technology", "Expense", "debit"),
    ("7200", "Interest Expense", "Expense", "debit"),
    ("7900", "Miscellaneous Expense", "Expense", "debit"),
]

DEPARTMENTS = [
    ("SALES", "Sales", "VP of Sales"),
    ("ENG", "Engineering", "VP of Engineering"),
    ("MKT", "Marketing", "VP of Marketing"),
    ("FIN", "Finance & Accounting", "CFO"),
    ("OPS", "Operations", "COO"),
    ("HR", "Human Resources", "VP of People"),
]

VENDORS = [
    ("V001", "Amazon Web Services", "aws-billing@amazon.com", "Net 30"),
    ("V002", "WeWork Offices LLC", "billing@wework.com", "Net 30"),
    ("V003", "Salesforce Inc", "invoices@salesforce.com", "Net 45"),
    ("V004", "Delta Air Lines", "corporate@delta.com", "Due on Receipt"),
    ("V005", "Staples Office Supply", "ap@staples.com", "Net 15"),
    ("V006", "Blue Cross Blue Shield", "premiums@bcbs.com", "Net 30"),
    ("V007", "Deloitte Consulting", "billing@deloitte.com", "Net 60"),
    ("V008", "Google Cloud Platform", "billing@google.com", "Net 30"),
    ("V009", "FedEx Shipping", "invoicing@fedex.com", "Net 15"),
    ("V010", "Comcast Business", "billing@comcast.com", "Net 30"),
]

CUSTOMERS = [
    ("C001", "TechVentures Inc", "ap@techventures.com", "Net 30", 500000),
    ("C002", "GlobalTrade Partners", "billing@globaltrade.com", "Net 45", 750000),
    ("C003", "Summit Healthcare Group", "finance@summithcg.com", "Net 30", 300000),
    ("C004", "Pinnacle Manufacturing", "ap@pinnaclemfg.com", "Net 60", 1000000),
    ("C005", "Riverside Financial", "invoices@riversidefa.com", "Net 30", 250000),
    ("C006", "Atlas Logistics Corp", "payables@atlaslogistics.com", "Net 45", 400000),
    ("C007", "Meridian Software", "ap@meridiansw.com", "Net 30", 350000),
    ("C008", "Coastal Properties LLC", "accounting@coastalprop.com", "Net 30", 200000),
    ("C009", "NorthStar Energy", "finance@northstarenergy.com", "Net 60", 600000),
    ("C010", "Pacific Retail Group", "ap@pacificretail.com", "Net 30", 450000),
    ("C011", "Evergreen Consulting", "billing@evergreenconsult.com", "Net 30", 150000),
    ("C012", "Diamond Pharmaceuticals", "payables@diamondpharma.com", "Net 45", 800000),
]


def seed(conn):
    """Main seed function — populates all tables."""
    cur = conn.cursor()

    print("Seeding demo data for Sage Finance OS...")

    # ── 1. Tenant ──────────────────────────────────────────────
    tenant_id = uid()
    cur.execute(
        "INSERT INTO platform.tenants (tenant_id, slug, name) VALUES (%s, %s, %s) ON CONFLICT (slug) DO UPDATE SET name = %s RETURNING tenant_id",
        (tenant_id, TENANT_SLUG, TENANT_NAME, TENANT_NAME),
    )
    tenant_id = str(cur.fetchone()[0])
    print(f"  Tenant: {TENANT_NAME} ({tenant_id[:8]})")

    # ── 2. Entity ──────────────────────────────────────────────
    entity_id = uid()
    cur.execute(
        "INSERT INTO contract.entity (entity_id, tenant_id, entity_code, entity_name) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (entity_id, tenant_id, ENTITY_CODE, ENTITY_NAME),
    )
    print(f"  Entity: {ENTITY_NAME}")

    # ── 3. Connection (demo, not real) ─────────────────────────
    conn_id = uid()
    cur.execute(
        "INSERT INTO platform.connections (connection_id, tenant_id, name, status, credentials) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (conn_id, tenant_id, "Sage Intacct — Demo", "active", json.dumps({"demo": True})),
    )
    print(f"  Connection: Sage Intacct — Demo")

    # ── 4. Data Run (completed) ────────────────────────────────
    run_id = SEED_RUN_ID
    run_started = datetime.now(timezone.utc) - timedelta(hours=2)
    run_completed = datetime.now(timezone.utc) - timedelta(hours=1, minutes=45)
    cur.execute(
        "INSERT INTO platform.data_runs (run_id, tenant_id, connection_id, mode, status, started_at, completed_at, summary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (run_id, tenant_id, conn_id, "full", "complete", run_started, run_completed,
         json.dumps({"objects": 7, "elapsed_seconds": 94.2, "mode": "full"})),
    )

    # Add a couple more historical runs
    for i, (status, hrs_ago) in enumerate([(  "complete", 26), ("complete", 50), ("failed", 74)]):
        rid = uid()
        sa = datetime.now(timezone.utc) - timedelta(hours=hrs_ago)
        ca = sa + timedelta(minutes=random.randint(1, 5)) if status != "failed" else sa + timedelta(seconds=30)
        err = "Connection timeout after 30s — Sage Intacct API unreachable" if status == "failed" else None
        cur.execute(
            "INSERT INTO platform.data_runs (run_id, tenant_id, connection_id, mode, status, started_at, completed_at, error_message) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (rid, tenant_id, conn_id, "incremental" if i > 0 else "full", status, sa, ca, err),
        )
    print(f"  Data runs: 4 (3 complete, 1 failed)")

    # ── 5. Chart of Accounts ───────────────────────────────────
    for acct_num, acct_name, acct_type, normal_bal in ACCOUNTS:
        cur.execute(
            "INSERT INTO contract.chart_of_accounts (tenant_id, run_id, entity_id, account_number, account_name, account_type, normal_balance) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (tenant_id, run_id, entity_id, acct_num, acct_name, acct_type, normal_bal),
        )
    print(f"  Chart of Accounts: {len(ACCOUNTS)} accounts")

    # ── 6. Departments ─────────────────────────────────────────
    for dept_code, dept_name, manager in DEPARTMENTS:
        cur.execute(
            "INSERT INTO contract.department (tenant_id, run_id, entity_id, dept_code, dept_name, manager_name) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (tenant_id, run_id, entity_id, dept_code, dept_name, manager),
        )
    print(f"  Departments: {len(DEPARTMENTS)}")

    # ── 7. Vendors ─────────────────────────────────────────────
    for vcode, vname, vemail, vterms in VENDORS:
        cur.execute(
            "INSERT INTO contract.vendor (tenant_id, run_id, entity_id, vendor_code, vendor_name, contact_email, payment_terms) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (tenant_id, run_id, entity_id, vcode, vname, vemail, vterms),
        )
    print(f"  Vendors: {len(VENDORS)}")

    # ── 8. Customers ───────────────────────────────────────────
    for ccode, cname, cemail, cterms, climit in CUSTOMERS:
        cur.execute(
            "INSERT INTO contract.customer (tenant_id, run_id, entity_id, customer_code, customer_name, contact_email, payment_terms, credit_limit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (tenant_id, run_id, entity_id, ccode, cname, cemail, cterms, climit),
        )
    print(f"  Customers: {len(CUSTOMERS)}")

    # ── 9. GL Entries (12 months of journal entries) ────────────
    gl_count = 0
    revenue_accounts = ["4000", "4100", "4200", "4300"]
    expense_accounts = ["5000", "5100", "6000", "6100", "6200", "6300", "6400", "6500", "6600", "6700", "6800", "6900", "7000", "7100", "7200"]
    dept_codes = [d[0] for d in DEPARTMENTS]

    for month in range(1, 13):
        period_start = date(FISCAL_YEAR, month, 1)
        period_end = date(FISCAL_YEAR, month, 28)

        # Revenue entries (8-15 per month)
        for _ in range(random.randint(8, 15)):
            acct = random.choice(revenue_accounts)
            amt = rand_amount(5000, 85000)
            dept = random.choice(dept_codes)
            d = rand_date(period_start, period_end)
            cust = random.choice(CUSTOMERS)
            cur.execute(
                """INSERT INTO contract.gl_entry
                    (tenant_id, run_id, entity_id, posting_date, document_number, description,
                     account_number, amount, debit_amount, credit_amount, dimension_1,
                     source_module, fiscal_year, fiscal_period)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tenant_id, run_id, entity_id, d, f"INV-{FISCAL_YEAR}{month:02d}-{gl_count:04d}",
                 f"Revenue — {cust[1]}", acct, amt, 0, amt, dept, "AR", FISCAL_YEAR, month),
            )
            # Debit to AR
            cur.execute(
                """INSERT INTO contract.gl_entry
                    (tenant_id, run_id, entity_id, posting_date, document_number, description,
                     account_number, amount, debit_amount, credit_amount, dimension_1,
                     source_module, fiscal_year, fiscal_period)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tenant_id, run_id, entity_id, d, f"INV-{FISCAL_YEAR}{month:02d}-{gl_count:04d}",
                 f"AR — {cust[1]}", "1100", amt, amt, 0, dept, "AR", FISCAL_YEAR, month),
            )
            gl_count += 2

        # Expense entries (15-25 per month)
        for _ in range(random.randint(15, 25)):
            acct = random.choice(expense_accounts)
            amt = rand_amount(500, 45000)
            dept = random.choice(dept_codes)
            d = rand_date(period_start, period_end)
            vendor = random.choice(VENDORS)
            cur.execute(
                """INSERT INTO contract.gl_entry
                    (tenant_id, run_id, entity_id, posting_date, document_number, description,
                     account_number, amount, debit_amount, credit_amount, dimension_1,
                     source_module, fiscal_year, fiscal_period)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tenant_id, run_id, entity_id, d, f"BILL-{FISCAL_YEAR}{month:02d}-{gl_count:04d}",
                 f"Expense — {vendor[1]}", acct, amt, amt, 0, dept, "AP", FISCAL_YEAR, month),
            )
            # Credit to AP
            cur.execute(
                """INSERT INTO contract.gl_entry
                    (tenant_id, run_id, entity_id, posting_date, document_number, description,
                     account_number, amount, debit_amount, credit_amount, dimension_1,
                     source_module, fiscal_year, fiscal_period)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tenant_id, run_id, entity_id, d, f"BILL-{FISCAL_YEAR}{month:02d}-{gl_count:04d}",
                 f"AP — {vendor[1]}", "2000", amt, 0, amt, dept, "AP", FISCAL_YEAR, month),
            )
            gl_count += 2

    print(f"  GL Entries: {gl_count}")

    # ── 10. Trial Balance ──────────────────────────────────────
    tb_count = 0
    as_of = date(FISCAL_YEAR, 3, 31)
    for acct_num, acct_name, acct_type, normal_bal in ACCOUNTS:
        beg = rand_amount(10000, 500000)
        debits = rand_amount(5000, 200000)
        credits = rand_amount(5000, 200000)
        ending = beg + debits - credits
        cur.execute(
            """INSERT INTO contract.trial_balance
                (tenant_id, run_id, entity_id, as_of_date, account_number, account_name,
                 beginning_balance, total_debits, total_credits, ending_balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (tenant_id, run_id, entity_id, as_of, acct_num, acct_name, beg, debits, credits, ending),
        )
        tb_count += 1
    print(f"  Trial Balance: {tb_count} rows")

    # ── 11. AR Invoices ────────────────────────────────────────
    ar_count = 0
    for ccode, cname, _, _, _ in CUSTOMERS:
        for _ in range(random.randint(3, 8)):
            inv_date = rand_date(date(FISCAL_YEAR, 1, 1), date(FISCAL_YEAR, 3, 20))
            due_date = inv_date + timedelta(days=random.choice([30, 45, 60]))
            total = rand_amount(5000, 95000)
            days_out = (date(FISCAL_YEAR, 3, 27) - due_date).days
            # Older invoices more likely paid
            if days_out > 60:
                status = random.choice(["paid", "paid", "paid", "open"])
            elif days_out > 30:
                status = random.choice(["paid", "partial", "open"])
            else:
                status = random.choice(["open", "open", "partial"])

            paid = total if status == "paid" else (rand_amount(total * 0.3, total * 0.7) if status == "partial" else 0)
            balance = round(total - paid, 2)

            cur.execute(
                """INSERT INTO contract.ar_invoice
                    (tenant_id, run_id, entity_id, customer_code, invoice_number, invoice_date,
                     due_date, total_amount, paid_amount, balance, status, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tenant_id, run_id, entity_id, ccode, f"AR-{ar_count+1:04d}",
                 inv_date, due_date, total, paid, balance, status,
                 f"Invoice to {cname}"),
            )
            ar_count += 1
    print(f"  AR Invoices: {ar_count}")

    # ── 12. AP Invoices ────────────────────────────────────────
    ap_count = 0
    for vcode, vname, _, _ in VENDORS:
        for _ in range(random.randint(4, 10)):
            inv_date = rand_date(date(FISCAL_YEAR, 1, 1), date(FISCAL_YEAR, 3, 20))
            due_date = inv_date + timedelta(days=random.choice([15, 30, 45, 60]))
            total = rand_amount(1000, 65000)
            days_out = (date(FISCAL_YEAR, 3, 27) - due_date).days
            if days_out > 45:
                status = random.choice(["paid", "paid", "paid", "open"])
            elif days_out > 15:
                status = random.choice(["paid", "partial", "open"])
            else:
                status = random.choice(["open", "open", "partial"])

            paid = total if status == "paid" else (rand_amount(total * 0.2, total * 0.6) if status == "partial" else 0)
            balance = round(total - paid, 2)

            cur.execute(
                """INSERT INTO contract.ap_invoice
                    (tenant_id, run_id, entity_id, vendor_code, invoice_number, invoice_date,
                     due_date, total_amount, paid_amount, balance, status, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (tenant_id, run_id, entity_id, vcode, f"AP-{ap_count+1:04d}",
                 inv_date, due_date, total, paid, balance, status,
                 f"Bill from {vname}"),
            )
            ap_count += 1
    print(f"  AP Invoices: {ap_count}")

    # ── 13. Budget Lines ───────────────────────────────────────
    budget_count = 0
    budget_accounts = revenue_accounts + expense_accounts
    for acct in budget_accounts:
        for month in range(1, 13):
            # Revenue budgets higher than expense budgets
            if acct.startswith("4"):
                amt = rand_amount(30000, 120000)
            else:
                amt = rand_amount(5000, 50000)
            cur.execute(
                """INSERT INTO contract.budget_line
                    (tenant_id, run_id, entity_id, account_number, fiscal_year, fiscal_period, budget_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                (tenant_id, run_id, entity_id, acct, FISCAL_YEAR, month, amt),
            )
            budget_count += 1
    print(f"  Budget Lines: {budget_count}")

    # ── 14. Quality Scorecard ──────────────────────────────────
    cur.execute(
        """INSERT INTO audit.scorecard_results
            (run_id, tenant_id, accuracy, completeness, consistency, validity, uniqueness, timeliness, composite, gate_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (run_id, tenant_id, 100.0, 97.5, 98.0, 99.2, 100.0, 95.8, 98.7, "certified"),
    )
    print(f"  Quality Scorecard: 1 (certified, composite=98.7)")

    # ── 15. Period Status ──────────────────────────────────────
    for month in range(1, 13):
        status = "closed" if month <= 2 else "open"
        closed_by = "admin@acme.com" if status == "closed" else None
        closed_at = datetime(FISCAL_YEAR, month + 1, 5, tzinfo=timezone.utc) if status == "closed" else None
        cur.execute(
            """INSERT INTO semantic.period_status
                (tenant_id, entity_id, fiscal_year, fiscal_period, status, closed_by, closed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (tenant_id, entity_id, FISCAL_YEAR, month, status, closed_by, closed_at),
        )
    print(f"  Period Status: 12 months (P1-P2 closed, P3-P12 open)")

    # ── 16. Watermarks ─────────────────────────────────────────
    for obj_name in ["GLACCOUNT", "GLDETAIL", "APBILL", "ARINVOICE", "CUSTOMER", "VENDOR"]:
        cur.execute(
            """INSERT INTO platform.watermarks (tenant_id, connection_id, object_name, last_value, last_sync_at)
            VALUES (%s, %s, %s, %s, now()) ON CONFLICT DO NOTHING""",
            (tenant_id, conn_id, obj_name, datetime.now(timezone.utc).isoformat()),
        )
    print(f"  Watermarks: 6 objects")

    conn.commit()
    print(f"\nDone! Seeded {gl_count} GL entries, {ar_count} AR invoices, {ap_count} AP invoices,")
    print(f"       {len(ACCOUNTS)} accounts, {len(VENDORS)} vendors, {len(CUSTOMERS)} customers,")
    print(f"       {budget_count} budget lines, {tb_count} trial balance rows.")
    print(f"       Tenant: {tenant_id}")
    print(f"       Run:    {run_id}")


if __name__ == "__main__":
    print(f"Connecting to: {DSN.split('@')[1] if '@' in DSN else DSN}")
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    try:
        seed(conn)
    finally:
        conn.close()

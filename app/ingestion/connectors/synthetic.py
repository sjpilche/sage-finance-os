"""
Synthetic Sage Intacct connector — generates realistic financial data
for end-to-end pipeline testing without a real Sage Intacct instance.

Produces data in Sage Intacct XML format so the real transforms,
contract writers, quality gate, and KPI engine all execute.
"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Generator

from app.ingestion.connectors.base import BaseConnector
from app.ingestion.connectors.sage_intacct.objects import OBJECT_CATALOG
from app.ingestion.connectors.sage_intacct.transform import SAGE_TRANSFORMERS

log = logging.getLogger(__name__)

random.seed()  # Non-deterministic for realistic variation

# ── Reference Data ─────────────────────────────────────────────────────

ACCOUNTS = [
    ("1000", "Cash and Equivalents", "balancesheet", "debit"),
    ("1100", "Accounts Receivable", "balancesheet", "debit"),
    ("1200", "Inventory", "balancesheet", "debit"),
    ("1300", "Prepaid Expenses", "balancesheet", "debit"),
    ("1500", "Equipment", "balancesheet", "debit"),
    ("1600", "Accumulated Depreciation", "balancesheet", "credit"),
    ("2000", "Accounts Payable", "balancesheet", "credit"),
    ("2100", "Accrued Expenses", "balancesheet", "credit"),
    ("2200", "Short-Term Debt", "balancesheet", "credit"),
    ("2500", "Long-Term Debt", "balancesheet", "credit"),
    ("3000", "Common Stock", "balancesheet", "credit"),
    ("3100", "Retained Earnings", "balancesheet", "credit"),
    ("4000", "Product Revenue", "incomestatement", "credit"),
    ("4100", "Service Revenue", "incomestatement", "credit"),
    ("4200", "Subscription Revenue", "incomestatement", "credit"),
    ("4300", "Consulting Revenue", "incomestatement", "credit"),
    ("5000", "Cost of Goods Sold", "incomestatement", "debit"),
    ("5100", "Direct Labor", "incomestatement", "debit"),
    ("6000", "Salaries & Wages", "incomestatement", "debit"),
    ("6100", "Employee Benefits", "incomestatement", "debit"),
    ("6200", "Payroll Taxes", "incomestatement", "debit"),
    ("6300", "Rent & Occupancy", "incomestatement", "debit"),
    ("6400", "Utilities", "incomestatement", "debit"),
    ("6500", "Office Supplies", "incomestatement", "debit"),
    ("6600", "Marketing & Advertising", "incomestatement", "debit"),
    ("6700", "Travel & Entertainment", "incomestatement", "debit"),
    ("6800", "Professional Services", "incomestatement", "debit"),
    ("6900", "Depreciation Expense", "incomestatement", "debit"),
    ("7000", "Insurance", "incomestatement", "debit"),
    ("7100", "Software & Technology", "incomestatement", "debit"),
]

DEPARTMENTS = ["SALES", "ENG", "MKT", "FIN", "OPS", "HR"]
LOCATIONS = ["HQ", "WEST", "EAST", "REMOTE"]

VENDORS = [
    ("V001", "Amazon Web Services"),
    ("V002", "WeWork Offices LLC"),
    ("V003", "Salesforce Inc"),
    ("V004", "Delta Air Lines"),
    ("V005", "Staples Office Supply"),
    ("V006", "Blue Cross Blue Shield"),
    ("V007", "Deloitte Consulting"),
    ("V008", "Google Cloud Platform"),
    ("V009", "FedEx Shipping"),
    ("V010", "Comcast Business"),
]

CUSTOMERS = [
    ("C001", "TechVentures Inc"),
    ("C002", "GlobalTrade Partners"),
    ("C003", "Summit Healthcare Group"),
    ("C004", "Pinnacle Manufacturing"),
    ("C005", "Riverside Financial"),
    ("C006", "Atlas Logistics Corp"),
    ("C007", "Meridian Software"),
    ("C008", "Coastal Properties LLC"),
    ("C009", "NorthStar Energy"),
    ("C010", "Pacific Retail Group"),
    ("C011", "Evergreen Consulting"),
    ("C012", "Diamond Pharmaceuticals"),
]

FISCAL_YEAR = 2026


def _rand_amount(lo: float, hi: float) -> str:
    return str(round(random.uniform(lo, hi), 2))


def _rand_date(start: date, end: date) -> str:
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, max(delta, 1)))
    return d.strftime("%m/%d/%Y")


def _iso_date(start: date, end: date) -> str:
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, max(delta, 1)))
    return d.isoformat()


# ── Generators per Object ──────────────────────────────────────────────


def _generate_gl_detail(count: int = 500) -> list[dict]:
    """Generate BALANCED GL journal entries in Sage Intacct GLDETAIL format.

    Every journal entry has matching debit and credit lines so the
    quality gate's debit/credit balance check passes.
    """
    records = []
    revenue_accounts = [a for a in ACCOUNTS if a[0].startswith("4")]
    expense_accounts = [a for a in ACCOUNTS if a[0].startswith(("5", "6", "7"))]
    rec_id = 10000

    # Generate ~count/2 balanced journal entries (each produces 2 lines)
    for i in range(count // 2):
        month = random.randint(1, 3)  # Q1 data
        period_start = date(FISCAL_YEAR, month, 1)
        period_end = date(FISCAL_YEAR, month, 28)
        posting_date = _rand_date(period_start, period_end)
        dept = random.choice(DEPARTMENTS)
        loc = random.choice(LOCATIONS)
        doc_num = f"JE-{FISCAL_YEAR}-{i:05d}"

        if i % 3 == 0:
            # Revenue entry: Credit revenue, Debit AR
            acct = random.choice(revenue_accounts)
            amt = round(random.uniform(5000, 85000), 2)
            # Credit line (revenue) — negative amount in Sage = credit
            records.append({
                "RECORDNO": str(rec_id), "AMOUNT": str(-amt),
                "BATCH_DATE": posting_date, "DOCNUMBER": doc_num,
                "DESCRIPTION": f"Revenue — {acct[1]}",
                "ACCOUNTNO": acct[0], "ACCOUNTTITLE": acct[1],
                "CURRENCY": "USD", "DEPARTMENTID": dept,
                "LOCATIONID": loc, "CLASSID": "", "BOOKID": "GL",
                "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
            })
            rec_id += 1
            # Debit line (AR) — positive amount = debit
            records.append({
                "RECORDNO": str(rec_id), "AMOUNT": str(amt),
                "BATCH_DATE": posting_date, "DOCNUMBER": doc_num,
                "DESCRIPTION": f"AR — {acct[1]}",
                "ACCOUNTNO": "1100", "ACCOUNTTITLE": "Accounts Receivable",
                "CURRENCY": "USD", "DEPARTMENTID": dept,
                "LOCATIONID": loc, "CLASSID": "", "BOOKID": "GL",
                "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
            })
            rec_id += 1
        else:
            # Expense entry: Debit expense, Credit AP
            acct = random.choice(expense_accounts)
            amt = round(random.uniform(500, 45000), 2)
            # Debit line (expense) — positive amount = debit
            records.append({
                "RECORDNO": str(rec_id), "AMOUNT": str(amt),
                "BATCH_DATE": posting_date, "DOCNUMBER": doc_num,
                "DESCRIPTION": f"Expense — {acct[1]}",
                "ACCOUNTNO": acct[0], "ACCOUNTTITLE": acct[1],
                "CURRENCY": "USD", "DEPARTMENTID": dept,
                "LOCATIONID": loc, "CLASSID": "", "BOOKID": "GL",
                "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
            })
            rec_id += 1
            # Credit line (AP) — negative amount = credit
            records.append({
                "RECORDNO": str(rec_id), "AMOUNT": str(-amt),
                "BATCH_DATE": posting_date, "DOCNUMBER": doc_num,
                "DESCRIPTION": f"AP — {acct[1]}",
                "ACCOUNTNO": "2000", "ACCOUNTTITLE": "Accounts Payable",
                "CURRENCY": "USD", "DEPARTMENTID": dept,
                "LOCATIONID": loc, "CLASSID": "", "BOOKID": "GL",
                "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
            })
            rec_id += 1

    return records


def _generate_accounts() -> list[dict]:
    """Generate Chart of Accounts in Sage Intacct GLACCOUNT format."""
    return [
        {
            "RECORDNO": str(i + 1),
            "ACCOUNTNO": acct[0],
            "TITLE": acct[1],
            "ACCOUNTTYPE": acct[2],
            "NORMALBALANCE": acct[3],
            "STATUS": "active",
            "PARENTID": "",
            "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
        }
        for i, acct in enumerate(ACCOUNTS)
    ]


def _generate_trial_balance() -> list[dict]:
    """Generate balanced trial balance in Sage Intacct format.

    Total debits = total credits across all accounts.
    """
    # Generate all accounts except last
    records = []
    for acct_num, acct_name, acct_type, normal_bal in ACCOUNTS[:-1]:
        beg = round(random.uniform(10000, 500000), 2)
        debits = round(random.uniform(5000, 200000), 2)
        credits = round(random.uniform(5000, 200000), 2)
        end = round(beg + debits - credits, 2)
        records.append({
            "ACCOUNTNO": acct_num,
            "ACCOUNTTITLE": acct_name,
            "BEGINBALANCE": str(beg),
            "ENDBALANCE": str(end),
            "TOTALDEBIT": str(debits),
            "TOTALCREDIT": str(credits),
        })

    # Last account: force exact balance
    total_d = sum(float(r["TOTALDEBIT"]) for r in records)
    total_c = sum(float(r["TOTALCREDIT"]) for r in records)
    last = ACCOUNTS[-1]
    beg = round(random.uniform(10000, 500000), 2)
    base = round(random.uniform(50000, 150000), 2)
    diff = round(total_d - total_c, 2)
    if diff >= 0:
        debits = base
        credits = round(base + diff, 2)
    else:
        credits = base
        debits = round(base + abs(diff), 2)
    end = round(beg + debits - credits, 2)
    records.append({
        "ACCOUNTNO": last[0],
        "ACCOUNTTITLE": last[1],
        "BEGINBALANCE": str(beg),
        "ENDBALANCE": str(end),
        "TOTALDEBIT": str(debits),
        "TOTALCREDIT": str(credits),
    })

    return records


def _generate_ap_bills(count: int = 60) -> list[dict]:
    """Generate AP bills in Sage Intacct APBILL format."""
    records = []
    for i in range(count):
        vendor = random.choice(VENDORS)
        inv_date = date(FISCAL_YEAR, random.randint(1, 3), random.randint(1, 28))
        due_date = inv_date + timedelta(days=random.choice([15, 30, 45, 60]))
        total = round(random.uniform(1000, 65000), 2)

        days_past = (date(FISCAL_YEAR, 3, 27) - due_date).days
        if days_past > 45:
            paid = total if random.random() < 0.75 else 0
        elif days_past > 15:
            paid = total if random.random() < 0.5 else round(total * random.uniform(0.2, 0.6), 2)
        else:
            paid = 0 if random.random() < 0.7 else total

        balance = round(total - paid, 2)
        state = "Paid" if paid >= total else ("Partially Paid" if paid > 0 else "Posted")

        records.append({
            "RECORDNO": str(20000 + i),
            "VENDORID": vendor[0],
            "VENDORNAME": vendor[1],
            "RECORDID": f"BILL-{i + 1:04d}",
            "WHENCREATED": inv_date.strftime("%m/%d/%Y"),
            "WHENDUE": due_date.strftime("%m/%d/%Y"),
            "TOTALDUE": str(total),
            "TOTALPAID": str(paid),
            "DESCRIPTION": f"Bill from {vendor[1]}",
            "CURRENCY": "USD",
            "STATE": state,
            "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
        })
    return records


def _generate_ar_invoices(count: int = 75) -> list[dict]:
    """Generate AR invoices in Sage Intacct ARINVOICE format."""
    records = []
    for i in range(count):
        customer = random.choice(CUSTOMERS)
        inv_date = date(FISCAL_YEAR, random.randint(1, 3), random.randint(1, 28))
        due_date = inv_date + timedelta(days=random.choice([30, 45, 60]))
        total = round(random.uniform(5000, 95000), 2)

        days_past = (date(FISCAL_YEAR, 3, 27) - due_date).days
        if days_past > 60:
            paid = total if random.random() < 0.7 else 0
        elif days_past > 30:
            paid = total if random.random() < 0.5 else round(total * random.uniform(0.3, 0.7), 2)
        else:
            paid = 0 if random.random() < 0.6 else total

        balance = round(total - paid, 2)
        state = "Paid" if paid >= total else ("Partially Paid" if paid > 0 else "Posted")

        records.append({
            "RECORDNO": str(30000 + i),
            "CUSTOMERID": customer[0],
            "CUSTOMERNAME": customer[1],
            "RECORDID": f"INV-{i + 1:04d}",
            "WHENCREATED": inv_date.strftime("%m/%d/%Y"),
            "WHENDUE": due_date.strftime("%m/%d/%Y"),
            "TOTALDUE": str(total),
            "TOTALPAID": str(paid),
            "DESCRIPTION": f"Invoice to {customer[1]}",
            "CURRENCY": "USD",
            "STATE": state,
            "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
        })
    return records


def _generate_vendors() -> list[dict]:
    """Generate vendors in Sage Intacct VENDOR format."""
    return [
        {
            "RECORDNO": str(i + 1),
            "VENDORID": v[0],
            "NAME": v[1],
            "STATUS": "active",
            "TERMNAME": random.choice(["Net 15", "Net 30", "Net 45", "Net 60"]),
            "DISPLAYCONTACT_EMAIL1": f"billing@{v[1].lower().replace(' ', '').replace(',', '')[:12]}.com",
            "DISPLAYCONTACT_MAILADDRESS_ADDRESS1": f"{random.randint(100, 9999)} Business Ave",
            "DISPLAYCONTACT_MAILADDRESS_CITY": random.choice(["Denver", "Austin", "Seattle", "NYC"]),
            "DISPLAYCONTACT_MAILADDRESS_STATE": random.choice(["CO", "TX", "WA", "NY"]),
            "DISPLAYCONTACT_MAILADDRESS_ZIP": f"{random.randint(10000, 99999)}",
            "DISPLAYCONTACT_MAILADDRESS_COUNTRY": "US",
            "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
        }
        for i, v in enumerate(VENDORS)
    ]


def _generate_customers() -> list[dict]:
    """Generate customers in Sage Intacct CUSTOMER format."""
    return [
        {
            "RECORDNO": str(i + 1),
            "CUSTOMERID": c[0],
            "NAME": c[1],
            "STATUS": "active",
            "TERMNAME": random.choice(["Net 30", "Net 45", "Net 60"]),
            "CREDITLIMIT": str(round(random.uniform(100000, 1000000), 2)),
            "DISPLAYCONTACT_EMAIL1": f"ap@{c[1].lower().replace(' ', '')[:12]}.com",
            "DISPLAYCONTACT_MAILADDRESS_ADDRESS1": f"{random.randint(100, 9999)} Commerce Blvd",
            "DISPLAYCONTACT_MAILADDRESS_CITY": random.choice(["Chicago", "Boston", "Portland", "Miami"]),
            "DISPLAYCONTACT_MAILADDRESS_STATE": random.choice(["IL", "MA", "OR", "FL"]),
            "DISPLAYCONTACT_MAILADDRESS_ZIP": f"{random.randint(10000, 99999)}",
            "DISPLAYCONTACT_MAILADDRESS_COUNTRY": "US",
            "WHENMODIFIED": datetime.now(timezone.utc).isoformat(),
        }
        for i, c in enumerate(CUSTOMERS)
    ]


# ── Object Generator Dispatch ──────────────────────────────────────────

_GENERATORS = {
    "GLDETAIL": lambda: _generate_gl_detail(500),
    "GLACCOUNT": _generate_accounts,
    "TRIALBALANCE": _generate_trial_balance,
    "APBILL": lambda: _generate_ap_bills(60),
    "ARINVOICE": lambda: _generate_ar_invoices(75),
    "VENDOR": _generate_vendors,
    "CUSTOMER": _generate_customers,
}


# ── Synthetic Connector ────────────────────────────────────────────────


class SyntheticSageConnector(BaseConnector):
    """
    Drop-in replacement for SageIntacctConnector that generates
    realistic financial data in Sage Intacct XML format.

    The real transforms, contract writers, quality gate, and KPI engine
    all execute against this synthetic data — proving the full pipeline.
    """

    def __init__(self, config: dict | None = None, **kwargs):
        super().__init__(config or {})
        self._gl_count = (config or {}).get("gl_count", 500)
        self._ap_count = (config or {}).get("ap_count", 60)
        self._ar_count = (config or {}).get("ar_count", 75)
        log.info("synthetic_connector: initialized (gl=%d, ap=%d, ar=%d)",
                 self._gl_count, self._ap_count, self._ar_count)

    @property
    def source_type(self) -> str:
        return "synthetic_sage"

    def test_connection(self) -> dict:
        return {"ok": True, "message": "Synthetic connector ready", "latency_ms": 1}

    def get_schema(self) -> list[dict]:
        return [
            {"name": obj.api_name, "description": obj.description,
             "estimated_rows": 500 if obj.api_name == "GLDETAIL" else 50,
             "canonical_target": obj.canonical}
            for obj in OBJECT_CATALOG.values()
        ]

    def extract(
        self,
        object_name: str,
        watermark: str | None = None,
        batch_size: int = 1000,
    ) -> Generator[list[dict], None, None]:
        """Generate synthetic data, apply real Sage transforms, yield batches."""
        generator = _GENERATORS.get(object_name)
        if not generator:
            log.warning("synthetic_connector: no generator for %s", object_name)
            return

        # Override counts from config
        if object_name == "GLDETAIL":
            raw_records = _generate_gl_detail(self._gl_count)
        elif object_name == "APBILL":
            raw_records = _generate_ap_bills(self._ap_count)
        elif object_name == "ARINVOICE":
            raw_records = _generate_ar_invoices(self._ar_count)
        else:
            raw_records = generator()

        # Apply watermark filter (simulate incremental — return subset)
        if watermark:
            # Return ~30% of records to simulate incremental delta
            raw_records = raw_records[:max(1, len(raw_records) // 3)]
            log.info("synthetic_connector: incremental mode — returning %d/%d records for %s",
                     len(raw_records), len(raw_records) * 3, object_name)

        # Apply real Sage Intacct transforms
        transformer = SAGE_TRANSFORMERS.get(object_name)
        if transformer:
            records = transformer(raw_records)
        else:
            records = raw_records

        # Yield in batches
        for i in range(0, len(records), batch_size):
            yield records[i:i + batch_size]

        log.info("synthetic_connector: extracted %d records for %s", len(records), object_name)

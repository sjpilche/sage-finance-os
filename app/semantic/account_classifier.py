"""
semantic.account_classifier
===========================
Maps chart of accounts entries to statement template lines.

Uses account_type from the COA as the primary classification,
with account_name keyword matching for sub-classification
(e.g. distinguishing "Cash" from "Accounts Receivable" within Assets).
"""

from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

# Keyword patterns for sub-classifying accounts within an account_type.
# Each pattern maps to a statement template line_key.
# Checked in order — first match wins.

_ASSET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("cash", re.compile(r"cash|bank|checking|savings|money market", re.I)),
    ("accounts_receivable", re.compile(r"accounts?\s*receivable|a/?r\b|trade\s*receiv", re.I)),
    ("inventory", re.compile(r"inventor", re.I)),
    ("prepaid_expenses", re.compile(r"prepaid|prepay", re.I)),
    ("accumulated_depreciation", re.compile(r"accum.*deprec|accum.*amort", re.I)),
    ("property_equipment", re.compile(r"property|equipment|furniture|vehicle|machine|computer|leasehold", re.I)),
]

_LIABILITY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("accounts_payable", re.compile(r"accounts?\s*payable|a/?p\b|trade\s*payable", re.I)),
    ("accrued_liabilities", re.compile(r"accru", re.I)),
    ("current_debt", re.compile(r"current.*(?:debt|loan|note|line.*credit)|short.*term.*(?:debt|loan)", re.I)),
    ("long_term_debt", re.compile(r"long.*term.*(?:debt|loan|note|mortgage)|(?:debt|loan|note|mortgage).*long", re.I)),
]

_EQUITY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("common_stock", re.compile(r"common.*stock|capital.*stock|paid.*in.*capital|contributed", re.I)),
    ("retained_earnings", re.compile(r"retain.*earn|net.*income.*(?:loss|summary)|undistrib", re.I)),
]

_REVENUE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("interest_income", re.compile(r"interest.*(?:income|earn|rev)", re.I)),
    ("other_income", re.compile(r"other.*(?:income|rev)|gain|miscell.*income", re.I)),
    ("operating_revenue", re.compile(r".*", re.I)),  # catch-all
]

_EXPENSE_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("direct_costs", re.compile(r"cost.*(?:goods|sales|service|revenue)|cogs|direct.*cost|material", re.I)),
    ("payroll", re.compile(r"payroll|salary|salaries|wages|benefit|compensation|bonus|401k|health.*ins", re.I)),
    ("rent_facilities", re.compile(r"rent|lease|facilit|utilit|electric|water|gas\b|telecom|internet", re.I)),
    ("depreciation", re.compile(r"deprec|amortiz", re.I)),
    ("interest_expense", re.compile(r"interest.*(?:expense|paid|cost)", re.I)),
    ("sales_marketing", re.compile(r"sales|marketing|advertis|promotion|trade\s*show", re.I)),
    ("general_admin", re.compile(r"admin|office|legal|accounting|audit|insur|tax|license|permit|profess.*fee", re.I)),
]


_TYPE_PATTERNS: dict[str, list[tuple[str, re.Pattern]]] = {
    "Asset": _ASSET_PATTERNS,
    "Liability": _LIABILITY_PATTERNS,
    "Equity": _EQUITY_PATTERNS,
    "Revenue": _REVENUE_PATTERNS,
    "Expense": _EXPENSE_PATTERNS,
}

# Fallback line_keys when no pattern matches
_TYPE_FALLBACKS: dict[str, str] = {
    "Asset": "other_current_assets",
    "Liability": "other_current_liabilities",
    "Equity": "other_equity",
    "Revenue": "operating_revenue",
    "Expense": "other_opex",
}


def classify_account(account_type: str, account_name: str) -> str:
    """
    Classify a COA account into a statement template line_key.

    Parameters
    ----------
    account_type:  From contract.chart_of_accounts.account_type
                   ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')
    account_name:  Human-readable account name for keyword matching.

    Returns
    -------
    Statement template line_key (e.g. 'cash', 'accounts_payable', 'payroll').
    """
    patterns = _TYPE_PATTERNS.get(account_type, [])

    for line_key, pattern in patterns:
        if pattern.search(account_name):
            return line_key

    return _TYPE_FALLBACKS.get(account_type, "other_opex")


def classify_accounts_bulk(conn, tenant_id: str) -> dict[str, str]:
    """
    Classify all accounts for a tenant.

    Returns
    -------
    dict mapping account_number → statement line_key.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT account_number, account_type, account_name "
            "FROM contract.chart_of_accounts WHERE tenant_id = %s",
            (tenant_id,),
        )
        rows = cur.fetchall()

    result = {}
    for row in rows:
        acct_num = row[0]
        acct_type = row[1]
        acct_name = row[2]
        result[acct_num] = classify_account(acct_type, acct_name)

    log.info("classifier: classified %d accounts for tenant %s", len(result), tenant_id)
    return result

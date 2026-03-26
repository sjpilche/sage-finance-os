"""
semantic.statement_templates
============================
P&L and Balance Sheet template definitions.

Defines the line hierarchy for financial statements. Each line maps to
account types from the chart of accounts. The template engine builds
statements by summing GL entries that match each line's account_type_filter.

Inspired by Jake's Finance Semantic Kernel — rebuilt clean with
configurable hierarchy, no Empire-specific mappings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StatementLine:
    """One line in a financial statement template."""
    key: str
    display_name: str
    parent_key: str | None = None
    sort_order: int = 0
    line_type: str = "detail"       # header, detail, subtotal, total
    sign_convention: int = 1        # 1 = natural, -1 = flip
    account_type_filter: str = ""   # 'Revenue', 'Expense', etc.
    is_calculated: bool = False     # True = sum of children
    formula: str = ""               # e.g. 'revenue - cogs' for gross_profit


# -- Income Statement Template ------------------------------------------------

INCOME_STATEMENT: list[StatementLine] = [
    StatementLine("revenue", "Revenue", None, 10, "header", 1, "Revenue"),
    StatementLine("operating_revenue", "Operating Revenue", "revenue", 11, "detail", 1, "Revenue"),

    StatementLine("cogs", "Cost of Goods Sold", None, 20, "header", -1, "Expense"),
    StatementLine("direct_costs", "Direct Costs", "cogs", 21, "detail", -1, "Expense"),

    StatementLine("gross_profit", "Gross Profit", None, 30, "subtotal", 1, "",
                  is_calculated=True, formula="revenue - cogs"),

    StatementLine("operating_expenses", "Operating Expenses", None, 40, "header", -1, "Expense"),
    StatementLine("payroll", "Payroll & Benefits", "operating_expenses", 41, "detail", -1, "Expense"),
    StatementLine("rent_facilities", "Rent & Facilities", "operating_expenses", 42, "detail", -1, "Expense"),
    StatementLine("general_admin", "General & Administrative", "operating_expenses", 43, "detail", -1, "Expense"),
    StatementLine("sales_marketing", "Sales & Marketing", "operating_expenses", 44, "detail", -1, "Expense"),
    StatementLine("depreciation", "Depreciation & Amortization", "operating_expenses", 45, "detail", -1, "Expense"),
    StatementLine("other_opex", "Other Operating Expenses", "operating_expenses", 49, "detail", -1, "Expense"),

    StatementLine("operating_income", "Operating Income", None, 50, "subtotal", 1, "",
                  is_calculated=True, formula="gross_profit - operating_expenses"),

    StatementLine("other_income_expense", "Other Income / (Expense)", None, 60, "header", 1, ""),
    StatementLine("interest_income", "Interest Income", "other_income_expense", 61, "detail", 1, "Revenue"),
    StatementLine("interest_expense", "Interest Expense", "other_income_expense", 62, "detail", -1, "Expense"),
    StatementLine("other_income", "Other Income", "other_income_expense", 63, "detail", 1, "Revenue"),

    StatementLine("net_income", "Net Income", None, 90, "total", 1, "",
                  is_calculated=True, formula="operating_income + other_income_expense"),
]


# -- Balance Sheet Template ----------------------------------------------------

BALANCE_SHEET: list[StatementLine] = [
    # Assets
    StatementLine("current_assets", "Current Assets", None, 10, "header", 1, "Asset"),
    StatementLine("cash", "Cash & Cash Equivalents", "current_assets", 11, "detail", 1, "Asset"),
    StatementLine("accounts_receivable", "Accounts Receivable", "current_assets", 12, "detail", 1, "Asset"),
    StatementLine("inventory", "Inventory", "current_assets", 13, "detail", 1, "Asset"),
    StatementLine("prepaid_expenses", "Prepaid Expenses", "current_assets", 14, "detail", 1, "Asset"),
    StatementLine("other_current_assets", "Other Current Assets", "current_assets", 19, "detail", 1, "Asset"),

    StatementLine("total_current_assets", "Total Current Assets", None, 20, "subtotal", 1, "",
                  is_calculated=True),

    StatementLine("fixed_assets", "Fixed Assets", None, 30, "header", 1, "Asset"),
    StatementLine("property_equipment", "Property & Equipment", "fixed_assets", 31, "detail", 1, "Asset"),
    StatementLine("accumulated_depreciation", "Accumulated Depreciation", "fixed_assets", 32, "detail", -1, "Asset"),
    StatementLine("other_fixed_assets", "Other Fixed Assets", "fixed_assets", 39, "detail", 1, "Asset"),

    StatementLine("total_assets", "Total Assets", None, 40, "total", 1, "",
                  is_calculated=True),

    # Liabilities
    StatementLine("current_liabilities", "Current Liabilities", None, 50, "header", 1, "Liability"),
    StatementLine("accounts_payable", "Accounts Payable", "current_liabilities", 51, "detail", 1, "Liability"),
    StatementLine("accrued_liabilities", "Accrued Liabilities", "current_liabilities", 52, "detail", 1, "Liability"),
    StatementLine("current_debt", "Current Portion of Debt", "current_liabilities", 53, "detail", 1, "Liability"),
    StatementLine("other_current_liabilities", "Other Current Liabilities", "current_liabilities", 59, "detail", 1, "Liability"),

    StatementLine("total_current_liabilities", "Total Current Liabilities", None, 60, "subtotal", 1, "",
                  is_calculated=True),

    StatementLine("long_term_liabilities", "Long-Term Liabilities", None, 70, "header", 1, "Liability"),
    StatementLine("long_term_debt", "Long-Term Debt", "long_term_liabilities", 71, "detail", 1, "Liability"),
    StatementLine("other_lt_liabilities", "Other Long-Term Liabilities", "long_term_liabilities", 79, "detail", 1, "Liability"),

    StatementLine("total_liabilities", "Total Liabilities", None, 80, "subtotal", 1, "",
                  is_calculated=True),

    # Equity
    StatementLine("equity", "Equity", None, 90, "header", 1, "Equity"),
    StatementLine("common_stock", "Common Stock", "equity", 91, "detail", 1, "Equity"),
    StatementLine("retained_earnings", "Retained Earnings", "equity", 92, "detail", 1, "Equity"),
    StatementLine("other_equity", "Other Equity", "equity", 99, "detail", 1, "Equity"),

    StatementLine("total_equity", "Total Equity", None, 95, "subtotal", 1, "",
                  is_calculated=True),

    StatementLine("total_liabilities_equity", "Total Liabilities & Equity", None, 99, "total", 1, "",
                  is_calculated=True),
]


TEMPLATES = {
    "income_statement": INCOME_STATEMENT,
    "balance_sheet": BALANCE_SHEET,
}


def get_template(name: str) -> list[StatementLine]:
    """Get a statement template by name."""
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template: {name}. Valid: {list(TEMPLATES.keys())}")
    return TEMPLATES[name]


def get_detail_lines(template_name: str) -> list[StatementLine]:
    """Get only detail lines (not calculated) for account mapping."""
    return [line for line in get_template(template_name)
            if not line.is_calculated and line.account_type_filter]

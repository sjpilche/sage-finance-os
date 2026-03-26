"""
semantic.metric_registry
========================
Canonical finance metric definitions with SQL formulas.

Each metric is a deterministic SQL computation — no ML, no LLM.
Metrics are grouped by category and can be materialized per entity/period.

Categories:
  revenue, expense, profitability, liquidity, efficiency, leverage, aging
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MetricDef:
    """Definition of a single finance metric."""
    name: str
    display_name: str
    description: str
    category: str          # revenue, expense, profitability, liquidity, efficiency, leverage, aging
    unit: str              # currency, percentage, days, ratio, count
    direction: str         # higher_better, lower_better, neutral
    sql: str               # SQL expression (uses {schema} placeholder for contract schema)


# -- Metric Catalog ------------------------------------------------------------

METRICS: dict[str, MetricDef] = {}


def _reg(m: MetricDef) -> MetricDef:
    METRICS[m.name] = m
    return m


# ── Revenue metrics ──────────────────────────────────────────

_reg(MetricDef(
    name="total_revenue",
    display_name="Total Revenue",
    description="Sum of all revenue account postings (credit balances)",
    category="revenue", unit="currency", direction="higher_better",
    sql="""
    SELECT COALESCE(SUM(credit_amount - debit_amount), 0)
    FROM contract.gl_entry g
    JOIN contract.chart_of_accounts c ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
    WHERE g.tenant_id = %(tenant_id)s AND c.account_type = 'Revenue'
      AND g.fiscal_year = %(fiscal_year)s AND (%(fiscal_period)s IS NULL OR g.fiscal_period = %(fiscal_period)s)
    """,
))

_reg(MetricDef(
    name="total_expenses",
    display_name="Total Expenses",
    description="Sum of all expense account postings (debit balances)",
    category="expense", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(debit_amount - credit_amount), 0)
    FROM contract.gl_entry g
    JOIN contract.chart_of_accounts c ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
    WHERE g.tenant_id = %(tenant_id)s AND c.account_type = 'Expense'
      AND g.fiscal_year = %(fiscal_year)s AND (%(fiscal_period)s IS NULL OR g.fiscal_period = %(fiscal_period)s)
    """,
))

# ── Profitability metrics ────────────────────────────────────

_reg(MetricDef(
    name="net_income",
    display_name="Net Income",
    description="Total Revenue minus Total Expenses",
    category="profitability", unit="currency", direction="higher_better",
    sql="""
    SELECT COALESCE(
        (SELECT SUM(credit_amount - debit_amount) FROM contract.gl_entry g
         JOIN contract.chart_of_accounts c ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
         WHERE g.tenant_id = %(tenant_id)s AND c.account_type = 'Revenue'
           AND g.fiscal_year = %(fiscal_year)s AND (%(fiscal_period)s IS NULL OR g.fiscal_period = %(fiscal_period)s))
        -
        (SELECT SUM(debit_amount - credit_amount) FROM contract.gl_entry g
         JOIN contract.chart_of_accounts c ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
         WHERE g.tenant_id = %(tenant_id)s AND c.account_type = 'Expense'
           AND g.fiscal_year = %(fiscal_year)s AND (%(fiscal_period)s IS NULL OR g.fiscal_period = %(fiscal_period)s)),
    0)
    """,
))

_reg(MetricDef(
    name="net_margin_pct",
    display_name="Net Margin %",
    description="Net Income / Total Revenue × 100",
    category="profitability", unit="percentage", direction="higher_better",
    sql="",  # computed from net_income / total_revenue
))

# ── Liquidity metrics ────────────────────────────────────────

_reg(MetricDef(
    name="total_cash",
    display_name="Cash Position",
    description="Sum of cash and cash equivalent account balances",
    category="liquidity", unit="currency", direction="higher_better",
    sql="""
    SELECT COALESCE(SUM(ending_balance), 0)
    FROM contract.trial_balance tb
    JOIN contract.chart_of_accounts c ON tb.account_number = c.account_number AND tb.tenant_id = c.tenant_id
    WHERE tb.tenant_id = %(tenant_id)s AND c.account_type = 'Asset'
      AND (c.account_name ILIKE '%%cash%%' OR c.account_name ILIKE '%%bank%%' OR c.account_name ILIKE '%%checking%%')
    """,
))

_reg(MetricDef(
    name="current_ratio",
    display_name="Current Ratio",
    description="Current Assets / Current Liabilities",
    category="liquidity", unit="ratio", direction="higher_better",
    sql="",  # computed from current assets / current liabilities
))

_reg(MetricDef(
    name="working_capital",
    display_name="Working Capital",
    description="Current Assets minus Current Liabilities",
    category="liquidity", unit="currency", direction="higher_better",
    sql="",  # computed
))

# ── Efficiency metrics ───────────────────────────────────────

_reg(MetricDef(
    name="dso",
    display_name="Days Sales Outstanding",
    description="(AR Balance / Daily Revenue) — how fast customers pay",
    category="efficiency", unit="days", direction="lower_better",
    sql="""
    SELECT CASE
        WHEN rev.daily_rev > 0
        THEN ROUND(ar.balance / rev.daily_rev, 1)
        ELSE 0
    END
    FROM (
        SELECT COALESCE(SUM(balance), 0) AS balance
        FROM contract.ar_invoice
        WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
    ) ar,
    (
        SELECT COALESCE(SUM(credit_amount - debit_amount), 0) / GREATEST(COUNT(DISTINCT posting_date), 1) AS daily_rev
        FROM contract.gl_entry g
        JOIN contract.chart_of_accounts c ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
        WHERE g.tenant_id = %(tenant_id)s AND c.account_type = 'Revenue'
          AND g.fiscal_year = %(fiscal_year)s
    ) rev
    """,
))

_reg(MetricDef(
    name="dpo",
    display_name="Days Payable Outstanding",
    description="(AP Balance / Daily Expenses) — how fast we pay vendors",
    category="efficiency", unit="days", direction="neutral",
    sql="""
    SELECT CASE
        WHEN exp.daily_exp > 0
        THEN ROUND(ap.balance / exp.daily_exp, 1)
        ELSE 0
    END
    FROM (
        SELECT COALESCE(SUM(balance), 0) AS balance
        FROM contract.ap_invoice
        WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
    ) ap,
    (
        SELECT COALESCE(SUM(debit_amount - credit_amount), 0) / GREATEST(COUNT(DISTINCT posting_date), 1) AS daily_exp
        FROM contract.gl_entry g
        JOIN contract.chart_of_accounts c ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
        WHERE g.tenant_id = %(tenant_id)s AND c.account_type = 'Expense'
          AND g.fiscal_year = %(fiscal_year)s
    ) exp
    """,
))

# ── AP / AR metrics ──────────────────────────────────────────

_reg(MetricDef(
    name="ar_balance",
    display_name="AR Outstanding",
    description="Total open AR invoice balance",
    category="aging", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ar_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
    """,
))

_reg(MetricDef(
    name="ap_balance",
    display_name="AP Outstanding",
    description="Total open AP invoice balance",
    category="aging", unit="currency", direction="neutral",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ap_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
    """,
))

_reg(MetricDef(
    name="ar_aging_current",
    display_name="AR Current (0-30 days)",
    description="AR invoices due within 30 days",
    category="aging", unit="currency", direction="neutral",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ar_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
      AND due_date >= CURRENT_DATE - INTERVAL '30 days'
    """,
))

_reg(MetricDef(
    name="ar_aging_31_60",
    display_name="AR 31-60 days",
    description="AR invoices 31-60 days past due",
    category="aging", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ar_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
      AND due_date < CURRENT_DATE - INTERVAL '30 days'
      AND due_date >= CURRENT_DATE - INTERVAL '60 days'
    """,
))

_reg(MetricDef(
    name="ar_aging_61_90",
    display_name="AR 61-90 days",
    description="AR invoices 61-90 days past due",
    category="aging", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ar_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
      AND due_date < CURRENT_DATE - INTERVAL '60 days'
      AND due_date >= CURRENT_DATE - INTERVAL '90 days'
    """,
))

_reg(MetricDef(
    name="ar_aging_over_90",
    display_name="AR Over 90 days",
    description="AR invoices over 90 days past due",
    category="aging", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ar_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
      AND due_date < CURRENT_DATE - INTERVAL '90 days'
    """,
))

_reg(MetricDef(
    name="ap_aging_current",
    display_name="AP Current (0-30 days)",
    description="AP invoices due within 30 days",
    category="aging", unit="currency", direction="neutral",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ap_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
      AND due_date >= CURRENT_DATE - INTERVAL '30 days'
    """,
))

_reg(MetricDef(
    name="ap_aging_31_60",
    display_name="AP 31-60 days",
    description="AP invoices 31-60 days past due",
    category="aging", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ap_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
      AND due_date < CURRENT_DATE - INTERVAL '30 days'
      AND due_date >= CURRENT_DATE - INTERVAL '60 days'
    """,
))

_reg(MetricDef(
    name="ap_aging_over_60",
    display_name="AP Over 60 days",
    description="AP invoices over 60 days past due",
    category="aging", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(balance), 0)
    FROM contract.ap_invoice
    WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')
      AND due_date < CURRENT_DATE - INTERVAL '60 days'
    """,
))

# ── Count / volume metrics ───────────────────────────────────

_reg(MetricDef(
    name="gl_entry_count",
    display_name="GL Entry Count",
    description="Total GL journal entries",
    category="revenue", unit="count", direction="neutral",
    sql="SELECT count(*) FROM contract.gl_entry WHERE tenant_id = %(tenant_id)s AND fiscal_year = %(fiscal_year)s",
))

_reg(MetricDef(
    name="vendor_count",
    display_name="Active Vendors",
    description="Number of active vendors",
    category="expense", unit="count", direction="neutral",
    sql="SELECT count(*) FROM contract.vendor WHERE tenant_id = %(tenant_id)s AND status = 'active'",
))

_reg(MetricDef(
    name="customer_count",
    display_name="Active Customers",
    description="Number of active customers",
    category="revenue", unit="count", direction="higher_better",
    sql="SELECT count(*) FROM contract.customer WHERE tenant_id = %(tenant_id)s AND status = 'active'",
))

_reg(MetricDef(
    name="open_ap_count",
    display_name="Open AP Invoices",
    description="Number of unpaid AP invoices",
    category="aging", unit="count", direction="lower_better",
    sql="SELECT count(*) FROM contract.ap_invoice WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')",
))

_reg(MetricDef(
    name="open_ar_count",
    display_name="Open AR Invoices",
    description="Number of unpaid AR invoices",
    category="aging", unit="count", direction="lower_better",
    sql="SELECT count(*) FROM contract.ar_invoice WHERE tenant_id = %(tenant_id)s AND status IN ('open', 'partial')",
))

# ── Leverage ─────────────────────────────────────────────────

_reg(MetricDef(
    name="total_assets",
    display_name="Total Assets",
    description="Sum of all asset account balances",
    category="leverage", unit="currency", direction="higher_better",
    sql="""
    SELECT COALESCE(SUM(ending_balance), 0)
    FROM contract.trial_balance tb
    JOIN contract.chart_of_accounts c ON tb.account_number = c.account_number AND tb.tenant_id = c.tenant_id
    WHERE tb.tenant_id = %(tenant_id)s AND c.account_type = 'Asset'
    """,
))

_reg(MetricDef(
    name="total_liabilities",
    display_name="Total Liabilities",
    description="Sum of all liability account balances",
    category="leverage", unit="currency", direction="lower_better",
    sql="""
    SELECT COALESCE(SUM(ending_balance), 0)
    FROM contract.trial_balance tb
    JOIN contract.chart_of_accounts c ON tb.account_number = c.account_number AND tb.tenant_id = c.tenant_id
    WHERE tb.tenant_id = %(tenant_id)s AND c.account_type = 'Liability'
    """,
))

_reg(MetricDef(
    name="total_equity",
    display_name="Total Equity",
    description="Sum of all equity account balances",
    category="leverage", unit="currency", direction="higher_better",
    sql="""
    SELECT COALESCE(SUM(ending_balance), 0)
    FROM contract.trial_balance tb
    JOIN contract.chart_of_accounts c ON tb.account_number = c.account_number AND tb.tenant_id = c.tenant_id
    WHERE tb.tenant_id = %(tenant_id)s AND c.account_type = 'Equity'
    """,
))


def get_metrics_by_category() -> dict[str, list[MetricDef]]:
    """Return metrics grouped by category."""
    result: dict[str, list[MetricDef]] = {}
    for m in METRICS.values():
        result.setdefault(m.category, []).append(m)
    return result


def get_computable_metrics() -> list[MetricDef]:
    """Return metrics that have direct SQL formulas (not computed from other metrics)."""
    return [m for m in METRICS.values() if m.sql.strip()]

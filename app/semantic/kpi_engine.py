"""
semantic.kpi_engine
===================
KPI materialization engine — computes metrics from contract data
and stores results in semantic.computed_kpis.

Runs after each successful pipeline sync. Serves pre-computed values
via the API for fast dashboard rendering.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.semantic.metric_registry import METRICS, get_computable_metrics

log = logging.getLogger(__name__)


def compute_all_kpis(
    conn,
    tenant_id: str,
    fiscal_year: int,
    fiscal_period: int | None = None,
    run_id: str | None = None,
) -> dict[str, float | None]:
    """
    Compute all metrics with SQL formulas and persist to semantic.computed_kpis.

    Parameters
    ----------
    conn:           psycopg2 connection (sync).
    tenant_id:      Tenant UUID.
    fiscal_year:    Target fiscal year.
    fiscal_period:  Target period (None = full year).
    run_id:         Pipeline run that triggered this computation.

    Returns
    -------
    dict mapping metric_name → computed value.
    """
    results: dict[str, float | None] = {}
    params = {
        "tenant_id": tenant_id,
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
    }

    computable = get_computable_metrics()

    for metric in computable:
        try:
            with conn.cursor() as cur:
                cur.execute(metric.sql, params)
                row = cur.fetchone()
                value = float(row[0]) if row and row[0] is not None else None

            results[metric.name] = value

            # Persist to computed_kpis
            _persist_kpi(conn, tenant_id, metric.name, fiscal_year, fiscal_period,
                         value, metric.unit, run_id)

        except Exception as e:
            log.warning("kpi_engine: failed to compute %s — %s", metric.name, e)
            results[metric.name] = None

    # Compute derived metrics (those without SQL, computed from other metrics)
    _compute_derived(conn, tenant_id, fiscal_year, fiscal_period, results, run_id)

    conn.commit()

    computed_count = sum(1 for v in results.values() if v is not None)
    log.info(
        "kpi_engine: computed %d/%d metrics for FY%d P%s tenant=%s",
        computed_count, len(results), fiscal_year,
        fiscal_period or "full", tenant_id[:8],
    )

    return results


def _compute_derived(
    conn, tenant_id: str, fiscal_year: int, fiscal_period: int | None,
    results: dict[str, float | None], run_id: str | None,
) -> None:
    """Compute metrics that derive from other computed metrics."""

    # Net Margin % = Net Income / Total Revenue × 100
    revenue = results.get("total_revenue")
    net_income = results.get("net_income")
    if revenue and revenue > 0 and net_income is not None:
        net_margin = round((net_income / revenue) * 100, 2)
        results["net_margin_pct"] = net_margin
        _persist_kpi(conn, tenant_id, "net_margin_pct", fiscal_year, fiscal_period,
                     net_margin, "percentage", run_id)

    # Current Ratio (not computed yet — needs current asset/liability sub-totals)
    # Working Capital (not computed yet)


def _persist_kpi(
    conn, tenant_id: str, metric_name: str,
    fiscal_year: int, fiscal_period: int | None,
    value: float | None, unit: str, run_id: str | None,
) -> None:
    """Upsert a single KPI value into semantic.computed_kpis."""
    if value is None:
        return

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO semantic.computed_kpis
                (tenant_id, metric_name, fiscal_year, fiscal_period, value, unit, run_id, computed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, entity_id, metric_name, fiscal_year, fiscal_period)
            DO UPDATE SET value = %s, unit = %s, run_id = %s, computed_at = %s
            """,
            (
                tenant_id, metric_name, fiscal_year, fiscal_period,
                value, unit, run_id, datetime.now(timezone.utc),
                value, unit, run_id, datetime.now(timezone.utc),
            ),
        )


def get_kpis(conn, tenant_id: str, fiscal_year: int | None = None) -> list[dict]:
    """
    Fetch computed KPIs for a tenant, optionally filtered by fiscal year.

    Returns list of dicts with metric metadata + computed value.
    """
    conditions = ["tenant_id = %s"]
    params: list = [tenant_id]

    if fiscal_year:
        conditions.append("fiscal_year = %s")
        params.append(fiscal_year)

    where = " AND ".join(conditions)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT metric_name, fiscal_year, fiscal_period, value, unit, computed_at
            FROM semantic.computed_kpis
            WHERE {where}
            ORDER BY metric_name, fiscal_year, fiscal_period
            """,
            params,
        )
        rows = cur.fetchall()

    result = []
    for row in rows:
        metric_def = METRICS.get(row[0])
        result.append({
            "metric_name": row[0],
            "display_name": metric_def.display_name if metric_def else row[0],
            "category": metric_def.category if metric_def else "unknown",
            "direction": metric_def.direction if metric_def else "neutral",
            "fiscal_year": row[1],
            "fiscal_period": row[2],
            "value": float(row[3]) if row[3] is not None else None,
            "unit": row[4],
            "computed_at": row[5].isoformat() if row[5] else None,
        })

    return result


def build_income_statement(conn, tenant_id: str, fiscal_year: int, fiscal_period: int | None = None) -> list[dict]:
    """
    Build an income statement from GL data using statement templates + account classifier.

    Returns list of statement lines with computed amounts.
    """
    from app.semantic.statement_templates import get_template
    from app.semantic.account_classifier import classify_accounts_bulk

    template = get_template("income_statement")
    classifications = classify_accounts_bulk(conn, tenant_id)

    # Query GL totals grouped by account
    with conn.cursor() as cur:
        period_filter = "AND g.fiscal_period = %s" if fiscal_period else ""
        params = [tenant_id, fiscal_year]
        if fiscal_period:
            params.append(fiscal_period)

        cur.execute(
            f"""
            SELECT g.account_number,
                   COALESCE(SUM(g.debit_amount), 0) AS total_debit,
                   COALESCE(SUM(g.credit_amount), 0) AS total_credit
            FROM contract.gl_entry g
            WHERE g.tenant_id = %s AND g.fiscal_year = %s {period_filter}
            GROUP BY g.account_number
            """,
            params,
        )
        gl_totals = {row[0]: (float(row[1]), float(row[2])) for row in cur.fetchall()}

    # Accumulate amounts per line_key
    line_amounts: dict[str, float] = {}
    for acct_num, (debit, credit) in gl_totals.items():
        line_key = classifications.get(acct_num)
        if not line_key:
            continue
        # Revenue accounts: credit - debit (natural credit balance)
        # Expense accounts: debit - credit (natural debit balance)
        # We use the sign_convention from the template line
        net = credit - debit  # positive for revenue, negative for expense
        line_amounts[line_key] = line_amounts.get(line_key, 0) + net

    # Build result lines
    result = []
    for line in template:
        if line.is_calculated:
            # Sum children or apply formula
            amount = _sum_children(line.key, template, line_amounts)
        else:
            amount = line_amounts.get(line.key, 0) * line.sign_convention

        result.append({
            "line_key": line.key,
            "display_name": line.display_name,
            "line_type": line.line_type,
            "parent_key": line.parent_key,
            "sort_order": line.sort_order,
            "amount": round(amount, 2),
        })

    return result


def _sum_children(parent_key: str, template: list, line_amounts: dict[str, float]) -> float:
    """Sum amounts for all direct children of a parent line."""
    total = 0.0
    for line in template:
        if line.parent_key == parent_key and not line.is_calculated:
            total += line_amounts.get(line.key, 0) * line.sign_convention
    return total

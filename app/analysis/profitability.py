"""
analysis.profitability
======================
Profitability analysis by entity, department, or dimension.

Generates P&L summaries grouped by the requested dimension.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


_VALID_DIMENSIONS = {"dimension_1", "dimension_2", "dimension_3"}


def get_profitability_by_dimension(
    conn, tenant_id: str,
    fiscal_year: int,
    dimension: str = "dimension_1",  # dimension_1=dept, dimension_2=location, dimension_3=class
    fiscal_period: int | None = None,
) -> dict:
    """
    Compute revenue, expenses, and net income grouped by a GL dimension.

    Parameters
    ----------
    dimension: Which GL dimension to group by (dimension_1, dimension_2, dimension_3).
    """
    if dimension not in _VALID_DIMENSIONS:
        raise ValueError(f"Invalid dimension: {dimension}. Must be one of {sorted(_VALID_DIMENSIONS)}")

    period_filter = "AND g.fiscal_period = %s" if fiscal_period else ""
    params = [tenant_id, fiscal_year]
    if fiscal_period:
        params.append(fiscal_period)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                COALESCE(g.{dimension}, '(unassigned)') AS dim_value,
                COALESCE(SUM(CASE WHEN c.account_type = 'Revenue'
                    THEN g.credit_amount - g.debit_amount ELSE 0 END), 0) AS revenue,
                COALESCE(SUM(CASE WHEN c.account_type = 'Expense'
                    THEN g.debit_amount - g.credit_amount ELSE 0 END), 0) AS expenses
            FROM contract.gl_entry g
            JOIN contract.chart_of_accounts c
                ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
            WHERE g.tenant_id = %s AND g.fiscal_year = %s
              AND c.account_type IN ('Revenue', 'Expense')
              {period_filter}
            GROUP BY COALESCE(g.{dimension}, '(unassigned)')
            ORDER BY revenue DESC
            """,
            params,
        )
        rows = cur.fetchall()

    segments = []
    total_revenue = 0.0
    total_expenses = 0.0

    for row in rows:
        rev = float(row[1])
        exp = float(row[2])
        net = rev - exp
        margin_pct = round((net / rev) * 100, 2) if rev > 0 else 0.0

        total_revenue += rev
        total_expenses += exp

        segments.append({
            "dimension_value": row[0],
            "revenue": round(rev, 2),
            "expenses": round(exp, 2),
            "net_income": round(net, 2),
            "margin_pct": margin_pct,
        })

    total_net = total_revenue - total_expenses

    return {
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "dimension": dimension,
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "total_net_income": round(total_net, 2),
            "total_margin_pct": round((total_net / total_revenue) * 100, 2) if total_revenue > 0 else 0.0,
            "segment_count": len(segments),
        },
        "segments": segments,
    }

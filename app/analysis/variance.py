"""
analysis.variance
=================
Budget vs actual variance analysis.

Compares actual GL amounts to budget_line entries by entity/department/account/period.
Flags variances exceeding configurable thresholds.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

# Variance > this % is flagged as significant
VARIANCE_THRESHOLD_PCT = 10.0


def get_variance_report(
    conn, tenant_id: str,
    fiscal_year: int,
    fiscal_period: int | None = None,
    threshold_pct: float = VARIANCE_THRESHOLD_PCT,
) -> dict:
    """
    Compute budget vs actual variance by account.

    Returns dict with summary + detail rows.
    """
    period_filter = "AND g.fiscal_period = %s" if fiscal_period else ""
    budget_period_filter = "AND b.fiscal_period = %s" if fiscal_period else ""

    params = [tenant_id, fiscal_year]
    if fiscal_period:
        params.append(fiscal_period)

    with conn.cursor() as cur:
        # Get budget lines
        cur.execute(
            f"""
            SELECT b.account_number,
                   SUM(b.budget_amount) AS budget_amount
            FROM contract.budget_line b
            WHERE b.tenant_id = %s AND b.fiscal_year = %s
              {budget_period_filter}
            GROUP BY b.account_number
            """,
            params,
        )
        budgets = {row[0]: float(row[1]) for row in cur.fetchall()}

        # Get actuals from GL
        cur.execute(
            f"""
            SELECT g.account_number,
                   c.account_name,
                   c.account_type,
                   SUM(CASE WHEN c.account_type = 'Revenue'
                       THEN g.credit_amount - g.debit_amount
                       ELSE g.debit_amount - g.credit_amount END) AS actual_amount
            FROM contract.gl_entry g
            JOIN contract.chart_of_accounts c
                ON g.account_number = c.account_number AND g.tenant_id = c.tenant_id
            WHERE g.tenant_id = %s AND g.fiscal_year = %s
              {period_filter}
            GROUP BY g.account_number, c.account_name, c.account_type
            """,
            params,
        )
        actuals = cur.fetchall()

    # Build variance detail
    details = []
    total_budget = 0.0
    total_actual = 0.0
    flagged_count = 0

    for row in actuals:
        acct_num, acct_name, acct_type, actual = row[0], row[1], row[2], float(row[3])
        budget = budgets.get(acct_num, 0.0)

        variance = actual - budget
        variance_pct = (variance / budget * 100) if budget != 0 else (100.0 if actual != 0 else 0.0)
        is_flagged = abs(variance_pct) > threshold_pct and budget != 0

        if is_flagged:
            flagged_count += 1

        total_budget += budget
        total_actual += actual

        details.append({
            "account_number": acct_num,
            "account_name": acct_name,
            "account_type": acct_type,
            "budget": round(budget, 2),
            "actual": round(actual, 2),
            "variance": round(variance, 2),
            "variance_pct": round(variance_pct, 2),
            "is_flagged": is_flagged,
            "direction": "favorable" if (
                (acct_type == "Revenue" and variance > 0) or
                (acct_type == "Expense" and variance < 0)
            ) else "unfavorable" if variance != 0 else "on_budget",
        })

    # Sort: flagged first, then by absolute variance
    details.sort(key=lambda d: (-d["is_flagged"], -abs(d["variance"])))

    return {
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "threshold_pct": threshold_pct,
        "summary": {
            "total_budget": round(total_budget, 2),
            "total_actual": round(total_actual, 2),
            "total_variance": round(total_actual - total_budget, 2),
            "accounts_analyzed": len(details),
            "accounts_flagged": flagged_count,
        },
        "details": details,
    }

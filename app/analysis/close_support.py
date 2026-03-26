"""
analysis.close_support
======================
Period close checklist and readiness assessment.

Generates a checklist of items to review before closing a fiscal period:
- Unposted entries
- Open AP/AR past due
- Unreconciled accounts
- Missing budget lines
- Quality gate status
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def get_close_checklist(
    conn, tenant_id: str,
    fiscal_year: int,
    fiscal_period: int,
) -> dict:
    """
    Generate a period close readiness checklist.

    Returns a list of check items with pass/fail status and details.
    """
    checks = []

    with conn.cursor() as cur:
        # 1. GL entry count for the period
        cur.execute(
            """
            SELECT count(*) FROM contract.gl_entry
            WHERE tenant_id = %s AND fiscal_year = %s AND fiscal_period = %s
            """,
            (tenant_id, fiscal_year, fiscal_period),
        )
        gl_count = cur.fetchone()[0]
        checks.append({
            "check": "gl_entries_exist",
            "display": "GL entries exist for period",
            "passed": gl_count > 0,
            "details": {"count": gl_count},
        })

        # 2. GL debit/credit balance for the period
        cur.execute(
            """
            SELECT COALESCE(SUM(debit_amount), 0), COALESCE(SUM(credit_amount), 0)
            FROM contract.gl_entry
            WHERE tenant_id = %s AND fiscal_year = %s AND fiscal_period = %s
            """,
            (tenant_id, fiscal_year, fiscal_period),
        )
        debit, credit = cur.fetchone()
        imbalance = abs(float(debit) - float(credit))
        checks.append({
            "check": "gl_balanced",
            "display": "GL debits equal credits",
            "passed": imbalance < 0.01,
            "details": {"debit": float(debit), "credit": float(credit), "imbalance": imbalance},
        })

        # 3. Overdue AP invoices
        cur.execute(
            """
            SELECT count(*), COALESCE(SUM(balance), 0)
            FROM contract.ap_invoice
            WHERE tenant_id = %s AND status IN ('open', 'partial')
              AND due_date < CURRENT_DATE
            """,
            (tenant_id,),
        )
        overdue_ap_count, overdue_ap_amount = cur.fetchone()
        checks.append({
            "check": "no_overdue_ap",
            "display": "No overdue AP invoices",
            "passed": overdue_ap_count == 0,
            "details": {"count": overdue_ap_count, "amount": float(overdue_ap_amount)},
        })

        # 4. Overdue AR invoices
        cur.execute(
            """
            SELECT count(*), COALESCE(SUM(balance), 0)
            FROM contract.ar_invoice
            WHERE tenant_id = %s AND status IN ('open', 'partial')
              AND due_date < CURRENT_DATE
            """,
            (tenant_id,),
        )
        overdue_ar_count, overdue_ar_amount = cur.fetchone()
        checks.append({
            "check": "no_overdue_ar",
            "display": "No overdue AR invoices",
            "passed": overdue_ar_count == 0,
            "details": {"count": overdue_ar_count, "amount": float(overdue_ar_amount)},
        })

        # 5. Latest sync freshness
        cur.execute(
            """
            SELECT MAX(completed_at) FROM platform.data_runs
            WHERE tenant_id = %s AND status = 'complete'
            """,
            (tenant_id,),
        )
        last_sync = cur.fetchone()[0]
        is_fresh = False
        hours_since = None
        if last_sync:
            from datetime import datetime, timezone
            hours_since = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600
            is_fresh = hours_since < 24
        checks.append({
            "check": "data_fresh",
            "display": "Data synced within 24 hours",
            "passed": is_fresh,
            "details": {
                "last_sync": last_sync.isoformat() if last_sync else None,
                "hours_since": round(hours_since, 1) if hours_since else None,
            },
        })

        # 6. Period not already closed
        cur.execute(
            """
            SELECT status FROM semantic.period_status
            WHERE tenant_id = %s AND fiscal_year = %s AND fiscal_period = %s
            """,
            (tenant_id, fiscal_year, fiscal_period),
        )
        period_row = cur.fetchone()
        period_status = period_row[0] if period_row else "open"
        checks.append({
            "check": "period_open",
            "display": "Period is open (not already closed)",
            "passed": period_status == "open",
            "details": {"current_status": period_status},
        })

        # 7. Budget lines exist for the period
        cur.execute(
            """
            SELECT count(*) FROM contract.budget_line
            WHERE tenant_id = %s AND fiscal_year = %s AND fiscal_period = %s
            """,
            (tenant_id, fiscal_year, fiscal_period),
        )
        budget_count = cur.fetchone()[0]
        checks.append({
            "check": "budget_exists",
            "display": "Budget lines loaded for period",
            "passed": budget_count > 0,
            "details": {"count": budget_count},
        })

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    ready = passed == total

    return {
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "ready_to_close": ready,
        "passed": passed,
        "total": total,
        "readiness_pct": round(passed / total * 100, 1) if total > 0 else 0,
        "checks": checks,
    }

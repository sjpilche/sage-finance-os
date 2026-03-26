"""
analysis.aging
==============
AR and AP aging analysis — bucket invoices by days outstanding.

Returns aging summaries with current, 31-60, 61-90, and 90+ buckets
for both receivables and payables.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def get_ar_aging(conn, tenant_id: str) -> dict:
    """Compute AR aging buckets from open invoices."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE due_date >= CURRENT_DATE - INTERVAL '30 days') AS current_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date >= CURRENT_DATE - INTERVAL '30 days'), 0) AS current_amt,

                COUNT(*) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '30 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '60 days') AS d31_60_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '30 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '60 days'), 0) AS d31_60_amt,

                COUNT(*) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '60 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '90 days') AS d61_90_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '60 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '90 days'), 0) AS d61_90_amt,

                COUNT(*) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '90 days') AS d90_plus_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '90 days'), 0) AS d90_plus_amt,

                COUNT(*) AS total_count,
                COALESCE(SUM(balance), 0) AS total_amt
            FROM contract.ar_invoice
            WHERE tenant_id = %s AND status IN ('open', 'partial')
            """,
            (tenant_id,),
        )
        row = cur.fetchone()

    return {
        "type": "ar",
        "buckets": [
            {"label": "Current (0-30)", "count": row[0], "amount": float(row[1])},
            {"label": "31-60 days", "count": row[2], "amount": float(row[3])},
            {"label": "61-90 days", "count": row[4], "amount": float(row[5])},
            {"label": "90+ days", "count": row[6], "amount": float(row[7])},
        ],
        "total_count": row[8],
        "total_amount": float(row[9]),
    }


def get_ap_aging(conn, tenant_id: str) -> dict:
    """Compute AP aging buckets from open invoices."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE due_date >= CURRENT_DATE - INTERVAL '30 days') AS current_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date >= CURRENT_DATE - INTERVAL '30 days'), 0) AS current_amt,

                COUNT(*) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '30 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '60 days') AS d31_60_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '30 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '60 days'), 0) AS d31_60_amt,

                COUNT(*) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '60 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '90 days') AS d61_90_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '60 days'
                    AND due_date >= CURRENT_DATE - INTERVAL '90 days'), 0) AS d61_90_amt,

                COUNT(*) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '90 days') AS d90_plus_count,
                COALESCE(SUM(balance) FILTER (WHERE due_date < CURRENT_DATE - INTERVAL '90 days'), 0) AS d90_plus_amt,

                COUNT(*) AS total_count,
                COALESCE(SUM(balance), 0) AS total_amt
            FROM contract.ap_invoice
            WHERE tenant_id = %s AND status IN ('open', 'partial')
            """,
            (tenant_id,),
        )
        row = cur.fetchone()

    return {
        "type": "ap",
        "buckets": [
            {"label": "Current (0-30)", "count": row[0], "amount": float(row[1])},
            {"label": "31-60 days", "count": row[2], "amount": float(row[3])},
            {"label": "61-90 days", "count": row[4], "amount": float(row[5])},
            {"label": "90+ days", "count": row[6], "amount": float(row[7])},
        ],
        "total_count": row[8],
        "total_amount": float(row[9]),
    }


def get_ar_aging_by_customer(conn, tenant_id: str, limit: int = 20) -> list[dict]:
    """Top customers by outstanding AR balance."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT customer_code,
                   MAX(customer_name) AS customer_name,
                   COUNT(*) AS invoice_count,
                   SUM(balance) AS total_balance,
                   MIN(due_date) AS oldest_due_date,
                   MAX(CURRENT_DATE - due_date) AS max_days_outstanding
            FROM (
                SELECT i.customer_code,
                       COALESCE(c.customer_name, i.customer_code) AS customer_name,
                       i.balance, i.due_date
                FROM contract.ar_invoice i
                LEFT JOIN contract.customer c ON i.customer_code = c.customer_code AND i.tenant_id = c.tenant_id
                WHERE i.tenant_id = %s AND i.status IN ('open', 'partial')
            ) sub
            GROUP BY customer_code
            ORDER BY total_balance DESC
            LIMIT %s
            """,
            (tenant_id, limit),
        )
        rows = cur.fetchall()

    return [
        {
            "customer_code": r[0],
            "customer_name": r[1],
            "invoice_count": r[2],
            "total_balance": float(r[3]),
            "oldest_due_date": r[4].isoformat() if r[4] else None,
            "max_days_outstanding": r[5],
        }
        for r in rows
    ]

"""
semantic.period_engine
======================
Fiscal calendar and period management.

Supports configurable fiscal year end per entity (not hardcoded).
Manages period lifecycle: open → closing → closed → locked.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

log = logging.getLogger(__name__)


def get_fiscal_year(posting_date: date, fiscal_year_end_month: int = 12) -> int:
    """
    Determine fiscal year for a posting date.

    Parameters
    ----------
    posting_date:         The transaction date.
    fiscal_year_end_month: Month the fiscal year ends (1-12). Default 12 = calendar year.

    Returns
    -------
    Fiscal year (integer).

    Examples
    --------
    Calendar year (end=12): 2026-03-15 → FY 2026
    June year-end (end=6):  2026-03-15 → FY 2026, 2026-08-15 → FY 2027
    """
    if posting_date.month <= fiscal_year_end_month:
        return posting_date.year
    return posting_date.year + 1


def get_fiscal_period(posting_date: date, fiscal_year_end_month: int = 12) -> int:
    """
    Determine fiscal period (1-12) for a posting date.

    Period 1 = first month of fiscal year.
    For calendar year (end=12): January = P1, December = P12.
    For June year-end (end=6): July = P1, June = P12.
    """
    first_month = (fiscal_year_end_month % 12) + 1  # month after FY end
    period = (posting_date.month - first_month) % 12 + 1
    return period


def generate_fiscal_calendar(
    fiscal_year: int,
    fiscal_year_end_month: int = 12,
) -> list[dict]:
    """
    Generate 12 monthly periods for a fiscal year.

    Returns list of dicts with: period_number, period_name, start_date, end_date.
    """
    first_month = (fiscal_year_end_month % 12) + 1
    # For calendar year: first_month = 1, start_year = fiscal_year
    # For June year-end: first_month = 7, start_year = fiscal_year - 1
    if fiscal_year_end_month == 12:
        start_year = fiscal_year
    else:
        start_year = fiscal_year - 1

    periods = []
    for i in range(12):
        month = (first_month + i - 1) % 12 + 1
        year = start_year + ((first_month + i - 1) // 12)

        start = date(year, month, 1)
        # End of month
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)

        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]

        periods.append({
            "period_number": i + 1,
            "period_name": f"P{i + 1} - {month_names[month - 1]} {year}",
            "start_date": start,
            "end_date": end,
        })

    return periods


# -- Period status management --------------------------------------------------


def get_period_status(conn, tenant_id: str, fiscal_year: int, fiscal_period: int) -> str:
    """Get the status of a fiscal period. Returns 'open' if no record exists."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT status FROM semantic.period_status
            WHERE tenant_id = %s AND fiscal_year = %s AND fiscal_period = %s
            """,
            (tenant_id, fiscal_year, fiscal_period),
        )
        row = cur.fetchone()
        return row[0] if row else "open"


def set_period_status(
    conn, tenant_id: str, fiscal_year: int, fiscal_period: int,
    status: str, actor: str | None = None,
) -> None:
    """Set the status of a fiscal period."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO semantic.period_status
                (tenant_id, fiscal_year, fiscal_period, status, closed_by, closed_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, entity_id, fiscal_year, fiscal_period)
            DO UPDATE SET status = %s, closed_by = %s, closed_at = %s
            """,
            (tenant_id, fiscal_year, fiscal_period, status, actor, now,
             status, actor, now),
        )
    conn.commit()
    log.info("period_status: FY%d P%d → %s (by %s)", fiscal_year, fiscal_period, status, actor)

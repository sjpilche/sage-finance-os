"""Tests for app.semantic.period_engine."""

from datetime import date

from app.semantic.period_engine import (
    generate_fiscal_calendar,
    get_fiscal_period,
    get_fiscal_year,
)


def test_calendar_year():
    assert get_fiscal_year(date(2026, 3, 15), 12) == 2026
    assert get_fiscal_year(date(2026, 12, 31), 12) == 2026
    assert get_fiscal_year(date(2026, 1, 1), 12) == 2026


def test_june_year_end():
    assert get_fiscal_year(date(2026, 6, 30), 6) == 2026
    assert get_fiscal_year(date(2026, 7, 1), 6) == 2027
    assert get_fiscal_year(date(2026, 1, 15), 6) == 2026


def test_calendar_year_periods():
    assert get_fiscal_period(date(2026, 1, 15), 12) == 1
    assert get_fiscal_period(date(2026, 6, 15), 12) == 6
    assert get_fiscal_period(date(2026, 12, 15), 12) == 12


def test_june_year_end_periods():
    assert get_fiscal_period(date(2026, 7, 15), 6) == 1   # July = P1
    assert get_fiscal_period(date(2026, 12, 15), 6) == 6   # December = P6
    assert get_fiscal_period(date(2027, 6, 15), 6) == 12   # June = P12


def test_generate_calendar_year():
    cal = generate_fiscal_calendar(2026, 12)
    assert len(cal) == 12
    assert cal[0]["period_number"] == 1
    assert cal[0]["start_date"] == date(2026, 1, 1)
    assert cal[0]["end_date"] == date(2026, 1, 31)
    assert cal[11]["period_number"] == 12
    assert cal[11]["start_date"] == date(2026, 12, 1)
    assert cal[11]["end_date"] == date(2026, 12, 31)


def test_generate_june_year_end():
    cal = generate_fiscal_calendar(2027, 6)
    assert len(cal) == 12
    assert cal[0]["period_number"] == 1
    assert cal[0]["start_date"] == date(2026, 7, 1)  # FY2027 starts July 2026
    assert cal[11]["end_date"] == date(2027, 6, 30)

"""Tests for app.trust.circuit_breaker — quarantine decision logic."""

from app.trust.circuit_breaker import should_quarantine, QUARANTINE_PASS_RATE


def test_should_quarantine_on_critical_failures():
    dq = {"critical_failures": 1, "pass_rate": 0.95}
    assert should_quarantine(dq) is True


def test_should_quarantine_on_low_pass_rate():
    dq = {"critical_failures": 0, "pass_rate": 0.85}
    assert should_quarantine(dq) is True


def test_should_not_quarantine_on_good_results():
    dq = {"critical_failures": 0, "pass_rate": 0.95}
    assert should_quarantine(dq) is False


def test_should_quarantine_at_exact_threshold():
    """Pass rate exactly at threshold should NOT quarantine (< not <=)."""
    dq = {"critical_failures": 0, "pass_rate": QUARANTINE_PASS_RATE}
    assert should_quarantine(dq) is False


def test_should_quarantine_just_below_threshold():
    dq = {"critical_failures": 0, "pass_rate": QUARANTINE_PASS_RATE - 0.001}
    assert should_quarantine(dq) is True


def test_should_quarantine_with_both_triggers():
    dq = {"critical_failures": 3, "pass_rate": 0.50}
    assert should_quarantine(dq) is True


def test_should_not_quarantine_missing_pass_rate():
    """If pass_rate is None, only critical_failures matters."""
    dq = {"critical_failures": 0, "pass_rate": None}
    assert should_quarantine(dq) is False


def test_should_not_quarantine_empty_summary():
    dq = {}
    assert should_quarantine(dq) is False


def test_quarantine_pass_rate_constant():
    """Verify the threshold is 90%."""
    assert QUARANTINE_PASS_RATE == 0.90

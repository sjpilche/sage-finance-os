"""Tests for app.quality.gate — quality gate orchestrator."""

from unittest.mock import MagicMock, patch

from app.quality.gate import run_quality_gate


def _make_dq_summary(pass_rate=1.0, critical_failures=0, total=5, passed=5):
    return {
        "results": {
            "gl_entry": [
                {"check_name": f"check_{i}", "severity": "critical", "passed": True}
                for i in range(passed)
            ] + [
                {"check_name": f"check_fail_{i}", "severity": "critical", "passed": False}
                for i in range(total - passed)
            ],
        },
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "critical_failures": critical_failures,
        "pass_rate": pass_rate,
    }


@patch("app.quality.gate.persist_certificate")
@patch("app.quality.gate.persist_scorecard")
@patch("app.quality.gate.run_all_checks")
def test_gate_certifies_on_perfect_results(mock_checks, mock_persist_sc, mock_persist_cert):
    mock_checks.return_value = _make_dq_summary()
    conn = MagicMock()

    result = run_quality_gate(conn, "t1", "r1", {"gl_entry": 100})

    assert result["outcome"] in ("certified", "conditional")
    assert "scorecard" in result
    assert result["scorecard"]["composite_score"] == 100.0
    mock_persist_sc.assert_called_once()
    mock_persist_cert.assert_called_once()


@patch("app.quality.gate.quarantine_run")
@patch("app.quality.gate.persist_scorecard")
@patch("app.quality.gate.run_all_checks")
def test_gate_quarantines_on_critical_failures(mock_checks, mock_persist_sc, mock_quarantine):
    mock_checks.return_value = _make_dq_summary(pass_rate=0.5, critical_failures=2, total=4, passed=2)
    mock_quarantine.return_value = {"run_id": "r1", "reason": "test", "quarantined_at": "now"}
    conn = MagicMock()

    result = run_quality_gate(conn, "t1", "r1", {"gl_entry": 100})

    assert result["outcome"] == "quarantined"
    assert "quarantine" in result
    mock_quarantine.assert_called_once()


@patch("app.quality.gate.persist_certificate")
@patch("app.quality.gate.persist_scorecard")
@patch("app.quality.gate.run_all_checks")
def test_gate_returns_dq_summary(mock_checks, mock_persist_sc, mock_persist_cert):
    dq = _make_dq_summary()
    mock_checks.return_value = dq
    conn = MagicMock()

    result = run_quality_gate(conn, "t1", "r1", {"gl_entry": 100})

    assert result["dq_summary"]["total"] == 5
    assert result["dq_summary"]["passed"] == 5
    assert result["dq_summary"]["pass_rate"] == 1.0


@patch("app.quality.gate.persist_certificate")
@patch("app.quality.gate.persist_scorecard")
@patch("app.quality.gate.run_all_checks")
def test_gate_returns_scorecard_dimensions(mock_checks, mock_persist_sc, mock_persist_cert):
    mock_checks.return_value = _make_dq_summary()
    conn = MagicMock()

    result = run_quality_gate(conn, "t1", "r1", {"gl_entry": 100})

    dims = result["scorecard"]["dimensions"]
    assert "accuracy" in dims
    assert "completeness" in dims
    assert "consistency" in dims
    assert "validity" in dims
    assert "uniqueness" in dims
    assert "timeliness" in dims

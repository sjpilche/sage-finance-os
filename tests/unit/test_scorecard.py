"""Tests for app.trust.scorecard — 6-dimension quality scorecard."""

from app.trust.scorecard import compute_scorecard, WEIGHTS


def _make_dq(critical_passed=3, critical_total=3, warning_passed=2, warning_total=2):
    """Helper to build a mock DQ summary."""
    results = {
        "gl_entry": [
            *[{"check_name": f"critical_{i}", "severity": "critical", "passed": i < critical_passed}
              for i in range(critical_total)],
            *[{"check_name": f"warning_{i}", "severity": "warning", "passed": i < warning_passed}
              for i in range(warning_total)],
        ],
    }
    total = critical_total + warning_total
    passed = critical_passed + warning_passed
    return {
        "results": results,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "critical_failures": critical_total - critical_passed,
        "pass_rate": passed / total if total > 0 else 1.0,
    }


def test_perfect_scorecard():
    dq = _make_dq(3, 3, 2, 2)
    sc = compute_scorecard("run-1", "tenant-1", dq, {"gl_entry": 1000})
    assert sc.composite_score == 100.0
    assert sc.verdict == "CERTIFIED"
    assert sc.gate_passed is True


def test_failed_accuracy_blocks_certification():
    dq = _make_dq(critical_passed=2, critical_total=3)  # 66.7% accuracy
    sc = compute_scorecard("run-2", "tenant-1", dq)
    assert sc.dimensions["accuracy"].raw_score < 100.0
    assert sc.verdict == "FAILED"
    assert sc.gate_passed is False


def test_conditional_verdict():
    """High composite but accuracy < 100% → CONDITIONAL."""
    dq = _make_dq(critical_passed=9, critical_total=10, warning_passed=5, warning_total=5)
    sc = compute_scorecard("run-3", "tenant-1", dq)
    # accuracy = 90% → composite could still be >= 98 depending on other dims
    # but accuracy < 100 → verdict should NOT be CERTIFIED
    assert sc.verdict in ("CONDITIONAL", "FAILED")
    assert sc.gate_passed is False


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001


def test_evidence_hash_deterministic():
    dq = _make_dq()
    sc1 = compute_scorecard("run-x", "tenant-1", dq)
    sc2 = compute_scorecard("run-x", "tenant-1", dq)
    assert sc1.evidence_hash == sc2.evidence_hash


def test_to_dict():
    dq = _make_dq()
    sc = compute_scorecard("run-d", "tenant-1", dq)
    d = sc.to_dict()
    assert "composite_score" in d
    assert "dimensions" in d
    assert "computed_at" in d

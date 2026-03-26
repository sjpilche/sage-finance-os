"""Tests for app.trust.envelope — TrustEnvelope dataclass."""

import pytest

from app.trust.envelope import ConfidenceLevel, TrustEnvelope


def test_high_confidence():
    te = TrustEnvelope(source="sage_intacct", confidence=0.95)
    assert te.confidence_level == "high"
    assert te.review_required is False


def test_low_confidence_triggers_review():
    te = TrustEnvelope(source="computed", confidence=0.55)
    assert te.confidence_level == "low"
    assert te.review_required is True
    assert te.review_reason == "low_confidence"


def test_critical_confidence():
    te = TrustEnvelope(source="model", confidence=0.30)
    assert te.confidence_level == "critical"
    assert te.review_required is True


def test_high_risk_triggers_review():
    te = TrustEnvelope(source="sage_intacct", confidence=0.90, risk_level="high")
    assert te.review_required is True
    assert te.review_reason == "high_risk"


def test_invalid_confidence_raises():
    with pytest.raises(ValueError, match="0.0–1.0"):
        TrustEnvelope(source="test", confidence=1.5)


def test_to_dict():
    te = TrustEnvelope(source="sage_intacct", confidence=0.88, scorecard_score=99.2)
    d = te.to_dict()
    assert d["source"] == "sage_intacct"
    assert d["confidence"] == 0.88
    assert d["scorecard_score"] == 99.2
    assert d["confidence_level"] == "high"
    assert "timestamp" in d


def test_confidence_level_boundaries():
    assert ConfidenceLevel.from_score(0.50) == "critical"
    assert ConfidenceLevel.from_score(0.51) == "low"
    assert ConfidenceLevel.from_score(0.69) == "low"
    assert ConfidenceLevel.from_score(0.70) == "medium"
    assert ConfidenceLevel.from_score(0.84) == "medium"
    assert ConfidenceLevel.from_score(0.85) == "high"

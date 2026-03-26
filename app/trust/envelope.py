"""
Trust Envelope — lightweight metadata attached to API responses.

Adapted from Jake's shared/trust_envelope.py. Slimmed down: removed
agent-specific fields, kept confidence/risk/magnitude/sources.

Attach to any API response to communicate data provenance and trust:

    from app.trust.envelope import TrustEnvelope

    te = TrustEnvelope(
        source="sage_intacct",
        confidence=0.97,
        risk_level="low",
        certified_at="2026-03-25T04:30:00Z",
        scorecard_score=99.2,
    )
    return {"data": result, "trust": te.to_dict()}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class ConfidenceLevel:
    CRITICAL = "critical"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @staticmethod
    def from_score(score: float) -> str:
        if score < 0.51:
            return "critical"
        if score < 0.70:
            return "low"
        if score < 0.85:
            return "medium"
        return "high"


@dataclass
class TrustEnvelope:
    """Trust metadata for a data response."""

    source: str                         # e.g. "sage_intacct", "computed", "manual"
    confidence: float                   # 0.0–1.0
    risk_level: str = "low"             # low | medium | high | critical
    financial_magnitude: float | None = None
    certified_at: str | None = None     # ISO timestamp of last certification
    scorecard_score: float | None = None
    is_stale: bool = False
    refreshed_at: str | None = None
    data_sources: list[str] = field(default_factory=list)
    review_required: bool = False
    review_reason: str = ""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")
        # Auto-flag for review if confidence is low or risk is high
        if self.confidence < 0.70:
            self.review_required = True
            self.review_reason = self.review_reason or "low_confidence"
        if self.risk_level in ("high", "critical"):
            self.review_required = True
            self.review_reason = self.review_reason or "high_risk"

    @property
    def confidence_level(self) -> str:
        return ConfidenceLevel.from_score(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "risk_level": self.risk_level,
            "financial_magnitude": self.financial_magnitude,
            "certified_at": self.certified_at,
            "scorecard_score": self.scorecard_score,
            "is_stale": self.is_stale,
            "refreshed_at": self.refreshed_at,
            "data_sources": self.data_sources,
            "review_required": self.review_required,
            "review_reason": self.review_reason,
            "timestamp": self.timestamp,
        }

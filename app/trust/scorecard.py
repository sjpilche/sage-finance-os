"""
trust.scorecard
===============
6-dimension weighted Data Health Scorecard engine.

Adapted from DataClean's certification/scorecard.py.
Removed tenant threshold lookups (use module-level defaults for V1).

Dimension weights:
  Accuracy       35%  — quality gate pass rate (critical checks)
  Completeness   20%  — field-level non-null rates
  Consistency    15%  — reconciliation FK + enum checks
  Validity       10%  — quality gate format/range/type checks
  Uniqueness     10%  — 1 - (duplicates / total rows)
  Timeliness     10%  — staleness penalty based on source age

Gate logic:
  composite >= 98.0 AND accuracy_raw == 100.0 → CERTIFIED
  composite >= 98.0 AND accuracy_raw  < 100.0 → CONDITIONAL
  otherwise                                   → FAILED
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

log = logging.getLogger(__name__)

WEIGHTS: dict[str, float] = {
    "accuracy": 0.35,
    "completeness": 0.20,
    "consistency": 0.15,
    "validity": 0.10,
    "uniqueness": 0.10,
    "timeliness": 0.10,
}

COMPOSITE_THRESHOLD = 98.0
ACCURACY_GATE = 100.0


@dataclass
class DimensionScore:
    name: str
    weight: float
    raw_score: float
    weighted_score: float
    details: dict = field(default_factory=dict)


@dataclass
class ScoreCard:
    run_id: str
    tenant_id: str
    composite_score: float
    dimensions: dict[str, DimensionScore]
    gate_passed: bool
    verdict: str  # "CERTIFIED" | "CONDITIONAL" | "FAILED"
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_hash: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["computed_at"] = self.computed_at.isoformat()
        return d


# -- Dimension calculators -----------------------------------------------------


def _calc_accuracy(dq_summary: dict) -> DimensionScore:
    """Accuracy = % of critical quality checks that passed."""
    results_by_obj = dq_summary.get("results", {})
    critical_total = 0
    critical_passed = 0

    for obj_results in results_by_obj.values():
        for r in obj_results:
            if r.get("severity") == "critical":
                critical_total += 1
                if r.get("passed"):
                    critical_passed += 1

    if critical_total == 0:
        raw = (dq_summary.get("pass_rate") or 1.0) * 100
    else:
        raw = (critical_passed / critical_total) * 100

    return DimensionScore(
        name="accuracy", weight=WEIGHTS["accuracy"],
        raw_score=round(raw, 2), weighted_score=round(raw * WEIGHTS["accuracy"], 2),
        details={"critical_total": critical_total, "critical_passed": critical_passed},
    )


def _calc_completeness(dq_summary: dict) -> DimensionScore:
    """Completeness = average non-null rate across completeness checks."""
    results_by_obj = dq_summary.get("results", {})
    completeness_scores = []

    for obj_results in results_by_obj.values():
        for r in obj_results:
            if "completeness" in r.get("check_name", "").lower():
                completeness_scores.append(100.0 if r.get("passed") else 0.0)

    raw = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 100.0

    return DimensionScore(
        name="completeness", weight=WEIGHTS["completeness"],
        raw_score=round(raw, 2), weighted_score=round(raw * WEIGHTS["completeness"], 2),
        details={"checks_count": len(completeness_scores)},
    )


def _calc_consistency(dq_summary: dict) -> DimensionScore:
    """Consistency = pass rate across FK and enum checks."""
    results_by_obj = dq_summary.get("results", {})
    total = 0
    passed = 0

    for obj_results in results_by_obj.values():
        for r in obj_results:
            name = r.get("check_name", "").lower()
            if any(kw in name for kw in ("fk", "foreign_key", "enum", "valid_values")):
                total += 1
                if r.get("passed"):
                    passed += 1

    raw = (passed / total * 100) if total > 0 else 100.0

    return DimensionScore(
        name="consistency", weight=WEIGHTS["consistency"],
        raw_score=round(raw, 2), weighted_score=round(raw * WEIGHTS["consistency"], 2),
        details={"total": total, "passed": passed},
    )


def _calc_validity(dq_summary: dict) -> DimensionScore:
    """Validity = % of non-critical (warning) quality checks that passed."""
    results_by_obj = dq_summary.get("results", {})
    warning_total = 0
    warning_passed = 0

    for obj_results in results_by_obj.values():
        for r in obj_results:
            if r.get("severity") != "critical":
                warning_total += 1
                if r.get("passed"):
                    warning_passed += 1

    raw = (warning_passed / warning_total * 100) if warning_total > 0 else 100.0

    return DimensionScore(
        name="validity", weight=WEIGHTS["validity"],
        raw_score=round(raw, 2), weighted_score=round(raw * WEIGHTS["validity"], 2),
        details={"warning_total": warning_total, "warning_passed": warning_passed},
    )


def _calc_uniqueness(write_counts: dict | None) -> DimensionScore:
    """Uniqueness — defaults to 100% (dedup not yet wired in Phase 3)."""
    return DimensionScore(
        name="uniqueness", weight=WEIGHTS["uniqueness"],
        raw_score=100.0, weighted_score=round(100.0 * WEIGHTS["uniqueness"], 2),
        details={"note": "dedup not yet computed"},
    )


def _calc_timeliness(run_started_at: datetime | None = None) -> DimensionScore:
    """Timeliness = penalty based on data staleness."""
    now = datetime.now(timezone.utc)

    if run_started_at:
        age_hours = max(0, (now - run_started_at).total_seconds() / 3600)
    else:
        age_hours = 0

    if age_hours <= 1:
        raw = 100.0
    elif age_hours <= 24:
        raw = 100 - (age_hours - 1) * (20 / 23)
    else:
        days_over = min((age_hours - 24) / 24, 6)
        raw = max(80 - days_over * 5, 50.0)

    return DimensionScore(
        name="timeliness", weight=WEIGHTS["timeliness"],
        raw_score=round(raw, 2), weighted_score=round(raw * WEIGHTS["timeliness"], 2),
        details={"age_hours": round(age_hours, 2)},
    )


# -- Public API ----------------------------------------------------------------


def compute_scorecard(
    run_id: str,
    tenant_id: str,
    dq_summary: dict,
    write_counts: dict | None = None,
    run_started_at: datetime | None = None,
) -> ScoreCard:
    """Compute the 6-dimension Data Health Scorecard for a pipeline run."""
    dimensions: dict[str, DimensionScore] = {
        "accuracy": _calc_accuracy(dq_summary),
        "completeness": _calc_completeness(dq_summary),
        "consistency": _calc_consistency(dq_summary),
        "validity": _calc_validity(dq_summary),
        "uniqueness": _calc_uniqueness(write_counts),
        "timeliness": _calc_timeliness(run_started_at),
    }

    composite = round(min(sum(d.weighted_score for d in dimensions.values()), 100.0), 2)
    accuracy_raw = dimensions["accuracy"].raw_score

    if composite >= COMPOSITE_THRESHOLD and accuracy_raw >= ACCURACY_GATE:
        verdict = "CERTIFIED"
        gate_passed = True
    elif composite >= COMPOSITE_THRESHOLD:
        verdict = "CONDITIONAL"
        gate_passed = False
    else:
        verdict = "FAILED"
        gate_passed = False

    evidence_hash = hashlib.sha256(json.dumps(
        {"run_id": run_id, "composite": composite, "pass_rate": dq_summary.get("pass_rate")},
        sort_keys=True,
    ).encode()).hexdigest()

    sc = ScoreCard(
        run_id=run_id, tenant_id=tenant_id,
        composite_score=composite, dimensions=dimensions,
        gate_passed=gate_passed, verdict=verdict, evidence_hash=evidence_hash,
    )

    log.info("scorecard: run=%s composite=%.2f verdict=%s accuracy=%.1f",
             run_id, composite, verdict, accuracy_raw)
    return sc


def persist_scorecard(conn, scorecard: ScoreCard) -> None:
    """Write the scorecard to audit.scorecard_results."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit.scorecard_results
                (run_id, tenant_id, accuracy, completeness, consistency,
                 validity, uniqueness, timeliness, composite, gate_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                scorecard.run_id, scorecard.tenant_id,
                scorecard.dimensions["accuracy"].raw_score,
                scorecard.dimensions["completeness"].raw_score,
                scorecard.dimensions["consistency"].raw_score,
                scorecard.dimensions["validity"].raw_score,
                scorecard.dimensions["uniqueness"].raw_score,
                scorecard.dimensions["timeliness"].raw_score,
                scorecard.composite_score,
                scorecard.verdict.lower(),
            ),
        )
    conn.commit()
    log.info("persist_scorecard: run=%s verdict=%s", scorecard.run_id, scorecard.verdict)

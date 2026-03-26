"""
quality.gate
============
Quality gate orchestrator — runs checks, computes scorecard, issues
certificate or quarantines the run.

This is the single entry point for the entire quality layer:
    result = run_quality_gate(conn, tenant_id, run_id, write_counts, run_started_at)
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.quality.checks import run_all_checks
from app.trust.certificate import generate_certificate, persist_certificate
from app.trust.circuit_breaker import quarantine_run, should_quarantine
from app.trust.scorecard import compute_scorecard, persist_scorecard

log = logging.getLogger(__name__)


def run_quality_gate(
    conn,
    tenant_id: str,
    run_id: str,
    write_counts: dict[str, int],
    run_started_at: datetime | None = None,
) -> dict:
    """
    Run the full quality gate: checks → scorecard → certificate/quarantine.

    Parameters
    ----------
    conn:            psycopg2 connection (sync).
    tenant_id:       Tenant UUID.
    run_id:          Pipeline run UUID.
    write_counts:    {object_name: row_count} from contract writers.
    run_started_at:  When the pipeline run started (for timeliness).

    Returns
    -------
    dict with: dq_summary, scorecard, certificate (if certified), quarantine (if quarantined).
    """
    # Step 1: Run SQL quality checks
    dq_summary = run_all_checks(conn, tenant_id, run_id, write_counts)

    # Step 2: Compute scorecard
    scorecard = compute_scorecard(
        run_id=run_id,
        tenant_id=tenant_id,
        dq_summary=dq_summary,
        write_counts=write_counts,
        run_started_at=run_started_at,
    )
    persist_scorecard(conn, scorecard)

    result = {
        "dq_summary": {
            "total": dq_summary["total"],
            "passed": dq_summary["passed"],
            "failed": dq_summary["failed"],
            "critical_failures": dq_summary["critical_failures"],
            "pass_rate": dq_summary["pass_rate"],
        },
        "scorecard": {
            "composite_score": scorecard.composite_score,
            "verdict": scorecard.verdict,
            "gate_passed": scorecard.gate_passed,
            "dimensions": {
                name: {"raw": dim.raw_score, "weighted": dim.weighted_score}
                for name, dim in scorecard.dimensions.items()
            },
        },
    }

    # Step 3: Certificate or quarantine
    if should_quarantine(dq_summary):
        q = quarantine_run(conn, run_id, tenant_id, {
            **dq_summary,
            "composite_score": scorecard.composite_score,
        })
        result["quarantine"] = q
        result["outcome"] = "quarantined"
        log.warning("quality_gate: run=%s QUARANTINED — %s", run_id, q["reason"])
    else:
        cert = generate_certificate(scorecard)
        persist_certificate(conn, cert)
        result["certificate"] = {
            "certificate_id": cert.certificate_id,
            "verdict": cert.verdict,
            "signature": cert.signature[:16] + "...",
        }
        result["outcome"] = "certified" if scorecard.gate_passed else "conditional"
        log.info("quality_gate: run=%s %s (score=%.1f)",
                 run_id, result["outcome"].upper(), scorecard.composite_score)

    return result

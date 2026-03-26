"""
trust.circuit_breaker
=====================
Quality gate that quarantines non-compliant data.

Adapted from DataClean's certification/circuit_breaker.py.
Simplified: removed tenant threshold lookups (uses module defaults).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

log = logging.getLogger(__name__)

QUARANTINE_PASS_RATE = 0.90  # quarantine if pass_rate below this


def should_quarantine(dq_summary: dict) -> bool:
    """
    Determine if a run should be quarantined.

    Triggers:
      - Any critical failures
      - Pass rate below 90%
    """
    if dq_summary.get("critical_failures", 0) > 0:
        return True
    pass_rate = dq_summary.get("pass_rate")
    if pass_rate is not None and pass_rate < QUARANTINE_PASS_RATE:
        return True
    return False


def quarantine_run(conn, run_id: str, tenant_id: str, dq_summary: dict, reason: str | None = None) -> dict:
    """Quarantine a pipeline run — log to audit.quarantine_log, update run status."""
    now = datetime.now(timezone.utc)

    if reason is None:
        parts = []
        critical = dq_summary.get("critical_failures", 0)
        pass_rate = dq_summary.get("pass_rate")
        if critical > 0:
            parts.append(f"{critical} critical quality failure(s)")
        if pass_rate is not None and pass_rate < QUARANTINE_PASS_RATE:
            parts.append(f"pass rate {pass_rate:.1%} below {QUARANTINE_PASS_RATE:.0%} threshold")
        reason = "; ".join(parts) or "quality gate did not pass"

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit.quarantine_log (run_id, tenant_id, reason, scorecard_score)
            VALUES (%s, %s, %s, %s)
            """,
            (run_id, tenant_id, reason, dq_summary.get("composite_score")),
        )
        cur.execute(
            "UPDATE platform.data_runs SET status = 'quarantined', completed_at = %s WHERE run_id = %s",
            (now, run_id),
        )
    conn.commit()

    log.warning("quarantine: run=%s reason=%s", run_id, reason)
    return {"run_id": run_id, "reason": reason, "quarantined_at": now.isoformat()}


def release_quarantine(conn, run_id: str, tenant_id: str, approver: str, reason: str) -> dict:
    """Manually release a quarantined run — requires approver + reason."""
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE audit.quarantine_log
            SET resolved_at = %s, resolved_by = %s, resolution_note = %s
            WHERE run_id = %s AND tenant_id = %s AND resolved_at IS NULL
            """,
            (now, approver, reason, run_id, tenant_id),
        )
        if cur.rowcount == 0:
            return {"released": False, "reason": "no active quarantine found"}

        cur.execute(
            "UPDATE platform.data_runs SET status = 'complete' WHERE run_id = %s",
            (run_id,),
        )
    conn.commit()

    log.info("quarantine_released: run=%s approver=%s", run_id, approver)
    return {"released": True, "run_id": run_id, "approver": approver, "released_at": now.isoformat()}


def is_quarantined(conn, run_id: str, tenant_id: str) -> bool:
    """Check if a run is currently quarantined."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM audit.quarantine_log WHERE run_id = %s AND tenant_id = %s AND resolved_at IS NULL LIMIT 1",
            (run_id, tenant_id),
        )
        return cur.fetchone() is not None

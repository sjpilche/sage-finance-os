"""
pipeline.runner
===============
Main pipeline orchestrator for Sage Finance OS.

Threads a RunContext through every step, updates run status at each
transition, and always completes or fails — even on unexpected exceptions.

Pipeline sequence (connector-first, no file upload):
1. Extract from Sage Intacct connector (per object)
2. Write transformed records to contract tables
3. Update watermarks
4. Complete run with summary

Unlike DataClean's file-based pipeline, this extracts directly from the
connector and writes to contract tables without intermediate staging.
Staging (raw_records) will be added in a future phase for full auditability.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.core.tenant import (
    RunContext,
    complete_run,
    create_run,
    fail_run,
    update_run_status,
)
from app.contract.writer import OBJECT_WRITERS, write_all
from app.ingestion.connectors.sage_intacct import SageIntacctConnector
from app.ingestion.connectors.sage_intacct.objects import OBJECT_CATALOG, OBJECT_TO_CANONICAL

log = logging.getLogger(__name__)


def run_pipeline(
    conn,
    tenant_id: str,
    connection_id: str | None = None,
    credentials: dict | None = None,
    objects: list[str] | None = None,
    mode: str = "full",
) -> dict:
    """
    Execute the full extraction → write pipeline for a single run.

    Parameters
    ----------
    conn:           psycopg2 connection (sync, from db_sync pool).
    tenant_id:      UUID of the owning tenant.
    connection_id:  UUID of the Sage Intacct connection.
    credentials:    Sage Intacct credentials dict.
    objects:        List of Intacct object names to extract (None = all).
    mode:           "full" or "incremental".

    Returns
    -------
    dict with run_id, status, summary.
    """
    # Create run context
    ctx = create_run(conn, tenant_id, "sage_intacct", connection_id, mode)
    start = time.monotonic()

    try:
        # Phase: Extracting
        update_run_status(conn, ctx.run_id, "extracting")

        connector = SageIntacctConnector(config=credentials)
        target_objects = objects or list(OBJECT_CATALOG.keys())

        # Extract and accumulate records per canonical object
        extracted: dict[str, list[dict]] = {}
        extract_counts: dict[str, int] = {}

        for obj_name in target_objects:
            if obj_name not in OBJECT_CATALOG:
                log.warning("pipeline: skipping unknown object %s", obj_name)
                continue

            canonical = OBJECT_TO_CANONICAL[obj_name]
            watermark = _get_watermark(conn, tenant_id, connection_id, obj_name) if mode == "incremental" else None

            obj_records: list[dict] = []
            for batch in connector.extract(obj_name, watermark=watermark, batch_size=1000):
                obj_records.extend(batch)

            extracted[canonical] = obj_records
            extract_counts[obj_name] = len(obj_records)
            log.info("pipeline: extracted %s → %d records (%s)",
                     obj_name, len(obj_records), canonical)

        # Phase: Staging (writing to contract tables)
        update_run_status(conn, ctx.run_id, "staging")

        write_counts = write_all(conn, tenant_id, ctx.run_id, extracted)

        # Update watermarks for incremental sync
        for obj_name in target_objects:
            if obj_name in OBJECT_CATALOG and OBJECT_CATALOG[obj_name].watermark_field:
                _update_watermark(conn, tenant_id, connection_id, obj_name)

        # Phase: Validating (quality gate)
        update_run_status(conn, ctx.run_id, "validating")

        from app.quality.gate import run_quality_gate

        quality_result = run_quality_gate(
            conn, tenant_id, ctx.run_id, write_counts,
            run_started_at=ctx.started_at,
        )

        # If quarantined, the circuit breaker already updated run status
        if quality_result.get("outcome") == "quarantined":
            elapsed = round(time.monotonic() - start, 1)
            return {
                "run_id": ctx.run_id,
                "status": "quarantined",
                "summary": {
                    "extracted": extract_counts,
                    "written": write_counts,
                    "quality": quality_result,
                    "elapsed_seconds": elapsed,
                },
            }

        # Phase: KPI Materialization
        kpi_result = _materialize_kpis(conn, tenant_id, ctx.run_id)

        # Complete
        elapsed = round(time.monotonic() - start, 1)
        summary = {
            "extracted": extract_counts,
            "written": write_counts,
            "quality": quality_result,
            "kpis": kpi_result,
            "elapsed_seconds": elapsed,
            "objects": target_objects,
            "mode": mode,
        }

        complete_run(conn, ctx.run_id, summary)

        log.info("pipeline: run %s complete in %.1fs — %s", ctx.run_id, elapsed, write_counts)

        return {
            "run_id": ctx.run_id,
            "status": "complete",
            "summary": summary,
        }

    except Exception as e:
        elapsed = round(time.monotonic() - start, 1)
        log.error("pipeline: run %s failed after %.1fs — %s", ctx.run_id, elapsed, e)
        try:
            fail_run(conn, ctx.run_id, str(e))
        except Exception:
            log.error("pipeline: failed to mark run as failed", exc_info=True)

        return {
            "run_id": ctx.run_id,
            "status": "failed",
            "error": str(e),
            "elapsed_seconds": elapsed,
        }


def _materialize_kpis(conn, tenant_id: str, run_id: str) -> dict:
    """Compute and materialize KPIs after a successful pipeline run."""
    try:
        from app.semantic.kpi_engine import compute_all_kpis

        now = datetime.now(timezone.utc)
        fiscal_year = now.year
        fiscal_period = now.month

        results = compute_all_kpis(
            conn=conn,
            tenant_id=tenant_id,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            run_id=run_id,
        )

        computed = sum(1 for v in results.values() if v is not None)
        log.info("pipeline: materialized %d/%d KPIs", computed, len(results))

        return {"computed": computed, "total": len(results), "fiscal_year": fiscal_year, "fiscal_period": fiscal_period}

    except Exception as e:
        log.warning("pipeline: KPI materialization failed — %s", e)
        return {"error": str(e)}


def _get_watermark(conn, tenant_id: str, connection_id: str | None, object_name: str) -> str | None:
    """Get the last watermark value for incremental sync."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT last_value FROM platform.watermarks
                WHERE tenant_id = %s AND object_name = %s
                  AND (connection_id = %s OR connection_id IS NULL)
                ORDER BY last_sync_at DESC NULLS LAST
                LIMIT 1
                """,
                (tenant_id, object_name, connection_id),
            )
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None


def _update_watermark(conn, tenant_id: str, connection_id: str | None, object_name: str) -> None:
    """Update the watermark to current timestamp after successful extraction."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO platform.watermarks (tenant_id, connection_id, object_name, last_value, last_sync_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (tenant_id, connection_id, object_name)
                DO UPDATE SET last_value = %s, last_sync_at = now()
                """,
                (tenant_id, connection_id, object_name, now, now),
            )
        conn.commit()
    except Exception:
        log.warning("pipeline: failed to update watermark for %s", object_name, exc_info=True)

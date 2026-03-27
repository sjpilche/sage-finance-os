"""
workflows.scheduler
===================
APScheduler wrapper for automated sync and maintenance jobs.

Adapted from Jake's shared/scheduler_registry.py — simplified.
Manages scheduled jobs for:
  - Incremental Sage Intacct sync (every 4 hours)
  - Data freshness checks (every 30 minutes)
  - Stale run cleanup (daily)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

_scheduler = None


def get_scheduler():
    """Lazy-init and return the APScheduler instance."""
    global _scheduler
    if _scheduler is None:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            _scheduler = AsyncIOScheduler()
            log.info("scheduler: initialized")
        except ImportError:
            log.warning("scheduler: apscheduler not installed — scheduled jobs disabled")
            return None
    return _scheduler


def start_scheduler() -> None:
    """Start the scheduler if not already running."""
    s = get_scheduler()
    if s and not s.running:
        s.start()
        log.info("scheduler: started with %d jobs", len(s.get_jobs()))


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
        log.info("scheduler: stopped")
    _scheduler = None


def register_default_jobs() -> None:
    """Register the default set of scheduled jobs."""
    s = get_scheduler()
    if s is None:
        return

    # Data freshness check — every 30 minutes
    s.add_job(
        _job_freshness_check,
        "interval", minutes=30,
        id="freshness_check",
        replace_existing=True,
        name="Data Freshness Check",
    )

    # Stale run cleanup — daily at 03:00 UTC
    s.add_job(
        _job_stale_run_cleanup,
        "cron", hour=3, minute=0,
        id="stale_run_cleanup",
        replace_existing=True,
        name="Stale Run Cleanup",
    )

    # Scheduled incremental sync — every 4 hours
    s.add_job(
        _job_incremental_sync,
        "interval", hours=4,
        id="incremental_sync",
        replace_existing=True,
        name="Incremental Sage Intacct Sync",
    )

    log.info("scheduler: registered %d default jobs", len(s.get_jobs()))


def get_job_status() -> list[dict]:
    """Return status of all scheduled jobs."""
    s = get_scheduler()
    if s is None:
        return []

    return [
        {
            "job_id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }
        for job in s.get_jobs()
    ]


# -- Job implementations ------------------------------------------------------


async def _job_freshness_check() -> None:
    """Check data freshness and emit alert if stale."""
    from app.core.db import get_pool

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT MAX(completed_at) AS last_sync,
                       EXTRACT(EPOCH FROM (now() - MAX(completed_at))) / 3600 AS hours_since
                FROM platform.data_runs
                WHERE status = 'complete'
                """
            )

            if row and row["hours_since"] and row["hours_since"] > 8:
                log.warning(
                    "scheduler: data stale — last sync %.1f hours ago",
                    row["hours_since"],
                )
                from app.workflows.event_bus import emit
                await emit("alert.data_stale", {
                    "hours_since_sync": round(row["hours_since"], 1),
                    "last_sync": row["last_sync"].isoformat() if row["last_sync"] else None,
                }, source="scheduler", conn=conn)

    except Exception as e:
        log.error("scheduler: freshness check failed — %s", e)


async def _job_incremental_sync() -> None:
    """Run incremental sync for all active connections."""
    from app.core.db import get_pool

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Get all active connections
            rows = await conn.fetch(
                "SELECT connection_id, credentials FROM platform.connections WHERE status = 'active'"
            )

            if not rows:
                log.info("scheduler: no active connections — skipping incremental sync")
                return

            # Get default tenant
            tenant_row = await conn.fetchrow(
                "SELECT tenant_id FROM platform.tenants WHERE slug = 'default'"
            )
            if not tenant_row:
                log.warning("scheduler: no default tenant — skipping sync")
                return

            tenant_id = str(tenant_row["tenant_id"])

        # Run pipeline for each connection (in thread — sync DB)
        import asyncio
        import json
        from app.core.db_sync import get_write_connection
        from app.pipeline.runner import run_pipeline

        for row in rows:
            connection_id = str(row["connection_id"])
            creds = json.loads(row["credentials"]) if row["credentials"] else {}

            try:
                def _sync():
                    with get_write_connection() as sync_conn:
                        return run_pipeline(
                            conn=sync_conn,
                            tenant_id=tenant_id,
                            connection_id=connection_id,
                            credentials=creds,
                            mode="incremental",
                        )

                result = await asyncio.to_thread(_sync)
                status = result.get("status", "unknown")
                log.info("scheduler: incremental sync complete — connection=%s status=%s", connection_id[:8], status)

                # Trigger KPI materialization after successful sync
                if status == "complete":
                    await _job_kpi_materialization(tenant_id, result.get("run_id"))

            except Exception as e:
                log.error("scheduler: incremental sync failed for connection=%s — %s", connection_id[:8], e)

    except Exception as e:
        log.error("scheduler: incremental sync job failed — %s", e)


async def _job_kpi_materialization(tenant_id: str, run_id: str | None = None) -> None:
    """Compute and materialize KPIs after a successful sync."""
    from datetime import datetime
    from app.core.db_sync import get_write_connection
    from app.semantic.kpi_engine import compute_all_kpis

    try:
        now = datetime.now()
        fiscal_year = now.year
        fiscal_period = now.month

        def _compute():
            with get_write_connection() as sync_conn:
                return compute_all_kpis(
                    conn=sync_conn,
                    tenant_id=tenant_id,
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    run_id=run_id,
                )

        import asyncio
        results = await asyncio.to_thread(_compute)
        computed = sum(1 for v in results.values() if v is not None)
        log.info("scheduler: KPI materialization complete — %d/%d metrics computed", computed, len(results))

    except Exception as e:
        log.error("scheduler: KPI materialization failed — %s", e)


async def _job_stale_run_cleanup() -> None:
    """Mark runs stuck in 'extracting' for >2 hours as failed."""
    from app.core.db import get_pool

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE platform.data_runs
                SET status = 'failed',
                    completed_at = now(),
                    error_message = 'Marked as failed by stale run cleanup (stuck >2 hours)'
                WHERE status IN ('extracting', 'staging', 'validating')
                  AND started_at < now() - INTERVAL '2 hours'
                """
            )
            count = int(result.split()[-1]) if result else 0
            if count > 0:
                log.info("scheduler: cleaned up %d stale runs", count)

    except Exception as e:
        log.error("scheduler: stale run cleanup failed — %s", e)

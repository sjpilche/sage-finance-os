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

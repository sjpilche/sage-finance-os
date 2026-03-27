"""
Health check endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.models.responses import wrap_response
from app.core.db import get_pool

log = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Basic liveness check — always returns 200 if the process is running."""
    return wrap_response({
        "status": "healthy",
        "service": "sage-finance-os",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/health/deep")
async def deep_health():
    """Deep health check — verifies database connectivity."""
    checks = {}

    # Check async DB pool
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchval("SELECT 1")
            checks["database"] = {"status": "healthy", "result": row}
    except Exception as e:
        log.error("deep_health_db_failed error=%s", e)
        checks["database"] = {"status": "unhealthy"}

    overall = "healthy" if all(
        c.get("status") == "healthy" for c in checks.values()
    ) else "degraded"

    return wrap_response({
        "status": overall,
        "service": "sage-finance-os",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

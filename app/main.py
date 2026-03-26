"""
Sage Finance OS — FastAPI application factory.

Small, clean entry point. All complexity lives in modules.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.db import close_pool, get_pool
from app.core.db_sync import close_sync_pool
from app.core.errors import SageError
from app.core.migration_runner import run_migrations
from app.observability.logging_config import setup_logging

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # ── Startup ──────────────────────────────────────────────
    setup_logging()
    log.info("starting sage-finance-os env=%s", settings.ENVIRONMENT)

    # Validate production secrets
    settings.validate_production()

    # Run database migrations
    if settings.RUN_MIGRATIONS:
        try:
            count = run_migrations()
            log.info("migrations_applied count=%d", count)
        except Exception as e:
            log.error("migration_failed error=%s", e)
            raise

    # Initialize async connection pool
    await get_pool()

    # Start scheduler
    try:
        from app.workflows.scheduler import get_scheduler, register_default_jobs, start_scheduler
        register_default_jobs()
        start_scheduler()
    except Exception as e:
        log.warning("scheduler_init_failed error=%s", e)

    log.info("startup_complete")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    log.info("shutting_down")

    # Stop scheduler
    try:
        from app.workflows.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass

    await close_pool()
    close_sync_pool()
    log.info("shutdown_complete")


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Sage Finance OS",
        description="Finance intelligence platform for Sage Intacct",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── Middleware (LIFO — last added runs outermost) ─────────
    # Order matters: CORS must be outermost to wrap rate-limit 429 responses.

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    from app.api.middleware.timing import TimingMiddleware
    app.add_middleware(TimingMiddleware)

    from app.api.middleware.correlation import CorrelationMiddleware
    app.add_middleware(CorrelationMiddleware)

    # ── Exception handlers ───────────────────────────────────
    @app.exception_handler(SageError)
    async def sage_error_handler(request: Request, exc: SageError):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    # ── Routers ──────────────────────────────────────────────
    from app.api.routers.health import router as health_router
    from app.api.routers.connections import router as connections_router
    from app.api.routers.sync import router as sync_router
    from app.api.routers.data import router as data_router
    from app.api.routers.quality import router as quality_router
    from app.api.routers.semantic import router as semantic_router
    from app.api.routers.analysis import router as analysis_router
    from app.api.routers.platform import router as platform_router

    app.include_router(health_router)
    app.include_router(connections_router)
    app.include_router(sync_router)
    app.include_router(data_router)
    app.include_router(quality_router)
    app.include_router(semantic_router)
    app.include_router(analysis_router)
    app.include_router(platform_router)

    return app


# Module-level app instance for uvicorn
app = create_app()

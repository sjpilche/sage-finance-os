# Sage Finance OS — Development Guide

## What this is
Finance intelligence platform that ingests from Sage Intacct and creates a trusted decision system. Built by selectively salvaging infrastructure from two legacy products (Jake CFO Platform + Privium DataClean) and rebuilding the domain clean.

## Project Structure
- `app/` — FastAPI backend (Python 3.11+), entry point `app/main.py`
- `ui/` — Next.js 16 frontend (TypeScript), port 3004
- `sql/migrations/` — Numbered SQL migrations (001-007)
- `tests/` — pytest unit + integration tests

## Running Locally

```bash
# Start PostgreSQL
docker compose up db -d

# Backend
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

# Frontend
cd ui && npm install && npm run dev
```

## Architecture

### Backend Modules
- `app/core/` — DB pools (async+sync), config, errors, auth deps, migrations, RunContext
- `app/auth/` — JWT tokens + middleware (Bearer + API key)
- `app/ingestion/` — Sage Intacct connector (7 objects, XML Web Services)
- `app/pipeline/` — Extract → write pipeline runner
- `app/contract/` — 7 batch writers (GL, TB, AP, AR, vendor, customer, COA)
- `app/quality/` — SQL quality checks (15 checks across 7 objects)
- `app/trust/` — TrustEnvelope, 6-dimension scorecard, HMAC certificates, circuit breaker
- `app/semantic/` — 26 finance metrics, P&L+BS templates, account classifier, fiscal engine, KPI materialization
- `app/analysis/` — Aging, variance, profitability, close support
- `app/workflows/` — Event bus (13 types), kill switch, APScheduler
- `app/api/routers/` — 8 routers, 43 endpoints
- `app/api/middleware/` — Correlation ID, timing, rate limit
- `app/observability/` — structlog config

### Database (PostgreSQL 16, 6 schemas)
- `platform` — tenants, connections, runs, watermarks, DQ results
- `staging` — immutable raw records (JSONB)
- `contract` — canonical financial tables (GL, TB, AP, AR, vendors, customers, COA, departments, projects, budgets)
- `audit` — append-only (transformation log, evidence links, dedup, scorecards, certificates)
- `workflow` — events, actions, kill switch, schedules
- `semantic` — metric definitions, statement templates, computed KPIs, period status

### Key Design Decisions
- **Async API + Sync Pipeline**: asyncpg for HTTP handlers, psycopg2 for ETL (bridged via asyncio.to_thread)
- **Raw SQL**: No ORM — finance queries need CTEs + window functions
- **Trust-first**: Every API response can carry TrustEnvelope metadata
- **Deterministic**: All metrics are SQL-based, no LLM math
- **Idempotent writers**: Skip if run_id already written, upsert for master data

## API Endpoints (43 total)
- `GET /health`, `GET /health/deep`
- `POST/GET/DELETE /v1/connections`, `POST /v1/connections/{id}/test`
- `POST /v1/sync/trigger`, `GET /v1/sync/runs`, `GET /v1/sync/schema`
- `GET /v1/data/{gl,tb,ap,ar,vendors,customers,coa,summary}`
- `GET /v1/quality/{scorecards,checks,certificates}`, `POST /v1/quality/quarantine/{id}/release`
- `GET /v1/semantic/{metrics,kpis,financials/pl,financials/bs,periods}`, `POST /v1/semantic/{kpis/compute,periods/close}`
- `GET /v1/analysis/{aging/ar,aging/ap,aging/ar/by-customer,variance,profitability,close-checklist}`
- `GET /v1/platform/{freshness,scheduler,kill-switch,events}`, `POST /v1/platform/kill-switch/{activate,deactivate}`

## Middleware Order (LIFO)
1. CORS (outermost)
2. Rate Limit (100/min per IP)
3. GZip (>1KB)
4. Timing (X-Process-Time header)
5. Correlation (X-Request-ID header, innermost)

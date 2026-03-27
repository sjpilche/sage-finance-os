# Sage Finance OS

**Finance intelligence platform that ingests from Sage Intacct and creates a trusted decision system.**

Built with FastAPI + Next.js 16 + PostgreSQL 16. Extracts financial data via Sage Intacct XML Web Services, runs it through a 6-dimension quality gate, and surfaces it through 43 API endpoints and a full-featured dashboard with dark mode, drill-down analytics, and CSV export.

---

## Architecture

```
                    Next.js 16 (React 19)
                    Port 3004 / Netlify
                           |
                      /api proxy
                           |
                    FastAPI (Python 3.11)
                    Port 8090 / Docker
                     /            \
              asyncpg            psycopg2
             (API layer)       (Pipeline layer)
                     \            /
                    PostgreSQL 16
                  6 schemas, 38 tables
```

**Dual-pool design**: asyncpg for non-blocking API handlers, psycopg2 for batch ETL operations. Both hit the same database — the API reads, the pipeline writes.

## Key Systems

### Data Pipeline
- **Extract** from Sage Intacct (7 objects: GL, TB, AP, AR, vendors, customers, CoA)
- **Transform** XML to canonical financial records
- **Write** to contract tables with idempotent bulk inserts
- **Watermark-based** incremental sync (only fetch what changed)
- **Scheduled** every 4 hours via APScheduler

### Trust & Quality Gate
Every pipeline run goes through a 6-dimension quality gate before data is certified:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Accuracy | 35% | Critical check pass rate |
| Completeness | 20% | Non-null field rates |
| Consistency | 15% | FK + enum validation |
| Validity | 10% | Format/range checks |
| Uniqueness | 10% | Deduplication rate |
| Timeliness | 10% | Data freshness penalty |

- **Composite >= 98% + 100% accuracy** = CERTIFIED (HMAC-SHA256 signed certificate)
- **Composite >= 98%** = CONDITIONAL
- **Below threshold** = QUARANTINED (circuit breaker blocks downstream)

### Semantic Layer
- 40+ finance metrics with SQL formulas (revenue, margins, ratios, aging)
- P&L and Balance Sheet builders from GL data
- Account classifier maps CoA entries to statement lines
- KPI materialization auto-triggers after each sync

### Analysis Engine
- **AR/AP Aging** — 4-bucket analysis with customer drill-down
- **Variance** — Budget vs actual with flagging threshold (click account -> GL entries)
- **Profitability** — Revenue/expense/margin by department, location, or class
- **Period Close** — Readiness checklist with automated checks

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript 5.7, Tailwind CSS 4 |
| Charts | Recharts 2.12 |
| Data Fetching | SWR 2.2 (stale-while-revalidate) |
| Icons | Lucide React |
| Backend | FastAPI, Python 3.11, Pydantic 2, uvicorn |
| Database | PostgreSQL 16, asyncpg + psycopg2 |
| Auth | JWT (HMAC-SHA256) + API key |
| Scheduler | APScheduler |
| Logging | structlog (JSON in prod, pretty in dev) |
| Deployment | Docker, Render (API), Netlify (UI) |

## UI Features

- **Dark mode** with system preference detection + manual toggle
- **Skeleton loading** states (dashboard shimmer, not spinners)
- **Toast notifications** with auto-dismiss
- **Breadcrumb navigation** on detail pages
- **Keyboard accessible** tables with aria-sort, skip-links
- **Screen reader** support on all charts (aria-label summaries)
- **Colorblind-safe** chart labels (direct value labels, not color-only)
- **Mobile responsive** (iOS Safari viewport fix, stacking layouts, compact tables)
- **CSV export** on data pages
- **Drill-down** from variance/aging charts to GL entries
- **Confirmation dialogs** for destructive actions (delete, kill switch)

## API Surface (43 endpoints)

```
Health        GET  /health, /health/deep
Connections   POST/GET/DELETE /v1/connections, POST .../test
Sync          POST /v1/sync/trigger, GET /v1/sync/runs
Data          GET  /v1/data/{gl,tb,ap,ar,vendors,customers,coa,summary}
Quality       GET  /v1/quality/{scorecards,checks,certificates}
Semantic      GET  /v1/semantic/{metrics,kpis,financials/pl,financials/bs}
Analysis      GET  /v1/analysis/{aging/ar,aging/ap,variance,profitability}
Platform      GET  /v1/platform/{freshness,scheduler,kill-switch,events}
```

## Database (6 schemas)

| Schema | Purpose | Tables |
|--------|---------|--------|
| `platform` | Tenants, connections, runs, watermarks | 5 |
| `staging` | Immutable raw records (JSONB) | 1 |
| `contract` | Canonical financial tables | 12 |
| `audit` | Scorecards, certificates, quarantine log | 5 |
| `workflow` | Events, kill switch, schedules | 5 |
| `semantic` | Metrics, KPIs, period status | 6 |

## Running Locally

```bash
# Start PostgreSQL
docker compose up db -d

# Run migrations + seed demo data
python -c "from app.core.migration_runner import run_migrations; run_migrations()"
python scripts/seed_demo_data.py

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

# Start frontend (separate terminal)
cd ui && npm install && npm run dev
```

Open [http://localhost:3004](http://localhost:3004)

## Test Suite

```bash
python -m pytest tests/ -v
# 67 tests passing
```

Covers: scorecard dimensions, account classification, period engine, HMAC certificates, circuit breaker thresholds, quality gate orchestration, migration retry logic, API health endpoints, Sage Intacct transformers.

## Project Structure

```
sage-finance-os/
  app/                    FastAPI backend
    api/routers/          8 routers, 43 endpoints
    api/middleware/        CORS, rate limit, timing, correlation
    auth/                 JWT + API key auth
    ingestion/            Sage Intacct connector (7 objects)
    pipeline/             Extract -> write orchestration
    contract/             7 batch writers
    quality/              15 SQL quality checks
    trust/                Scorecard, certificates, circuit breaker
    semantic/             40+ metrics, P&L/BS builders, KPI engine
    analysis/             Aging, variance, profitability, close support
    workflows/            Event bus, scheduler, kill switch
  ui/                     Next.js 16 frontend
    app/                  17 pages (App Router)
    components/           20+ reusable components
    lib/                  API client, hooks, types, utils
  sql/migrations/         7 numbered SQL migrations
  scripts/                Seed data, utilities
  tests/                  67 unit + API tests
```

## Origin

Selectively salvaged from two legacy products (Jake CFO Platform + Privium DataClean) and rebuilt clean. The Sage Intacct connector, trust system, and quality gate are production-proven code adapted for this architecture. Everything else is new.

---

Built by Steve Pilcher

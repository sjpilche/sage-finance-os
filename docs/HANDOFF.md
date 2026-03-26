# Sage Finance OS — Handoff Document

> **Version**: 0.1.0 | **Date**: 2026-03-26 | **Status**: Backend complete, Frontend skeleton

## 1. What Is This

Sage Finance OS is a **finance intelligence platform** that ingests data from Sage Intacct and creates a trusted decision system. It was built by selectively salvaging infrastructure from two legacy products (**Jake CFO Platform** + **Privium DataClean**) and rebuilding the domain layer clean.

The core value proposition: ingest financial data from Sage Intacct, run it through quality gates and trust scoring, then expose deterministic finance metrics, statements, and analysis — all backed by an auditable data lineage.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js 16 (port 3004)                   │
│                     React 19 + Tailwind CSS 4                   │
│                   SWR data fetching → /api proxy                │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (rewrites to :8090)
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI (port 8090)                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ 8 Routers│  │ Middleware │  │   Auth   │  │ Observability│   │
│  │43 endpts │  │ CORS,Rate │  │ JWT+Key  │  │  structlog   │   │
│  └────┬─────┘  │ GZip,Time │  └──────────┘  └──────────────┘   │
│       │        │ Correlation│                                    │
│  ┌────▼─────────────────────────────────────────────────────┐   │
│  │                    Domain Modules                         │   │
│  │  Ingestion → Pipeline → Contract Writers → Quality Gates  │   │
│  │  Trust (Scorecard/Certificate/CircuitBreaker)             │   │
│  │  Semantic (Metrics/Statements/Periods/KPIs)               │   │
│  │  Analysis (Aging/Variance/Profitability/Close)            │   │
│  │  Workflows (EventBus/Scheduler/KillSwitch)                │   │
│  └──────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│               PostgreSQL 16 (6 schemas, 7 migrations)           │
│  platform │ staging │ contract │ audit │ workflow │ semantic     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Async API + Sync Pipeline** | asyncpg for HTTP handlers (non-blocking), psycopg2 for ETL (bridged via `asyncio.to_thread`) |
| **Raw SQL, no ORM** | Finance queries need CTEs, window functions, and precise decimal arithmetic |
| **Trust-first** | Every API response can carry TrustEnvelope metadata (confidence, staleness, review flags) |
| **Deterministic metrics** | All 52 metrics are SQL-based — no LLM math, no approximations |
| **Idempotent writers** | Skip if run_id already written, upsert for master data |
| **Immutable audit trail** | Staging + audit tables have PostgreSQL triggers preventing UPDATE/DELETE |

---

## 3. Tech Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | >= 0.115.0 |
| Runtime | Python | >= 3.11 |
| Async DB | asyncpg | >= 0.29.0 |
| Sync DB | psycopg2-binary | >= 2.9.9 |
| HTTP Client | httpx | >= 0.27.0 |
| XML Parsing | xmltodict + lxml | >= 0.13.0, >= 5.0.0 |
| Auth | python-jose + passlib | >= 3.3.0, >= 1.7.4 |
| Scheduling | APScheduler | >= 3.10.0 |
| Logging | structlog | >= 24.0.0 |
| Validation | Pydantic + pydantic-settings | >= 2.0 |
| Data Profiling | DuckDB | >= 1.0.0 |
| Data Quality | Great Expectations + pandas | >= 1.0.0, >= 2.0.0 |
| Linter | Ruff | >= 0.5.0 |

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Next.js | 16.0.0 |
| UI Library | React | 19.0.0 |
| Styling | Tailwind CSS | 4.0.0 |
| Charts | Recharts | 2.12.0 |
| Icons | Lucide React | 0.400.0 |
| Data Fetching | SWR | 2.2.0 |
| Utilities | clsx + tailwind-merge | 2.1.0, 2.3.0 |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Database | PostgreSQL 16 (Alpine) |
| Container | Docker (python:3.11-slim) |
| Orchestration | docker-compose |

---

## 4. Project Structure

```
sage-finance-os/
├── app/                          # FastAPI backend
│   ├── main.py                   # App factory, lifespan, middleware stack
│   ├── config.py                 # Pydantic settings (env-driven)
│   ├── core/
│   │   ├── db.py                 # Async pool (asyncpg) — singleton
│   │   ├── db_sync.py            # Sync pool (psycopg2) — read/write context managers
│   │   ├── deps.py               # FastAPI dependencies (require_db, require_api_key)
│   │   ├── errors.py             # Exception hierarchy (13 types, HTTP-mapped)
│   │   ├── migration_runner.py   # Numbered SQL migration executor
│   │   └── tenant.py             # RunContext dataclass + run lifecycle (create/update/complete/fail)
│   ├── auth/
│   │   ├── tokens.py             # JWT create/verify (access + refresh)
│   │   └── middleware.py         # Multi-auth: Bearer JWT OR X-API-Key, dev passthrough
│   ├── ingestion/
│   │   └── connectors/
│   │       └── sage_intacct/
│   │           ├── config.py     # SageIntacctConfig (frozen dataclass, 3-tier credential resolution)
│   │           ├── connector.py  # Main connector (extract, test, schema, pagination, retry)
│   │           ├── objects.py    # 7-object catalog (GLDETAIL, GLACCOUNT, TRIALBALANCE, APBILL, ARINVOICE, VENDOR, CUSTOMER)
│   │           ├── transport.py  # XML Web Services transport (session mgmt, retry, rate-limit)
│   │           └── transform.py  # 7 transformers (GL, COA, TB, AP, AR, Vendor, Customer)
│   ├── pipeline/
│   │   └── runner.py             # Extract → write orchestration (status tracking, error handling)
│   ├── contract/
│   │   └── writer.py             # 7 batch writers (bulk INSERT via psycopg2.extras, upsert for masters)
│   ├── quality/
│   │   ├── checks.py             # 15 SQL quality checks across 7 objects
│   │   └── gate.py               # Quality gate pass/fail logic
│   ├── trust/
│   │   ├── envelope.py           # TrustEnvelope (confidence, staleness, review flags)
│   │   ├── scorecard.py          # 6-dimension scorecard (accuracy 35%, completeness 20%, ...)
│   │   ├── certificate.py        # HMAC-SHA256 certificates of data quality
│   │   └── circuit_breaker.py    # Quarantine runs that fail quality gates
│   ├── semantic/
│   │   ├── metric_registry.py    # 52 finance metrics (SQL-based, 7 categories)
│   │   ├── kpi_engine.py         # KPI materialization + period aggregation
│   │   ├── account_classifier.py # Account type inference from name/number patterns
│   │   ├── period_engine.py      # Fiscal calendar + period close management
│   │   └── statement_templates.py# P&L + Balance Sheet templates (hierarchical line structure)
│   ├── analysis/
│   │   ├── aging.py              # AR/AP aging by bucket (0-30, 31-60, 61-90, 90+)
│   │   ├── variance.py           # Budget vs actual variance (flagged by threshold)
│   │   ├── profitability.py      # Revenue/expense/margin by GL dimension
│   │   └── close_support.py      # 7-check close readiness checklist
│   ├── workflows/
│   │   ├── event_bus.py          # In-process pub/sub (13 event types)
│   │   ├── scheduler.py          # APScheduler integration (add/remove/status)
│   │   └── kill_switch.py        # Emergency stop (hard=block, soft=warn)
│   ├── observability/
│   │   └── logging_config.py     # structlog config (JSON for prod, console for dev)
│   └── api/
│       ├── routers/              # 8 routers, 43 endpoints (see Section 6)
│       ├── middleware/
│       │   ├── correlation.py    # X-Request-ID propagation
│       │   ├── rate_limit.py     # 100 req/min per IP (in-memory counter)
│       │   └── timing.py         # X-Process-Time header
│       └── models/
│           └── responses.py      # StandardResponse envelope (data, meta, errors)
├── ui/                           # Next.js frontend
│   ├── app/
│   │   ├── globals.css           # CSS variables (teal primary, slate neutrals)
│   │   ├── layout.tsx            # Root layout + sidebar nav (16 links, 5 sections)
│   │   └── page.tsx              # Dashboard (KPI cards + freshness table)
│   ├── components/
│   │   ├── charts/               # (empty — ready for Recharts wrappers)
│   │   ├── layout/               # (empty — ready for Sidebar extraction)
│   │   ├── tables/               # (empty — ready for DataTable)
│   │   └── ui/                   # (empty — ready for Card, Badge, etc.)
│   ├── lib/
│   │   └── api/
│   │       └── client.ts         # useApi<T> hook (SWR), apiMutate helper, ApiResponse<T> type
│   ├── next.config.ts            # standalone output, /api/* rewrite to backend
│   ├── package.json              # Dependencies + scripts (dev :3004, build, start)
│   └── tsconfig.json             # Strict, ES2017, @/* alias
├── sql/
│   └── migrations/               # 7 numbered migrations (001-007)
│       ├── 001_schemas.sql       # 6 schemas
│       ├── 002_platform.sql      # tenants, connections, runs, watermarks, DQ results, settings
│       ├── 003_staging.sql       # raw_records (immutable trigger)
│       ├── 004_contract.sql      # 16 tables (entity, GL, TB, AP, AR, vendors, customers, COA, ...)
│       ├── 005_audit.sql         # transformation_log, evidence_links, dedup, quarantine, scorecards, certificates
│       ├── 006_workflow.sql      # events, dead_letters, action_requests, kill_switch, schedules
│       └── 007_semantic.sql      # metric_definitions, statement_templates, computed_kpis, period_status
├── tests/
│   ├── unit/                     # 5 test files, 40 tests
│   │   ├── test_account_classifier.py
│   │   ├── test_period_engine.py
│   │   ├── test_scorecard.py
│   │   ├── test_transforms.py
│   │   └── test_trust_envelope.py
│   └── integration/              # (empty — not yet implemented)
├── pyproject.toml                # Python deps, ruff + pytest config
├── Dockerfile                    # python:3.11-slim, port 8090
├── docker-compose.yml            # PostgreSQL 16 + backend
├── .env.example                  # All environment variables documented
├── .gitignore                    # Python, Node, env files
└── CLAUDE.md                     # AI-readable development guide
```

---

## 5. Database Schema

### Schema Map (6 schemas, 38 tables)

#### `platform` — System metadata (7 tables)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tenants` | Multi-tenant registry | tenant_id (PK), slug (UNIQUE), name, is_active |
| `connections` | Sage Intacct credentials | connection_id (PK), tenant_id (FK), credentials (JSONB), status |
| `data_runs` | Pipeline execution log | run_id (PK), tenant_id (FK), status, started_at, completed_at, summary (JSONB) |
| `raw_assets` | Ingested batch metadata | asset_id (PK), run_id (FK), object_type, row_count |
| `watermarks` | Incremental sync tracking | UNIQUE(tenant_id, connection_id, object_name), last_value, last_sync_at |
| `dq_results` | Quality check results | result_id (PK), run_id (FK), check_name, passed, severity |
| `settings` | Key-value platform config | key (PK), value (JSONB) |

#### `staging` — Immutable raw records (1 table)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `raw_records` | Immutable JSONB store | raw_id (PK), run_id, data (JSONB), source_checksum. **UPDATE/DELETE trigger prevents mutation.** |

#### `contract` — Canonical financial data (16 tables)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `entity` | Legal entities | entity_id (PK), entity_code (UNIQUE per tenant), currency_code |
| `fiscal_calendar` | Fiscal periods | fiscal_year, period_number, start_date, end_date |
| `department` | Departments | dept_code (UNIQUE per tenant+entity), parent_dept |
| `chart_of_accounts` | COA | account_number (UNIQUE per tenant+entity), account_type, normal_balance |
| `gl_entry` | General ledger | posting_date, account_number, amount (18,2), debit/credit, dimensions 1-3 |
| `trial_balance` | Trial balance | as_of_date, account_number, beginning/ending balance, debits/credits |
| `vendor` | Vendor master | vendor_code (UNIQUE per tenant), payment_terms, contact_email |
| `customer` | Customer master | customer_code (UNIQUE per tenant), credit_limit, payment_terms |
| `ap_invoice` | Accounts payable | vendor_code, invoice_number, total_amount, paid_amount, balance, status |
| `ap_payment` | AP payments | vendor_code, payment_date, amount, payment_method |
| `ar_invoice` | Accounts receivable | customer_code, invoice_number, total_amount, paid_amount, balance, status |
| `ar_payment` | AR payments | customer_code, payment_date, amount, payment_method |
| `project` | Jobs/projects | project_number (UNIQUE per tenant), contract_amount, percent_complete |
| `job_cost` | Project costs | project_id (FK), cost_type, amount, quantity |
| `employee` | Employees | employee_code (UNIQUE per tenant), department_code, title |
| `budget_line` | Budgets | department_code, account_number, fiscal_year/period, budget_amount, scenario |

#### `audit` — Append-only evidence (6 tables)
| Table | Purpose | Immutable? |
|-------|---------|------------|
| `transformation_log` | Before/after transformation evidence | Yes (trigger) |
| `evidence_links` | Source → contract row mapping + checksums | Yes (trigger) |
| `dedup_log` | Deduplication decisions | Yes (trigger) |
| `quarantine_log` | Run quarantine + resolution tracking | No (resolution updates) |
| `scorecard_results` | 6-dimension quality scores (0-100) | No |
| `certificates` | HMAC-signed quality certificates | Yes (trigger) |

#### `workflow` — Events and automation (6 tables)
| Table | Purpose |
|-------|---------|
| `events` | Pub/sub event log (13 types) |
| `dead_letters` | Failed event deliveries |
| `action_requests` | Governed action queue (risk-tiered) |
| `kill_switch_rules` | Emergency stop rules (UNIQUE per scope) |
| `kill_switch_log` | Kill switch audit trail |
| `sync_schedules` | Cron-based sync scheduling |

#### `semantic` — Metrics and intelligence (6 tables)
| Table | Purpose |
|-------|---------|
| `metric_definitions` | 52 finance metric definitions (SQL formulas) |
| `statement_templates` | Income statement + balance sheet templates |
| `statement_template_lines` | Hierarchical line items (line_key, parent_key, sort_order) |
| `statement_account_mappings` | COA → statement line mappings |
| `computed_kpis` | Materialized KPI values per tenant/period |
| `period_status` | Fiscal period lifecycle (open → closing → closed → locked) |

---

## 6. API Reference (43 Endpoints)

### Standard Response Envelope

Every endpoint returns:
```json
{
  "data": <T>,
  "meta": {
    "generated_at": "2026-03-26T12:00:00Z",
    "refreshed_at": "2026-03-26T11:55:00Z",
    "is_stale": false,
    "version": "1.0",
    "correlation_id": "abc-123"
  },
  "errors": []
}
```

### Middleware Stack (applied LIFO)
1. CORS (outermost) — origins from `ALLOWED_ORIGINS`
2. Rate Limit — 100/min per IP, in-memory counter
3. GZip — responses > 1KB
4. Timing — `X-Process-Time` header (seconds)
5. Correlation — `X-Request-ID` header (innermost)

### Authentication
- **Bearer JWT** — `Authorization: Bearer <token>` (access or refresh token)
- **API Key** — `X-API-Key: <key>` header
- **Dev passthrough** — In development mode, unauthenticated requests get `dev-user` identity
- **Public paths** — `/health`, `/health/deep`, `/docs`, `/openapi.json` skip auth

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check → `{status, service, timestamp}` |
| GET | `/health/deep` | DB connectivity check → `{status, checks: {database: ...}}` |

### Connections (`/v1/connections`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/connections` | Create connection (name, credentials{sender_id, sender_password, company_id, user_id, user_password}) |
| GET | `/v1/connections` | List all connections (credentials redacted) |
| GET | `/v1/connections/{id}` | Get connection detail (passwords show as `***`) |
| POST | `/v1/connections/{id}/test` | Test connection (updates status + last_tested_at) |
| DELETE | `/v1/connections/{id}` | Delete connection |

### Sync (`/v1/sync`)
| Method | Path | Params | Description |
|--------|------|--------|-------------|
| POST | `/v1/sync/trigger` | body: {connection_id, objects?, mode?} | Trigger async pipeline (background task) |
| GET | `/v1/sync/runs` | ?limit=20 | List recent runs |
| GET | `/v1/sync/runs/{id}` | | Run detail |
| GET | `/v1/sync/schema` | ?connection_id= | Available Sage Intacct objects |

**Run statuses**: pending → extracting → profiling → mapping → staging → validating → certifying → promoting → complete | failed | quarantined

### Data (`/v1/data`)
All paginated: `?limit=100&offset=0`

| Method | Path | Extra Filters | Description |
|--------|------|---------------|-------------|
| GET | `/v1/data/summary` | | Row counts per contract table |
| GET | `/v1/data/gl` | account, date_from, date_to, dimension_1 | GL journal entries |
| GET | `/v1/data/tb` | | Trial balance rows |
| GET | `/v1/data/ap` | status, vendor | AP invoices |
| GET | `/v1/data/ar` | status, customer | AR invoices |
| GET | `/v1/data/vendors` | | Vendor master |
| GET | `/v1/data/customers` | | Customer master |
| GET | `/v1/data/coa` | account_type | Chart of accounts |

**Pagination response**: `{total, limit, offset, rows: [...]}`

### Quality (`/v1/quality`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/quality/scorecards` | List recent scorecards (6 dimensions + composite + gate_status) |
| GET | `/v1/quality/scorecards/{run_id}` | Scorecard for specific run |
| GET | `/v1/quality/checks/{run_id}` | DQ check results → `{run_id, total, passed, failed, pass_rate, checks}` |
| GET | `/v1/quality/certificates` | List HMAC-signed certificates |
| POST | `/v1/quality/quarantine/{run_id}/release` | Release quarantined run (body: {approver, reason}) |

**Scorecard dimensions**: accuracy (35%), completeness (20%), consistency (15%), validity (10%), uniqueness (10%), timeliness (10%)
**Verdicts**: CERTIFIED (composite >= 98 AND accuracy = 100), CONDITIONAL, FAILED

### Semantic (`/v1/semantic`)
| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/v1/semantic/metrics` | | List 52 metric definitions grouped by category |
| GET | `/v1/semantic/kpis` | ?fiscal_year= | Computed KPI values |
| POST | `/v1/semantic/kpis/compute` | body: {fiscal_year, fiscal_period?} | Trigger KPI materialization |
| GET | `/v1/semantic/financials/pl` | ?fiscal_year=&fiscal_period= | Income statement (hierarchical lines) |
| GET | `/v1/semantic/financials/bs` | ?fiscal_year= | Balance sheet (sections + totals) |
| GET | `/v1/semantic/periods` | ?fiscal_year= | Period statuses (open/closing/closed/locked) |
| POST | `/v1/semantic/periods/close` | body: {fiscal_year, fiscal_period, actor} | Close a fiscal period |

**Metric categories**: revenue, expense, profitability, liquidity, efficiency, leverage, aging
**P&L line types**: header, detail, subtotal, total (rendered hierarchically via parent_key + sort_order)

### Analysis (`/v1/analysis`)
| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/v1/analysis/aging/ar` | | AR aging by bucket (0-30, 31-60, 61-90, 90+) |
| GET | `/v1/analysis/aging/ap` | | AP aging by bucket |
| GET | `/v1/analysis/aging/ar/by-customer` | ?limit=20 | Top customers by outstanding balance |
| GET | `/v1/analysis/variance` | ?fiscal_year=&fiscal_period=&threshold_pct=10 | Budget vs actual with flagging |
| GET | `/v1/analysis/profitability` | ?fiscal_year=&dimension=dimension_1 | Revenue/expense/margin by dimension |
| GET | `/v1/analysis/close-checklist` | ?fiscal_year=&fiscal_period= | 7-check close readiness |

**Close checklist checks**: gl_entries_exist, gl_balanced, no_overdue_ap, no_overdue_ar, data_fresh, period_open, budget_exists

### Platform (`/v1/platform`)
| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/v1/platform/freshness` | | Data freshness per object (stale = >8hrs) |
| GET | `/v1/platform/scheduler` | | Scheduled job status |
| GET | `/v1/platform/kill-switch` | | Kill switch rules |
| POST | `/v1/platform/kill-switch/activate` | body: {scope?, mode?, reason?, actor?} | Activate kill switch |
| POST | `/v1/platform/kill-switch/deactivate` | body: same | Deactivate kill switch |
| GET | `/v1/platform/events` | ?limit=50&event_type= | Recent platform events |

---

## 7. Data Pipeline Flow

```
1. TRIGGER (/v1/sync/trigger)
   └→ Validate connection exists + is active
   └→ Create data_run (status: extracting)
   └→ Launch background task

2. EXTRACT (pipeline/runner.py → ingestion/connector)
   └→ For each object in scope:
       └→ connector.extract(object_name, watermark, batch_size=1000)
       └→ Paginated XML Web Services calls (readByQuery → readMore)
       └→ Transform raw XML → canonical dicts (7 transformers)
       └→ GLDETAIL uses date-range chunking (12 monthly windows)
       └→ TRIALBALANCE uses legacy get_trialbalance (no pagination)

3. WRITE (contract/writer.py)
   └→ 7 batch writers (one per object type)
   └→ GL, TB, AP, AR: bulk INSERT (skip if run_id exists)
   └→ Vendor, Customer, COA: UPSERT on natural key
   └→ All use psycopg2.extras for bulk operations

4. QUALITY (quality/checks.py)
   └→ 15 SQL checks across 7 objects
   └→ Check types: null checks, duplicate checks, referential integrity, range validation
   └→ Each check: {object_name, check_name, passed, severity, details}
   └→ Results stored in platform.dq_results

5. TRUST (trust/scorecard.py → certificate.py → circuit_breaker.py)
   └→ Compute 6-dimension scorecard from DQ results
   └→ Verdict: CERTIFIED / CONDITIONAL / FAILED
   └→ If CERTIFIED: issue HMAC-signed certificate
   └→ If FAILED: quarantine run (circuit_breaker), status → quarantined

6. COMPLETE
   └→ Update data_run status: complete | failed | quarantined
   └→ Update watermarks for incremental sync
   └→ Emit event to event bus
```

---

## 8. Sage Intacct Connector Detail

### Supported Objects (7)
| Intacct Object | Canonical Table | Extraction Method | Watermark Field |
|---------------|----------------|-------------------|----------------|
| GLDETAIL | gl_entry | Date-range chunking | WHENMODIFIED |
| GLACCOUNT | chart_of_accounts | readByQuery pagination | WHENMODIFIED |
| TRIALBALANCE | trial_balance | get_trialbalance (legacy) | None (always full) |
| APBILL | ap_invoice | readByQuery pagination | WHENMODIFIED |
| ARINVOICE | ar_invoice | readByQuery pagination | WHENMODIFIED |
| VENDOR | vendor | readByQuery pagination | WHENMODIFIED |
| CUSTOMER | customer | readByQuery pagination | WHENMODIFIED |

### Transport Layer
- **Protocol**: XML Web Services (SOAP-like) via `https://api.intacct.com/ia/xml/xmlgw.phtml`
- **Auth**: Session-based (25-min TTL, auto-renewed)
- **Retry**: 3 attempts with exponential backoff for 429, 524, connection errors
- **Rate limits**: Handled with Retry-After header parsing
- **Multi-entity**: Optional `<locationid>` element in XML envelope
- **Batch size**: Capped at 2000 (Intacct API limit)

### Credential Resolution (3-tier)
1. Database vault (`platform.connections.credentials` JSONB)
2. Environment variables (`SAGE_INTACCT_*`)
3. Constructor args (direct dict)

---

## 9. Trust System

### TrustEnvelope (attached to API responses)
```python
{
    "source": "sage_intacct",       # data provenance
    "confidence": 0.95,             # 0.0-1.0
    "confidence_level": "high",     # critical (<= 0.50) | low | medium | high (>= 0.85)
    "risk_level": "low",            # derived from confidence
    "is_stale": false,              # age-based staleness
    "review_required": false,       # true if low confidence or high risk
    "data_sources": ["sage_intacct"],
    "timestamp": "2026-03-26T12:00:00Z"
}
```

### Scorecard (6 dimensions, weighted composite)
| Dimension | Weight | Gate | Calculation |
|-----------|--------|------|-------------|
| Accuracy | 35% | 100% required for CERTIFIED | % critical DQ checks passed |
| Completeness | 20% | | Average non-null rate |
| Consistency | 15% | | FK + enum check pass rate |
| Validity | 10% | | Format/range/type check pass rate |
| Uniqueness | 10% | | 1 - (duplicates / total) |
| Timeliness | 10% | | Staleness penalty based on run age |

**Note**: Consistency, validity, uniqueness, and timeliness dimensions currently stub at 100.0. Accuracy and completeness are fully implemented.

### Verdicts
- **CERTIFIED**: composite >= 98.0 AND accuracy = 100.0 → issue HMAC certificate
- **CONDITIONAL**: composite >= 98.0 AND accuracy < 100.0 → pass with warning
- **FAILED**: composite < 98.0 → quarantine the run

### Circuit Breaker
- Failed runs are quarantined (status = `quarantined`)
- Quarantine log records reason + scorecard score
- Release requires explicit `POST /v1/quality/quarantine/{run_id}/release` with approver + reason

---

## 10. Semantic Layer

### 52 Finance Metrics (7 categories)
| Category | Metrics | Example |
|----------|---------|---------|
| Revenue | Total revenue, operating revenue, other income | `SELECT SUM(credit_amount) FROM contract.gl_entry WHERE account_type = 'Revenue'` |
| Expense | Total expenses, COGS, operating expenses | Similar GL aggregation by account type |
| Profitability | Gross margin, operating margin, net margin | Revenue - expense ratios |
| Liquidity | Current ratio, quick ratio, cash ratio | Balance sheet ratios |
| Efficiency | DSO, DPO, inventory turnover | Aging + revenue calculations |
| Leverage | Debt-to-equity, interest coverage | Balance sheet ratios |
| Aging | AR days outstanding, AP days outstanding | Weighted average from aging buckets |

### Financial Statements
- **Income Statement**: Hierarchical template with 14 line items (revenue → COGS → gross profit → operating expenses → operating income → other → net income)
- **Balance Sheet**: Grouped by account_type from trial_balance JOIN chart_of_accounts

### Fiscal Periods
- Lifecycle: `open` → `closing` → `closed` → `locked`
- Supports non-calendar fiscal years (configurable month-end)

---

## 11. Frontend State

### What Exists
| File | What It Does |
|------|-------------|
| `ui/app/layout.tsx` | Root layout with fixed dark sidebar (slate-900), 16 nav links in 5 sections |
| `ui/app/page.tsx` | Dashboard: 8 KPI cards (data summary) + data freshness table |
| `ui/lib/api/client.ts` | `useApi<T>()` SWR hook, `apiMutate<T>()` for mutations, `ApiResponse<T>` type |
| `ui/app/globals.css` | CSS variables: --accent (#0f7173 teal), --bg, --text, --success/warning/danger |
| `ui/next.config.ts` | Standalone output, `/api/*` rewrite to backend |

### What Does NOT Exist Yet
- No reusable UI components (Card, Badge, DataTable, etc.)
- No TypeScript types for API responses
- No chart components (Recharts wrappers)
- No pages beyond the dashboard (0 of 16 sidebar links work)
- No loading/error states
- No form components

### Design Tokens
```css
--accent: #0f7173       /* Teal primary */
--accent-light: #14a3a8 /* Teal light */
--bg: #ffffff           /* White */
--bg-secondary: #f8fafc /* Light slate */
--text: #0f172a         /* Dark slate */
--text-secondary: #64748b
--border: #e2e8f0
--success: #16a34a      /* Green */
--warning: #eab308      /* Yellow */
--danger: #dc2626       /* Red */
```

---

## 12. Testing

### Unit Tests (40 tests across 5 files)
| File | Tests | Coverage |
|------|-------|----------|
| `test_account_classifier.py` | 15 | Account type classification (asset/liability/equity/revenue/expense) |
| `test_period_engine.py` | 10 | Fiscal year/period calculation, calendar generation |
| `test_scorecard.py` | 9 | Scorecard computation, verdicts, weight validation |
| `test_transforms.py` | 15 | All 7 Sage Intacct transformers (debit/credit, status mapping, etc.) |
| `test_trust_envelope.py` | 8 | Confidence levels, review triggers, boundaries |

### Not Yet Implemented
- Integration tests (directory exists, empty)
- API endpoint tests
- Frontend tests

---

## 13. Running Locally

```bash
# 1. Start PostgreSQL
docker compose up db -d

# 2. Backend
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

# 3. Frontend
cd ui && npm install && npm run dev
```

- Backend: http://localhost:8090 (API docs at /docs)
- Frontend: http://localhost:3004
- Database: postgresql://sage:sage@localhost:5432/sage_finance

### Environment Variables
Copy `.env.example` to `.env` and update:
- `JWT_SECRET_KEY` — change from default for production
- `API_KEY` — change from default for production
- `SAGE_INTACCT_*` — fill in for Sage Intacct connectivity
- `DATABASE_URL` / `DATABASE_URL_SYNC` — if not using default Docker setup

---

## 14. Known Issues & Gaps

| Issue | Severity | Location |
|-------|----------|----------|
| `docker-compose.yml` references `Dockerfile.sage` but only `Dockerfile` exists | Build blocker | docker-compose.yml:24 |
| Balance Sheet endpoint is simplified (account_type grouping only, not template-driven) | Functional gap | app/api/routers/semantic.py |
| Scorecard dimensions (consistency, validity, uniqueness, timeliness) stub at 100.0 | Partial impl | app/trust/scorecard.py |
| Dead code paths with `get_cursor()` placeholder in analysis/semantic routers | Code quality | app/api/routers/analysis.py:43, semantic.py:79 |
| No auth enforcement on most routes (only `require_db` dependency) | Security gap | app/api/routers/*.py |
| Rate limiter is in-memory only (resets on restart, no distributed support) | Scalability | app/api/middleware/rate_limit.py |
| No integration tests | Test coverage | tests/integration/ |
| Frontend is ~20% complete (dashboard only) | Feature gap | ui/ |

---

## 15. Glossary

| Term | Meaning |
|------|---------|
| **RunContext** | Immutable context bag threaded through pipeline steps (run_id, tenant_id, mode, schemas) |
| **Contract table** | Canonical, normalized financial data table (as opposed to raw staging) |
| **Watermark** | Last-seen value for incremental sync (typically WHENMODIFIED timestamp) |
| **TrustEnvelope** | Metadata attached to API responses indicating data confidence and provenance |
| **Scorecard** | 6-dimension quality score computed after each sync run |
| **Certificate** | HMAC-signed proof that a dataset passed quality gates |
| **Circuit breaker** | Mechanism that quarantines runs failing quality thresholds |
| **Kill switch** | Emergency stop mechanism (hard=block all, soft=warn only) |
| **Dimension 1/2/3** | GL entry classification fields (typically department, location/project, class) |

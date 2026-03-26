# REBUILD MASTER PLAN — Sage Finance OS

> **Date**: 2026-03-26
> **Status**: Active — Phase 1 complete, Phase 2 next
> **Mission**: Selective salvage from Legacy Jake + Legacy DataClean → new finance intelligence platform for Sage Intacct
> **This is the single source of truth for the entire rebuild.**

---

## Table of Contents

1. [Legacy Repo Audit](#a-legacy-repo-audit)
2. [Reuse Decision Matrix](#b-reuse-decision-matrix)
3. [New Product Architecture](#c-new-product-architecture)
4. [Domain Model](#d-domain-model)
5. [Database Schema](#e-database-schema)
6. [Ingestion Architecture](#f-ingestion-architecture)
7. [Data Pipeline](#g-data-pipeline)
8. [Quality & Trust Layer](#h-quality--trust-layer)
9. [Semantic Layer](#i-semantic-layer)
10. [Workflow & Orchestration](#j-workflow--orchestration)
11. [Dashboard / UI](#k-dashboard--ui)
12. [MVP Boundaries](#l-mvp-boundaries)
13. [Tech Stack Decisions](#m-tech-stack-decisions)
14. [Build Sequence](#n-build-sequence)
15. [Implementation Status](#o-implementation-status)
16. [File Inventory](#p-file-inventory)

---

## A. Legacy Repo Audit

### Legacy Jake

**What it is**: Production-grade construction finance operations platform.
**Scale**: FastAPI + Next.js 16, 56 agents, 602 tables, 9 schemas, 4,881 tests, 31M GL postings, 35 companies.
**Built for**: Empire Capital (PE-backed construction holding company).

#### Strongest reusable components

| Component | LOC | Why it's good |
|-----------|-----|---------------|
| Trust Envelope (`shared/trust_envelope.py`) | 398 | Confidence/risk metadata on any output. Dataclass, weighted formula, auto-review triggers |
| Event Bus (`shared/event_bus.py`) | 646 | In-process async pub/sub, cascade depth limiter, dead-letter handling, DB persistence |
| Kill Switch (`shared/kill_switch.py`) | 262 | Global + per-module mutation control, SHA-256 tamper detection, hot-reload |
| Action Queue (`shared/action_queue.py`) | ~100 | Governed action submission, idempotency keys, risk tiers (GREEN/YELLOW/RED) |
| Response Envelope (`backend/api/models/responses.py`) | 57 | `StandardResponse[T]` with `ResponseMetadata` (refreshed_at, is_stale, correlation_id) |
| Error Hierarchy (`shared/errors.py`) | ~200 | 15+ typed exceptions with centralized FastAPI handlers |
| Scheduler Registry (`shared/scheduler_registry.py`) | 298 | Centralized APScheduler management, SLA tracking |
| Structured Logging | ~150 | structlog, JSON output, correlation IDs per request |
| Auth Middleware (`backend/middleware/auth_middleware.py`) | ~200 | JWT + API key dual auth, agent key cache, dev passthrough |
| Finance Semantic Kernel (`shared/finance_semantic_kernel.py`) | 607 | P&L hierarchy, account classification, metric defs — **concept reusable, code Empire-specific** |

#### Weakest / most dangerous

- `app_factory.py` (880 LOC) — 7 concerns in one file, monolithic
- `chat_orchestrator.py` (1,381 LOC) — over-engineered ReAct chain, 11 templates
- `kpi_tracker.py` (1,150 LOC) — monolithic, coupled to construction KPIs
- `event_subscriptions.py` (1,004 LOC) — hardcoded 50+ subscription mappings
- All 56 agent modules — tightly coupled to construction/PE business logic

#### Over-engineering

- CFO Manager FSM with HTTP round-trip for action approval
- Collective Brain 4-layer agent memory system
- Monte Carlo engine, driver-based budget engine
- 24 chat-capable agents with ReAct multi-agent chaining
- 47 validated event types (most never fire)

#### Disposition

| Action | What |
|--------|------|
| **DELETE** | All 56 agent modules, chat orchestrator, collective brain, CFO Manager, Monte Carlo, cost behavior engine, forecast snapshot manager, all domain prompts, `_archive/`, all 52 frontend agent pages |
| **QUARANTINE** | budget_forecast (30% reusable math), anomaly_detection (generic detectors), close_audit_prep (period locking), margin_fade (alert concept) |
| **ADAPT** | Trust Envelope (slim to ~80 LOC), Event Bus (new events), Kill Switch (simplify), Action Queue (in-process), Scheduler Registry, Response Envelope, Auth Middleware |
| **INSPIRE REWRITE** | Finance Semantic Kernel (P&L hierarchy concept only), KPI Tracker (rewrite as kpi_engine), 3-Layer Reconciliation (generalize) |

---

### Legacy DataClean

**What it is**: SaaS data cleaning and AI-readiness platform.
**Scale**: FastAPI + Next.js 15, 195 Python modules, ~30K LOC, 595+ tests, 6 schemas.
**Pipeline**: 7-stage: ingest → profile → parse → map → write → quality → certify.
**Multi-tenant**: Row-level security + optional schema-per-tenant.

#### Strongest reusable components

| Component | Location | Why it's good |
|-----------|----------|---------------|
| Sage Intacct Connector | `ingestion/connectors/sage_intacct/` (7 files) | Production-proven, 7 objects, XML+REST, multi-entity, incremental sync, 3-tier credential resolution |
| Pipeline Runner | `pipeline/runner.py` | Clean orchestrator, RunContext threading, status FSM, always completes or fails |
| RunContext | `core/tenant.py` | Tenant isolation threaded through all operations, run lifecycle |
| YAML Mapping Engine | `mapping/engine.py` + `transforms.py` | Template-driven field mapping, 16 transforms, evidence metadata |
| Contract Writers | `contract/*.py` | Batch writers for GL, TB, AP, AR, vendor, customer with evidence links |
| 6-Level Reconciliation | `transform/reconcile.py` | Row count, completeness, checksum, TB balance, FK, enum |
| SHA-256 Dedup | `transform/dedup.py` | Content-hash dedup with audit trail, SQL-injection safe |
| Scorecard | `certification/scorecard.py` | 6-dimension weighted (0-100), deterministic gate logic |
| HMAC Certificate | `certification/certificate.py` | Tamper-evident signed data certificates |
| Circuit Breaker | `certification/circuit_breaker.py` | Auto-quarantine failed runs, manual override |
| Evidence Packs | `certification/evidence_pack.py` | SOC-ready audit bundles |
| DuckDB Profiler | `ingestion/profiler.py` | Fast column profiling (cardinality, types, nulls) |
| BaseConnector ABC | `ingestion/connectors/base.py` | Pluggable connector interface |
| Quality Gate (GE 1.x) | `quality/gate.py` + `suites/` | Declarative expectation suites per object |
| Contract Schema SQL | `sql/bootstrap/004_contract_tables.sql` | Clean canonical tables, constraints, indexes, evidence |

#### Weakest / over-engineered

- psycopg2 sync throughout (async-ready but blocking)
- Great Expectations 1.x heavy dependency
- RAG mapping (OpenAI + sentence-transformers + pgvector) — overkill for structured ERP
- Fuzzy dedup — rarely used
- Prefect creates dual code paths
- Multi-tier Stripe billing ($49/$199/$499)
- Schema-per-tenant enterprise isolation (premature)

#### Disposition

| Action | What |
|--------|------|
| **DELETE** | `agent_tools/` (15 modules), `ai/`, `ai_proof/`, `compliance/`, `monitoring/`, `orchestration/`, `delivery/`, `website/`, all SaaS features (billing, Stripe, plans, signup), CRM tables |
| **KEEP AS-IS** | Sage Intacct connector (7 files), BaseConnector, mapping engine + transforms, scorecard, certificate, circuit breaker, evidence packs, profiler, dedup, reconciliation |
| **ADAPT** | Pipeline runner (remove file paths, add semantic promotion), contract writers (add dept/project/employee), quality gate (new suites), RunContext (remove enterprise isolation), migration runner |

---

## B. Reuse Decision Matrix

| Module / Area | Source | Keep | Adapt | Rewrite | Delete | Reason |
|---------------|--------|:----:|:-----:|:-------:|:------:|--------|
| Sage Intacct Connector (7 files) | DataClean | ✅ | | | | Production-proven, 7 objects, XML+REST, multi-entity, incremental |
| BaseConnector ABC | DataClean | ✅ | | | | Clean interface, extensible |
| DuckDB Profiler | DataClean | ✅ | | | | Fast column profiling |
| Pipeline Runner | DataClean | | ✅ | | | Remove file paths, add semantic promotion step |
| Pipeline Steps | DataClean | | ✅ | | | Focus on connector extraction, remove file upload |
| RunContext / Tenant | DataClean | | ✅ | | | Remove enterprise schema-per-tenant for V1 |
| YAML Mapping Engine | DataClean | ✅ | | | | Clean, extensible, 16 transforms |
| Mapping Templates | DataClean | | ✅ | | | Expand sage_intacct template for new objects |
| Contract Writers (GL, TB, AP, AR, Vendor, Customer) | DataClean | ✅ | | | | Proven batch writers with evidence |
| Contract Writers (Department, Project, Employee) | — | | | ✅ | | New writers for Sage objects |
| Contract Schema SQL | DataClean | | ✅ | | | Add department, project, employee, budget tables |
| SHA-256 Dedup | DataClean | ✅ | | | | Content-hash dedup with audit trail |
| 6-Level Reconciliation | DataClean | ✅ | | | | Row count, completeness, checksum, TB, FK, enum |
| Quality Gate (GE 1.x) | DataClean | ✅ | | | | Declarative expectation suites |
| Scorecard | DataClean | ✅ | | | | 6-dimension weighted, deterministic gate |
| HMAC Certificate | DataClean | ✅ | | | | Tamper-evident data certification |
| Circuit Breaker | DataClean | ✅ | | | | Auto-quarantine with audit trail |
| Evidence Packs | DataClean | ✅ | | | | SOC-ready audit bundles |
| Trust Envelope | Jake | | ✅ | | | Slim to ~80 LOC, remove agent-specific fields |
| Event Bus | Jake | | ✅ | | | New event types for Sage Finance OS |
| Kill Switch | Jake | | ✅ | | | Simplify to global + per-module |
| Action Queue | Jake | | ✅ | | | In-process for V1, remove CFO Manager round-trip |
| Response Envelope | Jake | ✅ | | | | StandardResponse[T] + ResponseMetadata |
| Error Hierarchy | Jake | ✅ | | | | 15+ exception classes |
| Scheduler Registry | Jake | | ✅ | | | Keep APScheduler wrapper, simplify |
| Auth Middleware | Jake | | ✅ | | | JWT + API key, remove agent key cache |
| Structured Logging | Jake | ✅ | | | | JSON output, correlation IDs |
| Metric Registry | — | | | ✅ | | New: ~40 finance metrics with SQL formulas |
| Statement Templates | Jake (concept) | | | ✅ | | P&L/BS hierarchy from FSK, discard Empire mappings |
| KPI Engine | Jake (concept) | | | ✅ | | Rewrite as materialization engine |
| Period Engine | — | | | ✅ | | New: configurable fiscal calendar |
| Account Classifier | — | | | ✅ | | New: COA → statement template mapping |
| All 56 Jake Agents | Jake | | | | ✅ | Construction/PE-specific |
| Chat Orchestrator | Jake | | | | ✅ | Over-engineered, not needed V1 |
| Collective Brain | Jake | | | | ✅ | Premature agent memory |
| CFO Manager FSM | Jake | | | | ✅ | Overkill governance for V1 |
| 15 DataClean Agent Tools | DataClean | | | | ✅ | Jake bridge endpoints |
| RAG Mapping / AI | DataClean | | | | ✅ | Defer until data model stable |
| SaaS Billing / Stripe | DataClean | | | | ✅ | Single-tenant V1 |
| Prefect Orchestration | DataClean | | | | ✅ | APScheduler sufficient for V1 |
| SOX Compliance | DataClean | | | | ✅ | Defer to V2 |
| Drift Detection | DataClean | | | | ✅ | Defer to V2 |
| Jake Frontend (52 pages) | Jake | | | | ✅ | Agent-specific, rebuild from scratch |
| DataClean Dashboard | DataClean | | ✅ | | | Use as UI scaffold |

---

## C. New Product Architecture

```
sage-finance-os/
├── app/                              # Python backend (FastAPI)
│   ├── main.py                       # App factory (~100 LOC)
│   ├── config.py                     # Pydantic Settings
│   ├── core/
│   │   ├── db.py                     # Async pool (asyncpg) — from Jake
│   │   ├── db_sync.py               # Sync pool (psycopg2) — from DataClean
│   │   ├── tenant.py                # RunContext — from DataClean
│   │   ├── errors.py                # Exception hierarchy — from Jake
│   │   ├── deps.py                  # FastAPI DI: AuthDep, ConnDep
│   │   └── migration_runner.py      # SQL-file migrations — from DataClean
│   ├── auth/
│   │   ├── tokens.py                # JWT issue/verify
│   │   └── middleware.py            # Auth middleware — adapted from Jake
│   ├── ingestion/
│   │   ├── connectors/
│   │   │   ├── base.py              # BaseConnector ABC — from DataClean
│   │   │   ├── sage_intacct/        # Full connector — from DataClean (7 files)
│   │   │   │   ├── connector.py     # Main class: extract, test, get_schema
│   │   │   │   ├── config.py        # Credential management (DB vault / env)
│   │   │   │   ├── objects.py       # 7-object catalog (GL, TB, AP, AR, Vendor, Customer, COA)
│   │   │   │   ├── transport.py     # XML envelope, session mgmt, retry (429/524)
│   │   │   │   └── transform.py     # 7 pure transformers (GLDETAIL→gl_entry, etc.)
│   │   │   ├── csv.py               # Manual CSV upload fallback (Phase 2)
│   │   │   └── registry.py          # Connector registry (Phase 2)
│   │   ├── profiler.py              # DuckDB profiler — from DataClean (Phase 2)
│   │   └── staging.py               # Raw record staging (Phase 2)
│   ├── pipeline/
│   │   ├── runner.py                # Pipeline orchestrator — adapted from DataClean (Phase 2)
│   │   ├── steps.py                 # Step functions — adapted from DataClean (Phase 2)
│   │   └── worker.py               # Background job dispatch (Phase 2)
│   ├── mapping/
│   │   ├── engine.py                # YAML template engine — from DataClean (Phase 2)
│   │   ├── transforms.py           # 16 transform rules — from DataClean (Phase 2)
│   │   └── templates/
│   │       └── sage_intacct_v2.yaml # Mapping template (Phase 2)
│   ├── contract/
│   │   ├── gl_entry.py              # From DataClean (Phase 2)
│   │   ├── trial_balance.py         # From DataClean (Phase 2)
│   │   ├── ap.py, ar.py             # From DataClean (Phase 2)
│   │   ├── vendor.py, customer.py   # From DataClean (Phase 2)
│   │   ├── entity.py                # From DataClean (Phase 2)
│   │   ├── department.py            # NEW (Phase 2)
│   │   ├── project.py               # NEW (Phase 2)
│   │   ├── employee.py              # NEW (V2)
│   │   ├── evidence.py              # SHA-256 evidence — from DataClean (Phase 2)
│   │   └── writer.py                # Batch dispatch — from DataClean (Phase 2)
│   ├── quality/
│   │   ├── gate.py                  # GE 1.x orchestrator — from DataClean (Phase 3)
│   │   ├── checks.py               # SQL DQ checks — from DataClean (Phase 3)
│   │   ├── reporter.py              # (Phase 3)
│   │   └── suites/                  # Per-object expectations (Phase 3)
│   ├── trust/
│   │   ├── envelope.py              # TrustEnvelope — adapted from Jake ✅ DONE
│   │   ├── scorecard.py            # 6-dimension scorecard — from DataClean (Phase 3)
│   │   ├── certificate.py          # HMAC certificates — from DataClean (Phase 3)
│   │   ├── circuit_breaker.py      # Quarantine gate — from DataClean (Phase 3)
│   │   └── evidence_pack.py        # Audit bundles — from DataClean (Phase 3)
│   ├── semantic/
│   │   ├── metric_registry.py      # ~40 finance metrics — NEW (Phase 4)
│   │   ├── statement_templates.py  # P&L/BS hierarchy — NEW (Phase 4)
│   │   ├── account_classifier.py   # COA → template mapping — NEW (Phase 4)
│   │   ├── period_engine.py        # Configurable fiscal calendar — NEW (Phase 4)
│   │   └── kpi_engine.py           # Materialization engine — NEW (Phase 4)
│   ├── reconciliation/
│   │   ├── pipeline_recon.py       # 6-level recon — from DataClean (Phase 3)
│   │   ├── gl_subledger_recon.py   # GL ↔ AP/AR — inspired by Jake (Phase 3)
│   │   └── tb_gl_recon.py          # TB ↔ GL — NEW (Phase 3)
│   ├── workflows/
│   │   ├── event_bus.py            # Pub/sub — adapted from Jake (Phase 5)
│   │   ├── event_contracts.py      # Pydantic payloads (Phase 5)
│   │   ├── action_queue.py         # Governed actions (Phase 5)
│   │   ├── kill_switch.py          # Mutation control (Phase 5)
│   │   └── scheduler.py           # APScheduler (Phase 5)
│   ├── analysis/
│   │   ├── variance.py             # Budget vs actual — NEW (Phase 5)
│   │   ├── cash_flow.py            # Cash position — NEW (Phase 5)
│   │   ├── margin.py               # Margin by entity/dept/project — NEW (Phase 5)
│   │   ├── aging.py                # AR/AP aging — NEW (Phase 5)
│   │   ├── close_support.py        # Period close — NEW (Phase 5)
│   │   └── profitability.py        # Entity/dept P&L — NEW (Phase 5)
│   ├── api/
│   │   ├── routers/
│   │   │   ├── health.py           # /health, /health/deep ✅ DONE
│   │   │   ├── connections.py      # CRUD for Sage connections ✅ DONE
│   │   │   ├── sync.py             # Trigger/monitor sync ✅ DONE
│   │   │   ├── data.py             # GL, TB, AP, AR queries (Phase 2)
│   │   │   ├── quality.py          # DQ results, scorecards (Phase 3)
│   │   │   ├── semantic.py         # Metrics, KPIs (Phase 4)
│   │   │   ├── analysis.py         # Variance, aging (Phase 5)
│   │   │   ├── close.py            # Period close (Phase 5)
│   │   │   ├── cash.py             # Cash planning (Phase 5)
│   │   │   └── platform.py         # Data freshness (Phase 5)
│   │   ├── models/
│   │   │   └── responses.py        # StandardResponse envelope ✅ DONE
│   │   └── middleware/
│   │       ├── correlation.py       # (Phase 6)
│   │       ├── timing.py            # (Phase 6)
│   │       └── rate_limit.py        # (Phase 6)
│   └── observability/
│       ├── logging_config.py       # structlog config ✅ DONE
│       └── metrics.py              # Prometheus (Phase 6)
├── sql/migrations/
│   ├── 001_schemas.sql              # 6 schemas ✅ DONE
│   ├── 002_platform.sql             # tenants, runs, watermarks, connections ✅ DONE
│   ├── 003_staging.sql              # raw_records (immutable) ✅ DONE
│   ├── 004_contract.sql             # 17 canonical financial tables ✅ DONE
│   ├── 005_audit.sql                # transformation_log, evidence, dedup, certificates ✅ DONE
│   ├── 006_workflow.sql             # events, actions, kill_switch, schedules ✅ DONE
│   ├── 007_semantic.sql             # metric_definitions, templates, kpis (Phase 4)
│   ├── 008_indexes.sql              # Performance indexes (Phase 6)
│   └── 009_views.sql                # Materialized views (Phase 6)
├── ui/                               # Next.js 16 frontend (Phase 2+)
├── tests/
├── docker-compose.sage.yml           # PostgreSQL 16 + backend ✅ DONE
├── Dockerfile.sage                   # Python 3.11 slim ✅ DONE
├── pyproject.toml                    # Dependencies ✅ DONE
├── .env.sage.example                 # Environment template ✅ DONE
└── REBUILD_MASTER_PLAN.md            # This file
```

---

## D. Domain Model

### Platform Entities (system metadata)

| Entity | Purpose | Key Fields |
|--------|---------|------------|
| **Tenant** | Organizational boundary | tenant_id, slug, name, settings (JSONB) |
| **Connection** | Sage Intacct credentials | tenant_id, provider, credentials (encrypted JSONB), status |
| **DataRun** | One pipeline execution | run_id, tenant_id, source_type, mode, status (FSM), started_at, completed_at, summary, error_message |
| **RawAsset** | Ingested data batch | asset_id, run_id, object_type, row_count, source_checksum |
| **Watermark** | Per-object sync cursor | tenant_id, connection_id, object_name, last_value, last_sync_at |
| **DQResult** | Quality check result | run_id, object_name, check_name, passed, severity, details |
| **Settings** | Platform config | key, value (JSONB) |

### Financial Entities (contract schema — canonical data)

| Entity | Sage Intacct Source | Key Fields |
|--------|-------------------|------------|
| **Entity** | LOCATION | entity_code, entity_name, currency_code, fiscal_year_end |
| **Department** | DEPARTMENT | dept_code, dept_name, parent_dept, entity_id |
| **ChartOfAccounts** | GLACCOUNT | account_number, account_name, account_type (Asset/Liability/Equity/Revenue/Expense), normal_balance |
| **GLEntry** | GLDETAIL | posting_date, account_number, amount, debit/credit, dimension_1/2/3, fiscal_year/period |
| **TrialBalance** | TRIALBALANCE | as_of_date, account_number, beginning/ending balance, total debits/credits |
| **Vendor** | VENDOR | vendor_code, vendor_name, status, payment_terms, contact_email, address (JSONB) |
| **Customer** | CUSTOMER | customer_code, customer_name, status, credit_limit, payment_terms |
| **APInvoice** | APBILL | vendor_code, invoice_number, invoice_date, due_date, total/paid/balance, status |
| **APPayment** | APPAYMENT | vendor_code, payment_date, amount, method |
| **ARInvoice** | ARINVOICE | customer_code, invoice_number, invoice_date, due_date, total/paid/balance, status |
| **ARPayment** | ARPAYMENT | customer_code, payment_date, amount |
| **Project** | PROJECT | project_number, name, status, contract_amount, percent_complete, department_code |
| **JobCost** | — | project_id, cost_date, cost_type, amount, vendor_code |
| **Employee** | EMPLOYEE | employee_code, name, department_code, title, status |
| **BudgetLine** | — (CSV seed V1) | entity_id, dept_code, account_number, fiscal_year, period, budget_amount, scenario |
| **FiscalCalendar** | — | entity_id, fiscal_year, period_number, start/end date |

### Semantic Entities

| Entity | Purpose |
|--------|---------|
| **MetricDefinition** | Canonical KPI formula (SQL), category, unit, description |
| **StatementTemplate** | P&L or BS structure definition |
| **StatementTemplateLine** | Hierarchy node: sort_order, account_type_filter, sign_convention |
| **ComputedKPI** | Materialized metric value per entity/period |
| **PeriodStatus** | Fiscal period lifecycle: open → closing → closed → locked |

### Quality / Trust Entities

| Entity | Purpose |
|--------|---------|
| **ScoreCard** | 6-dimension composite score: accuracy (35%), completeness (20%), consistency (15%), validity (10%), uniqueness (10%), timeliness (10%) |
| **Certificate** | HMAC-SHA256 signed proof of data certification |
| **EvidencePack** | SOC-ready audit bundle |
| **TrustEnvelope** | Runtime API response metadata (not persisted): confidence, risk_level, certified_at, scorecard_score |

### Workflow Entities

| Entity | Purpose |
|--------|---------|
| **Event** | Pub/sub log: event_type, source, payload |
| **DeadLetter** | Failed event deliveries |
| **ActionRequest** | Governed action queue: risk_tier (green/yellow/red), status, idempotency_key |
| **KillSwitchRule** | Per-scope mutation control: mode (hard/soft) |
| **SyncSchedule** | Cron definitions for automated sync |

### Audit Entities (append-only, immutable triggers)

| Entity | Purpose |
|--------|---------|
| **TransformationLog** | Every transform applied to every row |
| **EvidenceLink** | Source → contract row mapping with SHA-256 checksums |
| **DedupLog** | Duplicate detection/resolution audit trail |
| **QuarantineLog** | Circuit breaker activation events |

---

## E. Database Schema

**6 PostgreSQL schemas** in a single database:

| Schema | Tables | Purpose |
|--------|--------|---------|
| `platform` | tenants, connections, data_runs, raw_assets, watermarks, dq_results, settings | System metadata |
| `staging` | raw_records | Immutable JSONB ingestion (triggers prevent UPDATE/DELETE) |
| `contract` | entity, department, chart_of_accounts, gl_entry, trial_balance, vendor, customer, ap_invoice, ap_payment, ar_invoice, ar_payment, project, job_cost, employee, budget_line, fiscal_calendar | Canonical financial data |
| `audit` | transformation_log, evidence_links, dedup_log, quarantine_log, scorecard_results, certificates | Append-only audit trail (immutable triggers) |
| `workflow` | events, dead_letters, action_requests, kill_switch_rules, kill_switch_log, sync_schedules | Orchestration |
| `semantic` | metric_definitions, statement_templates, statement_template_lines, statement_account_mappings, computed_kpis, period_status | Semantic layer (Phase 4) |

**Run status FSM** (enforced by CHECK constraint):
```
pending → extracting → profiling → mapping → staging → validating → certifying → promoting → complete
                                                                                              ↘ failed
                                                                                              ↘ quarantined
```

---

## F. Ingestion Architecture

### Sage Intacct Connector (from DataClean — copied as-is)

**7 supported objects:**

| Object | Canonical Target | Method | Incremental | Notes |
|--------|-----------------|--------|:-----------:|-------|
| GLDETAIL | gl_entry | readByQuery | ✅ WHENMODIFIED | Date-range chunking for full sync (12 monthly chunks) |
| GLACCOUNT | chart_of_accounts | readByQuery | ✅ WHENMODIFIED | |
| TRIALBALANCE | trial_balance | get_trialbalance | ❌ Full only | Legacy function, period-based |
| APBILL | ap_invoice | readByQuery | ✅ WHENMODIFIED | |
| ARINVOICE | ar_invoice | readByQuery | ✅ WHENMODIFIED | |
| VENDOR | vendor | readByQuery | ✅ WHENMODIFIED | |
| CUSTOMER | customer | readByQuery | ✅ WHENMODIFIED | |

**Authentication flow:**
1. DB vault lookup (`platform.connections` per tenant)
2. Fall back to constructor config dict
3. Fall back to `SAGE_INTACCT_*` environment variables
4. Acquire XML session via `getAPISession` (cached ~25 min)

**Extraction strategies:**
- **Standard** (VENDOR, CUSTOMER, APBILL, ARINVOICE, GLACCOUNT): `readByQuery` + `readMore` pagination, max 2000 per page
- **GLDETAIL**: Mandatory date-range filters to prevent Intacct view timeouts. Full sync = 12 monthly chunks. Incremental = WHENMODIFIED >= watermark
- **TRIALBALANCE**: Legacy `get_trialbalance` function, always full sync
- **Session recovery**: If session expires mid-pagination, stop cleanly — remaining records caught on next incremental sync

**Transform layer** (7 pure functions, no side effects):
- Each transformer maps Intacct UPPER_CASE fields to canonical snake_case
- Decimal math via Python `decimal.Decimal` (never float)
- `_debit_credit()` helper splits signed amounts: positive → debit, negative → credit
- Bad records skipped with warning log, never raise

---

## G. Data Pipeline

**4-stage pipeline** (adapted from DataClean's 7-stage):

```
STAGE 1: RAW (staging schema)
  ├── Connector extraction → raw_records JSONB
  ├── DuckDB profiling (column stats, null rates, cardinality)
  └── Source checksums computed

STAGE 2: NORMALIZED (contract schema)
  ├── YAML mapping template applied (sage_intacct_v2)
  ├── 16 transform rules executed (parse_date, parse_decimal, trim, etc.)
  ├── Evidence links written (source_row ↔ contract_row + SHA-256)
  ├── Entity auto-detection from LOCATIONID
  └── Dedup (SHA-256 content hash)

STAGE 3: VALIDATED (quality + reconciliation)
  ├── GE 1.x expectation suites per object
  ├── SQL DQ checks (TB balance, GL tie-out)
  ├── 6-level reconciliation
  ├── Scorecard computation (6-dimension weighted, 0-100)
  ├── Circuit breaker: quarantine if score < 98 or critical failures
  └── Certificate generation (HMAC-signed) if passed

STAGE 4: SEMANTIC (semantic schema)
  ├── Account classification (COA → Revenue/Expense/Asset/Liability/Equity)
  ├── Statement template mapping (GL accounts → P&L/BS lines)
  ├── KPI materialization (DSO, DPO, margins, ratios)
  ├── Period status management
  └── Event emission: sync.completed, quality.passed
```

**RunContext** from DataClean threads through all stages ensuring tenant isolation and run traceability.

---

## H. Quality & Trust Layer

### From DataClean (data trust):
- **GE 1.x Quality Gate**: declarative expectation suites per canonical object
- **6-Level Reconciliation**: row count, field completeness, checksum coverage, TB balance, FK integrity, enum validation
- **6-Dimension Scorecard**: Accuracy (35%), Completeness (20%), Consistency (15%), Validity (10%), Uniqueness (10%), Timeliness (10%)
- **Gate logic**: composite ≥ 98 AND accuracy == 100 → CERTIFIED; composite ≥ 98 → CONDITIONAL; else → FAILED
- **Circuit Breaker**: auto-quarantine failed runs, manual override with audit trail
- **HMAC-Signed Certificates**: tamper-evident proof of data certification
- **Evidence Packs**: SOC-ready bundles (transformation log, checksums, DQ results, recon summary)

### From Jake (operational trust):
- **TrustEnvelope**: attach confidence/risk metadata to every API response
- **Kill Switch**: global + per-module mutation control (hard block or soft warn)
- **Action Queue**: governed write-back with idempotency, risk tiers (GREEN auto, YELLOW confirm, RED require approval)

### Merged quality flow:
```
Pipeline completes → Quality Gate (GE + SQL)
    → Reconciliation (6-level)
    → Scorecard (0-100)
    → Circuit Breaker:
        CERTIFIED (≥98, accuracy 100%) → promote to semantic, issue certificate
        CONDITIONAL (≥98, accuracy <100%) → promote with warnings
        FAILED (<98 or critical) → quarantine, alert
    → All API responses include TrustEnvelope
```

---

## I. Semantic Layer

**New — neither legacy system fully provides this.**

| Component | Purpose | Source |
|-----------|---------|--------|
| **Metric Registry** | ~40 canonical KPI definitions with SQL formulas | NEW (categories: revenue, expense, profitability, liquidity, efficiency, leverage, aging) |
| **Statement Templates** | Configurable P&L and BS hierarchy | Inspired by Jake FSK, rebuilt clean |
| **Account Classifier** | Maps COA account_type to statement template lines | NEW |
| **Period Engine** | Configurable fiscal year end per entity (not hardcoded) | NEW |
| **KPI Engine** | Materialize metrics on sync completion, serve from `semantic.computed_kpis` | NEW |

---

## J. Workflow & Orchestration

### Event types (in-process pub/sub):
```
sync.started, sync.object.completed, sync.completed, sync.failed
quality.passed, quality.failed, quality.quarantined
period.closing, period.closed
kpi.refreshed
alert.data_stale
```

### Scheduled jobs (APScheduler):

| Job | Schedule | Description |
|-----|----------|-------------|
| sage_intacct_incremental_sync | Every 4 hours | Incremental sync (WHENMODIFIED watermarks) |
| sage_intacct_full_sync | Weekly Sunday 02:00 UTC | Full re-extract |
| kpi_refresh | After sync.completed | Recompute materialized KPIs |
| data_freshness_check | Every 30 minutes | Check watermark staleness |
| stale_run_cleanup | Daily 03:00 UTC | Mark stuck runs as failed |

---

## K. Dashboard / UI

**~12 pages for V1** (Next.js 16, shadcn/ui, SWR, Recharts):

```
/                         — Dashboard: sync status, freshness, scorecard, KPIs
/connections              — Sage Intacct setup + test
/sync                     — Sync runs, trigger manual sync
/data/gl                  — GL journal browser with dimension filtering
/data/trial-balance       — TB viewer with period selection
/data/ap                  — AP invoice list with aging
/data/ar                  — AR invoice list with aging
/quality                  — Scorecards, DQ results, certificates
/financials/pl            — Income statement with drill-down
/financials/bs            — Balance sheet with drill-down
/analysis/variance        — Budget vs actual
/analysis/aging           — AR/AP aging dashboard
/settings                 — Entities, departments, fiscal calendar, users
```

---

## L. MVP Boundaries

### V1 INCLUDES
- Sage Intacct connection setup + test (XML Web Services)
- Incremental + full sync for 7 objects
- Full 4-stage pipeline: raw → normalized → validated → semantic
- YAML mapping templates with 16 transforms
- Quality gate (GE 1.x + SQL checks)
- 6-level reconciliation + scorecard + certificates + circuit breaker
- P&L and Balance Sheet via statement templates
- GL explorer with dimension filtering
- AP/AR aging analysis
- Variance analysis (CSV budget seed)
- Data freshness monitoring
- Kill switch, event bus, scheduled sync
- TrustEnvelope on all API responses
- Single-tenant, JWT auth

### V1 EXCLUDES
- AI/LLM features (chat, anomaly detection, NLP queries)
- Multi-tenant SaaS (billing, plans, signup)
- Additional connectors (QBO, BC, NetSuite)
- Cash flow forecasting (scaffold only)
- SOX compliance, drift detection, Prefect
- SSO/SAML, evidence pack UI
- Department/Project/Employee Sage objects (V2)

### V2 ROADMAP
1. Department / Project / Employee ingestion
2. AI: anomaly detection (Z-scores), NLP queries
3. Cash flow forecasting (13-week)
4. SOX compliance controls
5. Drift detection + Slack alerts
6. Budget import from Sage Intacct
7. Multi-entity consolidation
8. Additional connectors

---

## M. Tech Stack Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **API DB** | asyncpg (async) | Proven in Jake, handles concurrent HTTP |
| **Pipeline DB** | psycopg2 (sync) | Sequential ETL, simpler to debug, proven in DataClean |
| **Bridge** | `asyncio.to_thread()` | Pipeline dispatched from async handlers |
| **ORM** | None (raw SQL) | Finance queries need CTEs + window functions; both legacy systems use raw SQL |
| **SQL safety** | `psycopg2.sql.Identifier` + `%s` params | From DataClean's injection-safe pattern |
| **Quality** | GE 1.x + SQL checks (layered) | GE for structural, SQL for cross-table |
| **Scheduler** | APScheduler (in-process) | 3-5 jobs; Prefect overkill for V1 |
| **Frontend** | Next.js 16, shadcn/ui, SWR | From DataClean's cleaner dashboard |
| **Migrations** | Numbered SQL files | Full control, auditable, no ORM dependency |
| **Database** | PostgreSQL 16, 6 schemas | Single DB, clean namespace separation |
| **Auth** | JWT + API key | From Jake, simplified |
| **Logging** | structlog | JSON output, correlation IDs |
| **XML parsing** | `xml.etree.ElementTree` | Stdlib, no extra dependency for Intacct XML |

---

## N. Build Sequence

### Phase 0: Skeleton ✅ COMPLETE
**Milestone**: All imports pass, JWT round-trip works, 6 migration files ready.

### Phase 1: Ingestion ✅ COMPLETE
**Milestone**: Sage Intacct connector (7 files), connection CRUD (5 endpoints), sync trigger (4 endpoints), transforms tested.

### Phase 2: Pipeline — NEXT
**Goal**: Full pipeline runs end-to-end; user browses canonical GL entries in API.
- Copy pipeline runner + steps from DataClean (adapt)
- Copy mapping engine + transforms
- Copy contract writers (GL, TB, AP, AR, vendor, customer, entity)
- Add new writers (department, project)
- Copy dedup engine + reconciliation
- `api/routers/data.py` — query GL, TB, AP, AR, vendors, customers
- Stage raw_records from connector output

### Phase 3: Quality + Trust
**Goal**: Pipeline produces scorecards; failures trigger quarantine.
- Copy quality gate + suites from DataClean
- Copy scorecard, certificate, circuit breaker, evidence packs
- `api/routers/quality.py`
- TrustEnvelope on all data responses

### Phase 4: Semantic Layer
**Goal**: Auto-generated P&L and Balance Sheet.
- `sql/migrations/007_semantic.sql`
- Build metric_registry, statement_templates, account_classifier, period_engine, kpi_engine
- `api/routers/semantic.py`

### Phase 5: Analysis + Workflows
**Goal**: Variance, aging, margins, close support, automated sync.
- Build analysis modules (variance, aging, margin, profitability, close_support)
- Adapt event bus, kill switch, scheduler from Jake
- `api/routers/analysis.py`, `close.py`
- Budget CSV upload

### Phase 6: Polish + Harden
**Goal**: Production-ready V1.
- Middleware (CORS ✅, rate limit, body size, correlation, timing)
- Data freshness monitoring
- Integration tests
- Next.js UI scaffold
- Documentation, deployment

---

## O. Implementation Status

| Phase | Status | Files Created | Key Endpoints |
|-------|--------|---------------|---------------|
| **0 — Skeleton** | ✅ Complete | 14 files | `GET /health`, `GET /health/deep` |
| **1 — Ingestion** | ✅ Complete | 10 files | `POST/GET/DELETE /v1/connections`, `POST /v1/connections/{id}/test`, `POST /v1/sync/trigger`, `GET /v1/sync/runs`, `GET /v1/sync/schema` |
| **2 — Pipeline** | 🔜 Next | — | `GET /v1/data/gl`, `GET /v1/data/tb`, etc. |
| **3 — Quality** | Pending | — | `GET /v1/quality/scorecards` |
| **4 — Semantic** | Pending | — | `GET /v1/financials/pl` |
| **5 — Analysis** | Pending | — | `GET /v1/analysis/variance` |
| **6 — Polish** | Pending | — | Middleware, tests, UI |

---

## P. File Inventory

### Created files (Phase 0 + Phase 1)

```
app/
├── __init__.py
├── main.py                              # FastAPI app factory, lifespan, CORS, error handlers
├── config.py                            # Pydantic Settings, production validation
├── core/
│   ├── __init__.py
│   ├── db.py                            # asyncpg pool (from Jake)
│   ├── db_sync.py                       # psycopg2 pool (from DataClean)
│   ├── deps.py                          # FastAPI DI: require_db, require_api_key
│   ├── errors.py                        # 12 exception classes (from Jake)
│   └── migration_runner.py              # SQL-file runner, tracks in platform.schema_migrations
├── auth/
│   ├── __init__.py
│   ├── tokens.py                        # JWT create/verify (HS256)
│   └── middleware.py                    # JWT + API key dual auth, dev passthrough
├── ingestion/
│   ├── __init__.py
│   └── connectors/
│       ├── __init__.py
│       ├── base.py                      # BaseConnector ABC (from DataClean)
│       └── sage_intacct/
│           ├── __init__.py              # exports SageIntacctConnector
│           ├── connector.py             # Main class: test, schema, extract (from DataClean)
│           ├── config.py                # SageIntacctConfig: env + DB vault (from DataClean)
│           ├── objects.py               # 7-object OBJECT_CATALOG (from DataClean)
│           ├── transport.py             # XMLTransport + RESTTransport (from DataClean)
│           └── transform.py             # 7 transformers + SAGE_TRANSFORMERS dispatch (from DataClean)
├── trust/
│   ├── __init__.py
│   └── envelope.py                      # TrustEnvelope ~80 LOC (adapted from Jake)
├── api/
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py                    # GET /health, GET /health/deep
│   │   ├── connections.py               # CRUD + test for Sage Intacct connections
│   │   └── sync.py                      # Trigger sync, list runs, get schema
│   ├── models/
│   │   ├── __init__.py
│   │   └── responses.py                 # StandardResponse[T], ResponseMetadata, wrap_response
│   └── middleware/
│       └── __init__.py
├── observability/
│   ├── __init__.py
│   └── logging_config.py               # structlog config (from Jake)
├── [empty module dirs with __init__.py]:
│   pipeline/, mapping/, contract/, quality/, semantic/,
│   reconciliation/, workflows/, analysis/

sql/migrations/
├── 001_schemas.sql                      # 6 schemas
├── 002_platform.sql                     # 7 platform tables + default tenant
├── 003_staging.sql                      # raw_records + immutable trigger
├── 004_contract.sql                     # 17 financial tables
├── 005_audit.sql                        # 6 audit tables + immutable triggers
└── 006_workflow.sql                     # 6 workflow tables + global kill switch

tests/
├── __init__.py
├── unit/__init__.py
└── integration/__init__.py

Root:
├── pyproject.toml                       # hatchling build, all dependencies
├── docker-compose.sage.yml              # PostgreSQL 16 + backend
├── Dockerfile.sage                      # Python 3.11 slim
├── .env.sage.example                    # Environment template
└── REBUILD_MASTER_PLAN.md               # This file
```

### Verification results

All imports pass. Tested:
- TrustEnvelope: confidence scoring, auto-review flagging, debit/credit splitting
- JWT: create → verify round-trip
- Config: Pydantic Settings with production validation
- Error hierarchy: exception → HTTP status code mapping
- Migration runner: finds all 6 SQL files in order
- Sage Intacct transforms: Decimal math, GLDETAIL→gl_entry, negative→credit
- Connector: inherits BaseConnector, source_type = "sage_intacct"
- Routers: 5 connection endpoints + 4 sync endpoints registered

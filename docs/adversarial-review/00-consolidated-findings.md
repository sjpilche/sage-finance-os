# Consolidated Findings — Prioritized Master List

## P0 — Immediate (1 finding)

### P0-1: Sage Intacct Credentials Stored as Plaintext JSON
- **Lens**: Skeptic
- **Files**: `app/api/routers/connections.py:71`, `sql/migrations/002_platform.sql`
- **Issue**: `sender_password` and `user_password` stored unencrypted in `platform.connections.credentials` JSONB column. Any database breach (backup leak, SQL injection, insider) exposes all Sage Intacct credentials.
- **Fix**: Encrypt credentials with Fernet or AES-256 before storage, decrypt on use. Add `CREDENTIAL_ENCRYPTION_KEY` to settings.

---

## P1 — Ship-blockers (6 findings)

### P1-1: Zero Auth Enforcement on All Endpoints
- **Lens**: Skeptic
- **Files**: All 8 routers in `app/api/routers/`. Auth middleware at `app/auth/middleware.py:26-43`
- **Issue**: `require_auth` dependency exists but is **never used** in any router. All endpoints use only `Depends(require_db)` which provides a database connection, not authentication. Every endpoint (including `POST /v1/sync/trigger`, `POST /v1/platform/kill-switch/activate`, `DELETE /v1/connections/{id}`) is accessible without credentials.
- **Fix**: Add `Depends(require_auth)` to every router or apply globally via middleware.

### P1-2: Missing Tenant Isolation in Data Endpoints
- **Lens**: Skeptic
- **Files**: `app/api/routers/data.py:149,269,296`
- **Issue**: `GET /v1/data/tb`, `GET /v1/data/vendors`, `GET /v1/data/customers` execute `SELECT count(*) FROM contract.X` and `SELECT ... FROM contract.X` with **zero WHERE clause** — no tenant_id filter. Returns all data across all tenants.
- **Fix**: Add `WHERE tenant_id = $1` to all queries. Pass tenant_id from request context.

### P1-3: SQL Injection via Column Name Interpolation
- **Lens**: Skeptic
- **File**: `app/analysis/profitability.py:38,49`
- **Issue**: `dimension` parameter is f-string interpolated directly into SQL: `g.{dimension}`. While the API router validates against a whitelist, the function itself accepts any string. A direct caller or future refactor bypassing validation enables injection like `dimension_1; DROP TABLE contract.gl_entry--`.
- **Fix**: Use a dict mapping validated dimension names to column names inside the function, not at the router level.

### P1-4: Pipeline Race Condition — No Concurrent Write Protection
- **Lens**: Architect
- **File**: `app/pipeline/runner.py:40-169`
- **Issue**: Two simultaneous sync triggers write to the same contract tables with no locking. Both read the same watermark, extract the same data, and write duplicates. The idempotency check uses `run_id` which differs per run, so duplicates are not caught.
- **Fix**: Add PostgreSQL advisory lock at pipeline start: `SELECT pg_advisory_lock(hashtext('pipeline_' || %s))` keyed on connection_id.

### P1-5: Default Certificate Signing Key Not Validated in Production
- **Lens**: Skeptic
- **File**: `app/trust/certificate.py:46`
- **Issue**: `CERT_SIGNING_KEY` defaults to `"dev-signing-key-change-in-production"` via `os.getenv()`. Unlike `API_KEY` and `JWT_SECRET_KEY`, this is **not checked** by `validate_production()`. An attacker knowing the default can forge HMAC certificates.
- **Fix**: Add `CERT_SIGNING_KEY` to the production validation check in `config.py:59-72`.

### P1-6: Dev Auth Passthrough Bypasses All Security
- **Lens**: Skeptic
- **File**: `app/auth/middleware.py:37-38`
- **Issue**: When `ENVIRONMENT != "production"`, any request without credentials gets `dev-user` identity. If Render is deployed with `ENVIRONMENT=staging` or the env var is missing, all auth is bypassed. Combined with P1-1 (auth not enforced), this is moot — but if auth is added, this remains a hole.
- **Fix**: Only allow passthrough when `ENVIRONMENT == "development"` explicitly (not just != production).

---

## P2 — Data Integrity (4 findings)

### P2-1: Pipeline Partial Write — No Transaction Rollback
- **Lens**: Architect
- **File**: `app/pipeline/runner.py:96-145`, `app/contract/writer.py:78-300`
- **Issue**: Each contract writer calls `conn.commit()` independently. If GL entries write successfully but vendor write fails, the run has partial data. The exception handler marks the run as "failed" but doesn't roll back committed writes.
- **Fix**: Wrap entire write_all() in a single transaction. Only commit after quality gate.

### P2-2: Missing Foreign Keys on Contract Tables
- **Lens**: Architect
- **File**: `sql/migrations/004_contract.sql`
- **Issue**: `ap_invoice.vendor_code` has no FK to `vendor.vendor_code`. `ar_invoice.customer_code` has no FK to `customer.customer_code`. `budget_line.account_number` has no FK to `chart_of_accounts`. Allows orphaned references.
- **Fix**: Add FK constraints or document as intentional (ETL loads may insert invoices before master data).

### P2-3: Missing Unique Constraints on Invoices
- **Lens**: Architect
- **File**: `sql/migrations/004_contract.sql`
- **Issue**: `ap_invoice` and `ar_invoice` have no unique constraint on `(tenant_id, vendor_code/customer_code, invoice_number)`. Same invoice can be inserted multiple times across different runs.
- **Fix**: Add unique constraint or handle dedup in writers.

### P2-4: Missing Foreign Keys on Audit Tables
- **Lens**: Architect
- **File**: `sql/migrations/005_audit.sql:6-65`
- **Issue**: `audit.scorecard_results.run_id`, `audit.quarantine_log.run_id` have no FK to `platform.data_runs`. Orphaned audit records possible if runs are deleted.
- **Fix**: Add FK with `ON DELETE CASCADE` or `ON DELETE SET NULL`.

---

## P3 — Security Hardening (5 findings)

### P3-1: /health/deep Leaks Database Error Details
- **Lens**: Skeptic
- **File**: `app/api/routers/health.py:42-43`
- **Issue**: `str(e)` from database exceptions returned to unauthenticated callers. May reveal DB type, version, connection info.
- **Fix**: Return `"unhealthy"` status without error detail. Log the error server-side.

### P3-2: No Connection Pool Timeout
- **Lens**: Architect
- **Files**: `app/core/db.py:43-49`, `app/core/db_sync.py:38-42`
- **Issue**: Neither pool has acquisition timeout. If all connections are in use, new requests block indefinitely. Can deadlock under load.
- **Fix**: Add `timeout=30` to asyncpg pool, `maxconn` with a waiting queue timeout for psycopg2.

### P3-3: Rate Limiting Per-IP Only, Not Per-API-Key
- **Lens**: Skeptic
- **File**: `app/api/middleware/rate_limit.py`
- **Issue**: Token bucket is keyed on client IP. A single API key behind a load balancer can make unlimited requests from different IPs.
- **Fix**: Rate limit by API key when auth is present, fallback to IP.

### P3-4: No CSRF Protection on Mutation Endpoints
- **Lens**: Skeptic
- **File**: All POST/DELETE endpoints
- **Issue**: No CSRF tokens on state-changing endpoints. If the frontend is on a different origin and auth uses cookies (it doesn't currently — JWT/API key only), CSRF is possible.
- **Fix**: Low priority since auth is header-based, but add SameSite cookie policy if session auth is ever added.

### P3-5: Stack Traces in Logs via exc_info=True
- **Lens**: Skeptic
- **File**: `app/api/routers/sync.py:97`, `app/pipeline/runner.py:157`
- **Issue**: `exc_info=True` logs full stack traces including file paths, DB schema, internal state.
- **Fix**: Use `exc_info=True` only in development. Conditionally set based on `DEBUG` setting.

---

## P4 — Dead Code & Over-engineering (4 findings)

### P4-1: Event Bus Has Zero Subscribers
- **Lens**: Minimalist
- **File**: `app/workflows/event_bus.py` (163 lines)
- **Issue**: 12 event types defined, full pub/sub with cascade protection and dead-letter handling. Only 1 event ever emitted (`alert.data_stale`). Zero handlers registered anywhere.
- **Fix**: Remove or add actual subscribers. Currently 163 lines of unused infrastructure.

### P4-2: Kill Switch Enforcement Never Called
- **Lens**: Minimalist
- **File**: `app/workflows/kill_switch.py`
- **Issue**: `check_kill_switch()` function exists but is never called in the pipeline or any write path. The API can activate/deactivate but it has no effect.
- **Fix**: Wire into pipeline runner or remove.

### P4-3: Three Database Tables Never Used
- **Lens**: Minimalist
- **Files**: `sql/migrations/003_staging.sql` (raw_records), `sql/migrations/006_workflow.sql` (action_requests, sync_schedules)
- **Issue**: Tables created with triggers and constraints but zero code references.
- **Fix**: Keep if planned for next phase, but document in code.

### P4-4: TrustEnvelope Never Instantiated
- **Lens**: Minimalist
- **File**: `app/trust/envelope.py` (96 lines)
- **Issue**: Only imported by tests. Never used in any API response or pipeline step.
- **Fix**: Wire into response middleware or remove.

---

## P5 — Operational & Consistency (4 findings)

### P5-1: Hardcoded "default" Tenant in All Routers
- **Lens**: Architect
- **Files**: `app/api/routers/sync.py:32`, `app/api/routers/analysis.py:28`, etc.
- **Issue**: `_DEFAULT_TENANT = "default"` hardcoded. Every request queries for this slug. No path to multi-tenancy.
- **Fix**: Acceptable for V1. Extract tenant from JWT claims when auth is wired up.

### P5-2: Duplicate Bulk-Insert Pattern in Contract Writer
- **Lens**: Minimalist
- **File**: `app/contract/writer.py` (417 lines)
- **Issue**: 6 write functions with identical structure: check idempotent, build values list, execute_values, commit. ~60% of the file is copy-paste.
- **Fix**: Extract generic `_bulk_insert(conn, table, columns, records, transform_fn)` helper.

### P5-3: Frontend Type Definitions Unused
- **Lens**: Minimalist
- **File**: `ui/lib/types/data.ts`
- **Issue**: `Vendor`, `Customer`, `COAEntry` interfaces defined but never imported.
- **Fix**: Delete or use in vendor/customer/COA pages.

### P5-4: f-string SQL Pattern Across Codebase
- **Lens**: Architect
- **Files**: `app/api/routers/data.py`, `app/api/routers/semantic.py`, `app/api/routers/platform.py`, `app/analysis/profitability.py`, `app/analysis/variance.py`
- **Issue**: While WHERE clauses use parameterized values (`$N`), the clause structure itself is interpolated via f-strings. Safe today but fragile — any refactor that introduces user-controlled SQL fragments is an injection risk.
- **Fix**: Use a query builder pattern or explicit allowlists for dynamic SQL construction.

---

## Suggested Fix Order (Quick Wins First)

| Order | Finding | Effort | Impact |
|-------|---------|--------|--------|
| 1 | P1-1: Add auth to all endpoints | 30 min | Blocks all unauthenticated access |
| 2 | P1-2: Add tenant_id to TB/vendor/customer queries | 15 min | Fixes data leak |
| 3 | P1-5: Validate CERT_SIGNING_KEY in production | 5 min | Prevents certificate forgery |
| 4 | P3-1: Strip error detail from /health/deep | 5 min | Reduces info disclosure |
| 5 | P1-3: Whitelist dimension in function, not router | 10 min | Eliminates SQL injection vector |
| 6 | P0-1: Encrypt credentials at rest | 2 hours | Protects Sage Intacct access |
| 7 | P1-4: Add advisory lock to pipeline | 30 min | Prevents duplicate writes |
| 8 | P2-1: Transaction-wrap pipeline writes | 1 hour | Prevents partial data |
| 9 | P1-6: Tighten dev passthrough check | 5 min | Closes staging/test bypass |
| 10 | P3-2: Add pool timeouts | 15 min | Prevents deadlock |

---

## Aggregate Severity Counts

| Severity | Count |
|----------|-------|
| CRITICAL | 6 |
| HIGH | 8 |
| MEDIUM | 9 |
| LOW | 1 |
| **Total** | **24** |

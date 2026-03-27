# 02 — Data API Layer

## Findings: 2 CRITICAL, 1 HIGH, 1 MEDIUM

### CRITICAL: Missing Tenant Isolation on 3 Endpoints
- **Lens**: Skeptic
- **File**: `app/api/routers/data.py`
- **Lines**: 149 (TB count), 150-160 (TB rows), 269 (vendor count), 270-279 (vendor rows), 296 (customer count), 297-306 (customer rows)
- **Code**: `SELECT count(*) FROM contract.trial_balance` — no WHERE clause
- **Impact**: Returns all data across all tenants. Multi-tenant data breach.

### CRITICAL: f-string SQL WHERE Clause Interpolation
- **Lens**: Skeptic
- **File**: `app/api/routers/data.py`
- **Lines**: 112-127 (GL), 192-205 (AP), 238-251 (AR), 333-347 (COA)
- **Pattern**: `where = "WHERE " + " AND ".join(conditions)` then `f"SELECT ... {where}"`
- **Current risk**: LOW (conditions are hardcoded, values parameterized)
- **Future risk**: HIGH (any refactor adding user-controlled conditions enables injection)
- **Recommendation**: Use query builder or keep explicit allowlist

### HIGH: CSV Export Has No Row Limit
- **Lens**: Architect
- **File**: `app/api/routers/data.py:46-64` (`_rows_to_csv`)
- **Issue**: CSV export streams all matching rows. With `?format=csv&limit=5000`, an attacker can extract the entire GL in one request. No rate limiting on exports.
- **Recommendation**: Cap CSV export at reasonable limit, require auth.

### MEDIUM: Inconsistent Pagination Defaults
- **Lens**: Architect
- **Files**: Various endpoints in `data.py`
- **Issue**: GL defaults to limit=100, TB to limit=100, COA to limit=500. No consistency.
- **Recommendation**: Standardize to 100 across all data endpoints.

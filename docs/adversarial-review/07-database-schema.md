# 07 — Database Schema

## Findings: 0 CRITICAL, 2 HIGH, 2 MEDIUM

### HIGH: Missing Foreign Keys on Contract-to-Master Relationships
- **Lens**: Architect
- **File**: `sql/migrations/004_contract.sql`
- **Missing FKs**:
  - `ap_invoice.vendor_code` → no FK to `vendor.vendor_code`
  - `ar_invoice.customer_code` → no FK to `customer.customer_code`
  - `budget_line.account_number` → no FK to `chart_of_accounts.account_number`
  - `gl_entry.account_number` → no FK to `chart_of_accounts.account_number`
- **Impact**: Orphaned references possible. Invoices can reference non-existent vendors/customers.
- **Note**: This may be intentional for ETL — invoices may load before master data. If so, document it.

### HIGH: Missing Unique Constraints on Invoices
- **Lens**: Architect
- **File**: `sql/migrations/004_contract.sql`
- **Issue**: `ap_invoice` and `ar_invoice` have no unique constraint on `(tenant_id, invoice_number, vendor_code/customer_code)`. Same invoice can be inserted multiple times across runs.
- **Fix**: Add `UNIQUE (tenant_id, vendor_code, invoice_number)` or handle in writer with ON CONFLICT.

### MEDIUM: Missing Foreign Keys on Audit Tables
- **Lens**: Architect
- **File**: `sql/migrations/005_audit.sql`
- **Issue**: `scorecard_results.run_id`, `quarantine_log.run_id` have no FK to `platform.data_runs`. Orphaned audit records if runs are deleted.
- **Fix**: Add FKs or accept as intentional (audit should survive source deletion).

### MEDIUM: Nullable entity_id on Core Tables
- **Lens**: Architect
- **File**: `sql/migrations/004_contract.sql`
- **Issue**: `entity_id` is nullable on `gl_entry`, `trial_balance`, `ap_invoice`, `ar_invoice`. GROUP BY queries on entity will miss NULL rows.
- **Fix**: Acceptable for V1 single-entity. Add NOT NULL when multi-entity is implemented.

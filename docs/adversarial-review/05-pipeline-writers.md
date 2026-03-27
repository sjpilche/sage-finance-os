# 05 — Pipeline & Contract Writers

## Findings: 1 CRITICAL, 2 HIGH, 1 MEDIUM

### CRITICAL: No Concurrent Pipeline Protection
- **Lens**: Architect
- **File**: `app/pipeline/runner.py:40-169`
- **Issue**: No locking mechanism. Two sync triggers execute in parallel, both read same watermark, both write same data with different run_ids, bypassing idempotency checks (which are keyed on run_id).
- **Scenario**: User clicks "Trigger Sync" twice rapidly. Both pass. Both extract. Both write. Duplicate financial records.
- **Fix**: `SELECT pg_advisory_lock(hashtext(%s))` on connection_id at start of `run_pipeline()`.

### HIGH: Partial Write — Each Writer Commits Independently
- **Lens**: Architect
- **File**: `app/contract/writer.py:78-300`
- **Issue**: Each `write_*` function calls `conn.commit()` at the end. If `write_gl_entries()` succeeds but `write_vendors()` fails, the run has GL data but no vendor master. The pipeline exception handler marks the run as failed but doesn't roll back committed GL data.
- **Fix**: Remove per-writer commits. Have `write_all()` commit once at the end, or use savepoints.

### HIGH: Watermark Race Condition
- **Lens**: Architect
- **File**: `app/pipeline/runner.py:187-203`
- **Issue**: `_update_watermark()` uses `INSERT...ON CONFLICT...DO UPDATE`. If two pipelines run simultaneously, the last writer wins — potentially setting the watermark backward.
- **Fix**: Advisory lock (same as CRITICAL above) prevents this.

### MEDIUM: Writer Pattern Duplication
- **Lens**: Minimalist
- **File**: `app/contract/writer.py` (417 lines)
- **Issue**: 6 write functions with identical structure. ~250 lines of copy-paste that could be ~80 lines with a generic helper.
- **Fix**: Extract `_bulk_insert(conn, table, columns, records, row_transform)`.

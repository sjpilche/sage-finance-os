# 08 — Dead Code & Scaffolding

## Findings: 0 CRITICAL, 0 HIGH, 3 MEDIUM, 1 LOW

### MEDIUM: Event Bus — 163 Lines, Zero Subscribers
- **Lens**: Minimalist
- **File**: `app/workflows/event_bus.py`
- **Issue**: Full pub/sub with 12 event types, cascade protection, dead-letter handling. Only 1 event ever emitted (`alert.data_stale` in scheduler.py:132). Zero `@subscribe()` handlers anywhere.
- **Disposition**: Scaffolding for future use. Either wire up handlers or remove.

### MEDIUM: Kill Switch Enforcement Never Called
- **Lens**: Minimalist
- **File**: `app/workflows/kill_switch.py`
- **Issue**: `check_kill_switch()` exists but is never called in pipeline, writers, or any write path. The UI can toggle it but it has no effect on the system.
- **Disposition**: API works (activate/deactivate), enforcement missing. Wire into pipeline or document as UI-only.

### MEDIUM: Three Database Tables Never Referenced
- **Lens**: Minimalist
- **Files**: `sql/migrations/003_staging.sql` (raw_records), `sql/migrations/006_workflow.sql` (action_requests, sync_schedules)
- **Issue**: Created with full schemas, triggers, and constraints. Zero INSERTs, SELECTs, or references in any Python code.
- **Disposition**: Future-phase scaffolding. Pipeline comment confirms: "Staging will be added in a future phase."

### LOW: Unused TypeScript Interfaces
- **Lens**: Minimalist
- **File**: `ui/lib/types/data.ts`
- **Issue**: `Vendor`, `Customer`, `COAEntry` interfaces defined but never imported by any page.
- **Disposition**: Pages exist for these (data/ar, data/ap) but use inline types or don't type-check.

### What Went Well
- TrustEnvelope (envelope.py) is tested even though unused — good practice for future integration
- No orphaned UI components — all 24 are imported
- Config settings are all actually used — no dead configuration

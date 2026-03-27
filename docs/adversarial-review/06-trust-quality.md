# 06 — Trust & Quality System

## Findings: 0 CRITICAL, 1 HIGH, 1 MEDIUM

### HIGH: Certificate Signing Key Not Validated in Production
- **Lens**: Skeptic
- **File**: `app/trust/certificate.py:46`
- **Code**: `key = os.getenv("CERT_SIGNING_KEY", "dev-signing-key-change-in-production")`
- **Issue**: Unlike `API_KEY` and `JWT_SECRET_KEY`, `CERT_SIGNING_KEY` is NOT checked by `config.py:validate_production()`. A production deployment missing this env var uses the default, allowing certificate forgery.
- **Fix**: Add to `validate_production()` defaults dict, or move to Settings class.

### MEDIUM: Quality Gate Has No Rollback on Failure
- **Lens**: Architect
- **File**: `app/quality/gate.py:47-57`
- **Issue**: If `persist_scorecard()` succeeds but `quarantine_run()` fails, the scorecard is orphaned — written but the run isn't marked quarantined.
- **Fix**: Wrap gate operations in a transaction or add compensation logic.

### What Went Well
- 6-dimension weighted scorecard is well-designed with clear thresholds
- HMAC-SHA256 certificate signing/verification is correctly implemented
- Circuit breaker logic (`should_quarantine()`) has proper threshold handling
- Evidence hash is deterministic — same inputs always produce same hash
- Test coverage on scorecard, certificate, and circuit_breaker is solid (24 tests)

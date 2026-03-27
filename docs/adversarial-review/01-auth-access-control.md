# 01 — Auth & Access Control

## Findings: 1 CRITICAL, 1 HIGH

### CRITICAL: Auth Middleware Exists But Never Enforced
- **Lens**: Skeptic
- **File**: `app/auth/middleware.py:26-43` (defines `require_auth`)
- **All routers**: Use `Depends(require_db)` only — zero use of `require_auth`
- **Impact**: Every endpoint is publicly accessible. Financial data, connection management, kill switch, period close — all open.
- **Verified**: Searched all 8 router files — `require_auth` is imported nowhere.

### HIGH: Dev Passthrough Too Broad
- **Lens**: Skeptic
- **File**: `app/auth/middleware.py:37-38`
- **Code**: `if settings.ENVIRONMENT == "development" and not credentials and not x_api_key`
- **Issue**: Any non-"development" environment (staging, test, local, empty string) gets real auth. But combined with P1-1, this is moot — auth isn't called at all.
- **Recommendation**: When auth is wired up, change to explicit `== "development"` only.

# 04 — Credential & Connection Management

## Findings: 1 CRITICAL, 1 HIGH

### CRITICAL: Plaintext Credential Storage
- **Lens**: Skeptic
- **File**: `app/api/routers/connections.py:71`
- **Code**: `json.dumps(body.credentials)` stored directly in `platform.connections.credentials` JSONB
- **What's stored**: `sender_id`, `sender_password`, `company_id`, `user_id`, `user_password`
- **Impact**: Database compromise = all Sage Intacct credentials exposed
- **Retrieval**: `app/api/routers/sync.py:77` reads `json.loads(conn_row["credentials"])` — no decryption
- **Partial mitigation**: GET endpoint at `connections.py:133-135` redacts passwords client-side
- **Fix**: Encrypt with Fernet before INSERT, decrypt on use. Store encryption key in env var.

### HIGH: Credential Access Not Audited
- **Lens**: Skeptic
- **Files**: `app/api/routers/connections.py:149-156`, `app/api/routers/sync.py:77`
- **Issue**: No audit log when credentials are read from DB. If auth is added, there's no way to trace who accessed credentials and when.
- **Fix**: Log credential access events to `workflow.events` table.

-- ============================================================
-- 006 — Workflow tables (events, actions, kill switch)
-- ============================================================

-- ── Events (pub/sub event log) ───────────────────────────────
CREATE TABLE IF NOT EXISTS workflow.events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      TEXT NOT NULL,
    source          TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_type ON workflow.events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_time ON workflow.events (created_at);

-- ── Dead Letters (failed event deliveries) ───────────────────
CREATE TABLE IF NOT EXISTS workflow.dead_letters (
    dead_letter_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES workflow.events (event_id),
    handler         TEXT NOT NULL,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Action Requests (governed action queue) ──────────────────
CREATE TABLE IF NOT EXISTS workflow.action_requests (
    action_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type     TEXT NOT NULL,
    risk_tier       TEXT NOT NULL DEFAULT 'green',
    status          TEXT NOT NULL DEFAULT 'pending',
    payload         JSONB NOT NULL DEFAULT '{}',
    result          JSONB,
    idempotency_key TEXT UNIQUE,
    requested_by    TEXT,
    approved_by     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ,

    CONSTRAINT action_risk_check CHECK (risk_tier IN ('green', 'yellow', 'red')),
    CONSTRAINT action_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'executed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_action_status ON workflow.action_requests (status);

-- ── Kill Switch Rules ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workflow.kill_switch_rules (
    rule_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope           TEXT NOT NULL DEFAULT 'global',  -- 'global' or module name
    mode            TEXT NOT NULL DEFAULT 'hard',     -- 'hard' = block, 'soft' = warn
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    activated_by    TEXT,
    reason          TEXT,
    activated_at    TIMESTAMPTZ,
    deactivated_at  TIMESTAMPTZ,

    CONSTRAINT ks_mode_check CHECK (mode IN ('hard', 'soft')),
    CONSTRAINT ks_scope_unique UNIQUE (scope)
);

-- Seed global kill switch rule (inactive by default)
INSERT INTO workflow.kill_switch_rules (scope, mode, is_active)
VALUES ('global', 'hard', FALSE)
ON CONFLICT (scope) DO NOTHING;

-- ── Kill Switch Audit Log ────────────────────────────────────
CREATE TABLE IF NOT EXISTS workflow.kill_switch_log (
    log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope           TEXT NOT NULL,
    action          TEXT NOT NULL,       -- 'activated', 'deactivated'
    actor           TEXT,
    reason          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Sync Schedules ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workflow.sync_schedules (
    schedule_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    connection_id   UUID,
    object_scope    TEXT NOT NULL DEFAULT '*',  -- '*' for all, or specific object name
    cron_expression TEXT NOT NULL DEFAULT '0 */4 * * *',  -- every 4 hours
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at     TIMESTAMPTZ,
    next_run_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 005 — Audit tables (append-only, tamper-resistant)
-- ============================================================

-- ── Transformation Log ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit.transformation_log (
    log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    source_table    TEXT NOT NULL,
    source_row_id   TEXT,
    target_table    TEXT NOT NULL,
    target_row_id   TEXT,
    transform_name  TEXT NOT NULL,
    before_value    TEXT,
    after_value     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tlog_run ON audit.transformation_log (run_id);

-- ── Evidence Links (source → contract row mapping) ───────────
CREATE TABLE IF NOT EXISTS audit.evidence_links (
    evidence_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    source_table    TEXT NOT NULL,
    source_row_id   TEXT NOT NULL,
    target_table    TEXT NOT NULL,
    target_row_id   TEXT NOT NULL,
    source_checksum TEXT,
    target_checksum TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_run    ON audit.evidence_links (run_id);
CREATE INDEX IF NOT EXISTS idx_evidence_target ON audit.evidence_links (target_table, target_row_id);

-- ── Dedup Log ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit.dedup_log (
    dedup_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    table_name      TEXT NOT NULL,
    kept_row_id     TEXT NOT NULL,
    removed_row_id  TEXT NOT NULL,
    dedup_key       TEXT,
    reason          TEXT NOT NULL DEFAULT 'content_hash_match',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dedup_run ON audit.dedup_log (run_id);

-- ── Quarantine Log ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit.quarantine_log (
    quarantine_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    reason          TEXT NOT NULL,
    scorecard_score NUMERIC(5,2),
    resolved_at     TIMESTAMPTZ,
    resolved_by     TEXT,
    resolution_note TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quarantine_run ON audit.quarantine_log (run_id);

-- ── Scorecard Results ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit.scorecard_results (
    scorecard_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    accuracy        NUMERIC(5,2) NOT NULL DEFAULT 0,
    completeness    NUMERIC(5,2) NOT NULL DEFAULT 0,
    consistency     NUMERIC(5,2) NOT NULL DEFAULT 0,
    validity        NUMERIC(5,2) NOT NULL DEFAULT 0,
    uniqueness      NUMERIC(5,2) NOT NULL DEFAULT 0,
    timeliness      NUMERIC(5,2) NOT NULL DEFAULT 0,
    composite       NUMERIC(5,2) NOT NULL DEFAULT 0,
    gate_status     TEXT NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT gate_status_check CHECK (gate_status IN ('pending', 'certified', 'conditional', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_scorecard_run ON audit.scorecard_results (run_id);

-- ── Certificates ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit.certificates (
    certificate_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    signature       TEXT NOT NULL,       -- HMAC-SHA256
    scorecard_snapshot JSONB NOT NULL,
    issued_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cert_run ON audit.certificates (run_id);

-- Immutable triggers — prevent modification of audit records
DO $$
BEGIN
    -- Transformation log immutable trigger
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_tlog_immutable'
    ) THEN
        CREATE OR REPLACE FUNCTION audit.prevent_audit_update()
        RETURNS TRIGGER AS $fn$
        BEGIN
            RAISE EXCEPTION 'audit records are immutable — updates and deletes not allowed';
            RETURN NULL;
        END;
        $fn$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_tlog_immutable
            BEFORE UPDATE OR DELETE ON audit.transformation_log
            FOR EACH ROW EXECUTE FUNCTION audit.prevent_audit_update();

        CREATE TRIGGER trg_evidence_immutable
            BEFORE UPDATE OR DELETE ON audit.evidence_links
            FOR EACH ROW EXECUTE FUNCTION audit.prevent_audit_update();

        CREATE TRIGGER trg_dedup_immutable
            BEFORE UPDATE OR DELETE ON audit.dedup_log
            FOR EACH ROW EXECUTE FUNCTION audit.prevent_audit_update();

        CREATE TRIGGER trg_cert_immutable
            BEFORE UPDATE OR DELETE ON audit.certificates
            FOR EACH ROW EXECUTE FUNCTION audit.prevent_audit_update();
    END IF;
END $$;

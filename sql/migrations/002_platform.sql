-- ============================================================
-- 002 — Platform tables (system metadata)
-- ============================================================

-- ── Tenants ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS platform.tenants (
    tenant_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    settings        JSONB NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed a default tenant for single-tenant V1
INSERT INTO platform.tenants (slug, name)
VALUES ('default', 'Default Organization')
ON CONFLICT (slug) DO NOTHING;

-- ── Connections (Sage Intacct credentials) ──────────────────
CREATE TABLE IF NOT EXISTS platform.connections (
    connection_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    provider        TEXT NOT NULL DEFAULT 'sage_intacct',
    name            TEXT NOT NULL,
    credentials     JSONB NOT NULL DEFAULT '{}',  -- encrypted at app layer
    status          TEXT NOT NULL DEFAULT 'pending',
    last_tested_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT conn_status_check CHECK (status IN ('pending', 'active', 'failed', 'disabled'))
);

CREATE INDEX IF NOT EXISTS idx_conn_tenant ON platform.connections (tenant_id);

-- ── Data Runs (pipeline execution tracking) ─────────────────
CREATE TABLE IF NOT EXISTS platform.data_runs (
    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    connection_id   UUID REFERENCES platform.connections (connection_id),
    source_type     TEXT NOT NULL DEFAULT 'sage_intacct',
    mode            TEXT NOT NULL DEFAULT 'full',
    status          TEXT NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    summary         JSONB,
    error_message   TEXT,

    CONSTRAINT run_status_check CHECK (status IN (
        'pending', 'extracting', 'profiling', 'mapping', 'staging',
        'validating', 'certifying', 'promoting', 'complete', 'failed', 'quarantined'
    ))
);

CREATE INDEX IF NOT EXISTS idx_runs_tenant ON platform.data_runs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON platform.data_runs (status);

-- ── Raw Assets (ingested batch metadata) ────────────────────
CREATE TABLE IF NOT EXISTS platform.raw_assets (
    asset_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL REFERENCES platform.data_runs (run_id),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    object_type     TEXT NOT NULL,
    row_count       INT,
    source_checksum TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_assets_run ON platform.raw_assets (run_id);

-- ── Watermarks (incremental sync tracking) ──────────────────
CREATE TABLE IF NOT EXISTS platform.watermarks (
    watermark_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    connection_id   UUID REFERENCES platform.connections (connection_id),
    object_name     TEXT NOT NULL,
    last_value      TEXT,
    last_sync_at    TIMESTAMPTZ,
    row_count       INT,

    CONSTRAINT wm_unique UNIQUE (tenant_id, connection_id, object_name)
);

-- ── DQ Results (quality check results per run) ──────────────
CREATE TABLE IF NOT EXISTS platform.dq_results (
    result_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL REFERENCES platform.data_runs (run_id),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    object_name     TEXT NOT NULL,
    check_name      TEXT NOT NULL,
    passed          BOOLEAN NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'warning',
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT dq_severity_check CHECK (severity IN ('critical', 'warning', 'info'))
);

CREATE INDEX IF NOT EXISTS idx_dq_run ON platform.dq_results (run_id);

-- ── Settings (platform-level configuration) ─────────────────
CREATE TABLE IF NOT EXISTS platform.settings (
    key             TEXT PRIMARY KEY,
    value           JSONB NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

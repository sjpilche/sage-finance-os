-- ============================================================
-- 007 — Semantic layer tables
-- Metric definitions, statement templates, computed KPIs,
-- period status management.
-- ============================================================

-- ── Metric Definitions ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS semantic.metric_definitions (
    metric_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE,
    display_name    TEXT NOT NULL,
    description     TEXT,
    formula_sql     TEXT,            -- SQL expression for computation
    category        TEXT NOT NULL,   -- revenue, expense, profitability, liquidity, efficiency, leverage, aging
    unit            TEXT NOT NULL DEFAULT 'currency',  -- currency, percentage, days, ratio, count
    direction       TEXT NOT NULL DEFAULT 'neutral',   -- higher_better, lower_better, neutral
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Statement Templates ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS semantic.statement_templates (
    template_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name   TEXT NOT NULL UNIQUE,  -- 'income_statement', 'balance_sheet'
    display_name    TEXT NOT NULL,
    version         INT NOT NULL DEFAULT 1,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed default templates
INSERT INTO semantic.statement_templates (template_name, display_name)
VALUES
    ('income_statement', 'Income Statement'),
    ('balance_sheet', 'Balance Sheet')
ON CONFLICT (template_name) DO NOTHING;

-- ── Statement Template Lines (hierarchy) ─────────────────────
CREATE TABLE IF NOT EXISTS semantic.statement_template_lines (
    line_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id         UUID NOT NULL REFERENCES semantic.statement_templates (template_id),
    line_key            TEXT NOT NULL,           -- e.g. 'revenue', 'cogs', 'gross_profit'
    display_name        TEXT NOT NULL,
    parent_line_key     TEXT,                    -- NULL = top-level
    sort_order          INT NOT NULL DEFAULT 0,
    line_type           TEXT NOT NULL DEFAULT 'detail',  -- 'header', 'detail', 'subtotal', 'total'
    sign_convention     INT NOT NULL DEFAULT 1,  -- 1 = normal, -1 = flip sign (e.g. expenses)
    account_type_filter TEXT,                    -- 'Revenue', 'Expense', etc. (maps to COA)
    is_calculated       BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = sum of children, not direct accounts
    formula             TEXT,                    -- e.g. 'revenue - cogs' for gross_profit

    CONSTRAINT stl_unique UNIQUE (template_id, line_key)
);

-- ── Statement Account Mappings (COA → template lines) ────────
CREATE TABLE IF NOT EXISTS semantic.statement_account_mappings (
    mapping_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id     UUID NOT NULL REFERENCES semantic.statement_templates (template_id),
    line_key        TEXT NOT NULL,
    account_number  TEXT NOT NULL,
    tenant_id       UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT sam_unique UNIQUE (template_id, account_number, tenant_id)
);

-- ── Computed KPIs (materialized metric values) ───────────────
CREATE TABLE IF NOT EXISTS semantic.computed_kpis (
    kpi_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    entity_id       UUID,
    metric_name     TEXT NOT NULL,
    fiscal_year     INT,
    fiscal_period   INT,
    value           NUMERIC(18,4),
    unit            TEXT NOT NULL DEFAULT 'currency',
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id          UUID,

    CONSTRAINT ckpi_unique UNIQUE (tenant_id, entity_id, metric_name, fiscal_year, fiscal_period)
);

CREATE INDEX IF NOT EXISTS idx_ckpi_tenant ON semantic.computed_kpis (tenant_id);
CREATE INDEX IF NOT EXISTS idx_ckpi_metric ON semantic.computed_kpis (metric_name);

-- ── Period Status (fiscal period lifecycle) ──────────────────
CREATE TABLE IF NOT EXISTS semantic.period_status (
    period_status_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    entity_id       UUID,
    fiscal_year     INT NOT NULL,
    fiscal_period   INT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open',
    closed_by       TEXT,
    closed_at       TIMESTAMPTZ,
    locked_by       TEXT,
    locked_at       TIMESTAMPTZ,

    CONSTRAINT ps_status_check CHECK (status IN ('open', 'closing', 'closed', 'locked')),
    CONSTRAINT ps_unique UNIQUE (tenant_id, entity_id, fiscal_year, fiscal_period)
);

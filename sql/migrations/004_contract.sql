-- ============================================================
-- 004 — Contract tables (canonical cleaned financial data)
-- Adapted from DataClean's 004_contract_tables.sql with
-- additions for department, project, employee, budget.
-- Every row links to source evidence via audit.evidence_links.
-- ============================================================

-- ── Entity / Company ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.entity (
    entity_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_code     TEXT NOT NULL,
    entity_name     TEXT NOT NULL,
    currency_code   TEXT NOT NULL DEFAULT 'USD',
    fiscal_year_end TEXT,           -- MM-DD, e.g. '12-31'
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT entity_unique UNIQUE (tenant_id, entity_code)
);

CREATE INDEX IF NOT EXISTS idx_entity_tenant ON contract.entity (tenant_id);

-- ── Fiscal Calendar ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.fiscal_calendar (
    calendar_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    entity_id       UUID NOT NULL REFERENCES contract.entity (entity_id),
    fiscal_year     INT NOT NULL,
    period_number   INT NOT NULL,
    period_name     TEXT NOT NULL,
    period_type     TEXT NOT NULL DEFAULT 'month',
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    is_closing_period BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_fiscal_tenant_entity
    ON contract.fiscal_calendar (tenant_id, entity_id);

-- ── Department ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.department (
    department_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    dept_code       TEXT NOT NULL,
    dept_name       TEXT NOT NULL,
    parent_dept     TEXT,
    manager_name    TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT dept_unique UNIQUE (tenant_id, entity_id, dept_code)
);

CREATE INDEX IF NOT EXISTS idx_dept_tenant ON contract.department (tenant_id);

-- ── Chart of Accounts ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.chart_of_accounts (
    coa_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    account_number  TEXT NOT NULL,
    account_name    TEXT NOT NULL,
    account_type    TEXT NOT NULL,
    normal_balance  TEXT NOT NULL DEFAULT 'debit',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    parent_account  TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT coa_valid_type CHECK (
        account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense', 'Other')
    ),
    CONSTRAINT coa_valid_balance CHECK (normal_balance IN ('debit', 'credit')),
    CONSTRAINT coa_unique UNIQUE (tenant_id, entity_id, account_number)
);

CREATE INDEX IF NOT EXISTS idx_coa_tenant ON contract.chart_of_accounts (tenant_id);

-- ── GL Entries ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.gl_entry (
    gl_entry_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    posting_date    DATE NOT NULL,
    document_number TEXT,
    description     TEXT,
    account_number  TEXT NOT NULL,
    amount          NUMERIC(18,2) NOT NULL,
    debit_amount    NUMERIC(18,2) NOT NULL DEFAULT 0,
    credit_amount   NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency_code   TEXT NOT NULL DEFAULT 'USD',
    dimension_1     TEXT,           -- Department
    dimension_2     TEXT,           -- Project / Location
    dimension_3     TEXT,           -- Class / Custom
    source_module   TEXT,
    is_reversing    BOOLEAN NOT NULL DEFAULT FALSE,
    fiscal_year     INT,
    fiscal_period   INT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gl_tenant      ON contract.gl_entry (tenant_id);
CREATE INDEX IF NOT EXISTS idx_gl_date        ON contract.gl_entry (posting_date);
CREATE INDEX IF NOT EXISTS idx_gl_account     ON contract.gl_entry (account_number);
CREATE INDEX IF NOT EXISTS idx_gl_run         ON contract.gl_entry (run_id);
CREATE INDEX IF NOT EXISTS idx_gl_entity_date ON contract.gl_entry (entity_id, posting_date);

-- ── Trial Balance ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.trial_balance (
    tb_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id              UUID REFERENCES platform.data_runs (run_id),
    entity_id           UUID REFERENCES contract.entity (entity_id),
    as_of_date          DATE NOT NULL,
    account_number      TEXT NOT NULL,
    account_name        TEXT,
    beginning_balance   NUMERIC(18,2) NOT NULL DEFAULT 0,
    total_debits        NUMERIC(18,2) NOT NULL DEFAULT 0,
    total_credits       NUMERIC(18,2) NOT NULL DEFAULT 0,
    ending_balance      NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency_code       TEXT NOT NULL DEFAULT 'USD',
    metadata            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT tb_unique UNIQUE (tenant_id, run_id, entity_id, as_of_date, account_number)
);

CREATE INDEX IF NOT EXISTS idx_tb_tenant ON contract.trial_balance (tenant_id);
CREATE INDEX IF NOT EXISTS idx_tb_date   ON contract.trial_balance (as_of_date);

-- ── Vendors ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.vendor (
    vendor_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    vendor_code     TEXT NOT NULL,
    vendor_name     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    payment_terms   TEXT,
    contact_email   TEXT,
    address         JSONB,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT vendor_unique UNIQUE (tenant_id, vendor_code)
);

CREATE INDEX IF NOT EXISTS idx_vendor_tenant ON contract.vendor (tenant_id);

-- ── Customers ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.customer (
    customer_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    customer_code   TEXT NOT NULL,
    customer_name   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    credit_limit    NUMERIC(18,2),
    payment_terms   TEXT,
    contact_email   TEXT,
    address         JSONB,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT customer_unique UNIQUE (tenant_id, customer_code)
);

CREATE INDEX IF NOT EXISTS idx_customer_tenant ON contract.customer (tenant_id);

-- ── AP Invoices ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.ap_invoice (
    ap_invoice_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    vendor_code     TEXT NOT NULL,
    invoice_number  TEXT NOT NULL,
    invoice_date    DATE NOT NULL,
    due_date        DATE,
    total_amount    NUMERIC(18,2) NOT NULL,
    paid_amount     NUMERIC(18,2) NOT NULL DEFAULT 0,
    balance         NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency_code   TEXT NOT NULL DEFAULT 'USD',
    status          TEXT NOT NULL DEFAULT 'open',
    description     TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ap_status_check CHECK (status IN ('open', 'partial', 'paid', 'void'))
);

CREATE INDEX IF NOT EXISTS idx_ap_tenant ON contract.ap_invoice (tenant_id);
CREATE INDEX IF NOT EXISTS idx_ap_vendor ON contract.ap_invoice (vendor_code);
CREATE INDEX IF NOT EXISTS idx_ap_due    ON contract.ap_invoice (due_date);

-- ── AP Payments ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.ap_payment (
    ap_payment_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    vendor_code     TEXT NOT NULL,
    payment_date    DATE NOT NULL,
    amount          NUMERIC(18,2) NOT NULL,
    payment_method  TEXT,
    reference       TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ap_pmt_tenant ON contract.ap_payment (tenant_id);

-- ── AR Invoices ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.ar_invoice (
    ar_invoice_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    customer_code   TEXT NOT NULL,
    invoice_number  TEXT NOT NULL,
    invoice_date    DATE NOT NULL,
    due_date        DATE,
    total_amount    NUMERIC(18,2) NOT NULL,
    paid_amount     NUMERIC(18,2) NOT NULL DEFAULT 0,
    balance         NUMERIC(18,2) NOT NULL DEFAULT 0,
    currency_code   TEXT NOT NULL DEFAULT 'USD',
    status          TEXT NOT NULL DEFAULT 'open',
    description     TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ar_status_check CHECK (status IN ('open', 'partial', 'paid', 'void'))
);

CREATE INDEX IF NOT EXISTS idx_ar_tenant   ON contract.ar_invoice (tenant_id);
CREATE INDEX IF NOT EXISTS idx_ar_customer ON contract.ar_invoice (customer_code);
CREATE INDEX IF NOT EXISTS idx_ar_due      ON contract.ar_invoice (due_date);

-- ── AR Payments ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.ar_payment (
    ar_payment_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    customer_code   TEXT NOT NULL,
    payment_date    DATE NOT NULL,
    amount          NUMERIC(18,2) NOT NULL,
    payment_method  TEXT,
    reference       TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ar_pmt_tenant ON contract.ar_payment (tenant_id);

-- ── Projects / Jobs ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.project (
    project_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    project_number  TEXT NOT NULL,
    project_name    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    start_date      DATE,
    end_date        DATE,
    contract_amount NUMERIC(18,2),
    percent_complete NUMERIC(5,2),
    project_type    TEXT,
    manager_name    TEXT,
    department_code TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT project_unique UNIQUE (tenant_id, project_number)
);

CREATE INDEX IF NOT EXISTS idx_project_tenant ON contract.project (tenant_id);

-- ── Job Costs ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.job_cost (
    job_cost_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    project_id      UUID REFERENCES contract.project (project_id),
    cost_date       DATE NOT NULL,
    cost_type       TEXT NOT NULL,       -- labor, material, subcontract, equipment, overhead
    account_number  TEXT,
    description     TEXT,
    amount          NUMERIC(18,2) NOT NULL,
    quantity        NUMERIC(18,4),
    unit_cost       NUMERIC(18,4),
    vendor_code     TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jc_tenant  ON contract.job_cost (tenant_id);
CREATE INDEX IF NOT EXISTS idx_jc_project ON contract.job_cost (project_id);

-- ── Employees ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.employee (
    employee_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    employee_code   TEXT NOT NULL,
    employee_name   TEXT NOT NULL,
    department_code TEXT,
    title           TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT employee_unique UNIQUE (tenant_id, employee_code)
);

CREATE INDEX IF NOT EXISTS idx_emp_tenant ON contract.employee (tenant_id);

-- ── Budget Lines ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contract.budget_line (
    budget_line_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES platform.tenants (tenant_id),
    run_id          UUID REFERENCES platform.data_runs (run_id),
    entity_id       UUID REFERENCES contract.entity (entity_id),
    department_code TEXT,
    account_number  TEXT NOT NULL,
    fiscal_year     INT NOT NULL,
    fiscal_period   INT NOT NULL,
    budget_amount   NUMERIC(18,2) NOT NULL DEFAULT 0,
    scenario        TEXT NOT NULL DEFAULT 'base',  -- base, optimistic, conservative
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT budget_unique UNIQUE (
        tenant_id, entity_id, department_code, account_number,
        fiscal_year, fiscal_period, scenario
    )
);

CREATE INDEX IF NOT EXISTS idx_budget_tenant ON contract.budget_line (tenant_id);
CREATE INDEX IF NOT EXISTS idx_budget_period ON contract.budget_line (fiscal_year, fiscal_period);

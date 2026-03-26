-- ============================================================
-- 001 — Create schemas for Sage Finance OS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS platform;    -- System metadata: tenants, runs, watermarks, connections
CREATE SCHEMA IF NOT EXISTS staging;     -- Immutable raw records (JSONB) from ingestion
CREATE SCHEMA IF NOT EXISTS contract;    -- Canonical cleaned/validated financial data
CREATE SCHEMA IF NOT EXISTS semantic;    -- Metric definitions, statement templates, KPIs
CREATE SCHEMA IF NOT EXISTS audit;       -- Transformation log, evidence links (append-only)
CREATE SCHEMA IF NOT EXISTS workflow;    -- Events, actions, kill switch

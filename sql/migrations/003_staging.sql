-- ============================================================
-- 003 — Staging tables (immutable raw records)
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.raw_records (
    raw_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    asset_id        UUID NOT NULL,
    row_number      INT NOT NULL,
    data            JSONB NOT NULL,
    source_checksum TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_raw_run    ON staging.raw_records (run_id);
CREATE INDEX IF NOT EXISTS idx_raw_asset  ON staging.raw_records (asset_id);
CREATE INDEX IF NOT EXISTS idx_raw_tenant ON staging.raw_records (tenant_id);

-- Prevent modification of raw records after insertion
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_raw_records_immutable'
    ) THEN
        CREATE OR REPLACE FUNCTION staging.prevent_raw_update()
        RETURNS TRIGGER AS $fn$
        BEGIN
            RAISE EXCEPTION 'raw_records are immutable — updates and deletes are not allowed';
            RETURN NULL;
        END;
        $fn$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_raw_records_immutable
            BEFORE UPDATE OR DELETE ON staging.raw_records
            FOR EACH ROW
            EXECUTE FUNCTION staging.prevent_raw_update();
    END IF;
END $$;

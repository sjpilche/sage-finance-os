export interface Connection {
  connection_id: string;
  provider: "sage_intacct";
  name: string;
  status: "pending" | "active" | "failed" | "disabled";
  credentials?: Record<string, string>;
  last_tested_at: string | null;
  created_at: string;
}

export interface SyncRun {
  run_id: string;
  connection_id: string | null;
  source_type: string;
  mode: "full" | "incremental";
  status: "pending" | "extracting" | "profiling" | "mapping" | "staging" | "validating" | "certifying" | "promoting" | "complete" | "failed" | "quarantined";
  started_at: string;
  completed_at: string | null;
  summary: Record<string, unknown> | null;
  error_message: string | null;
}

export interface FreshnessObject {
  object_name: string;
  last_sync_at: string | null;
  hours_since_sync: number | null;
  is_stale: boolean;
  row_count: number;
}

export interface FreshnessResponse {
  last_sync: string | null;
  objects: FreshnessObject[];
}

export interface KillSwitchRule {
  scope: string;
  mode: "hard" | "soft";
  is_active: boolean;
  activated_by: string;
  reason: string;
  activated_at: string | null;
  deactivated_at: string | null;
}

export interface PlatformEvent {
  event_id: string;
  event_type: string;
  source: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface CloseCheckItem {
  check: string;
  display: string;
  passed: boolean;
  details: Record<string, unknown>;
}

export interface CloseChecklist {
  fiscal_year: number;
  fiscal_period: number;
  ready_to_close: boolean;
  passed: number;
  total: number;
  readiness_pct: number;
  checks: CloseCheckItem[];
}

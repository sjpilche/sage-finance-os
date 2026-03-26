export interface Scorecard {
  scorecard_id: string;
  run_id: string;
  tenant_id: string;
  accuracy: number;
  completeness: number;
  consistency: number;
  validity: number;
  uniqueness: number;
  timeliness: number;
  composite: number;
  gate_status: "pending" | "certified" | "conditional" | "failed";
  created_at: string;
}

export interface DQCheck {
  result_id: string;
  object_name: string;
  check_name: string;
  passed: boolean;
  severity: "critical" | "high" | "medium" | "low";
  details: Record<string, unknown>;
  created_at: string;
}

export interface DQChecksResponse {
  run_id: string;
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  checks: DQCheck[];
}

export interface Certificate {
  certificate_id: string;
  run_id: string;
  tenant_id: string;
  signature: string;
  scorecard_snapshot: Record<string, number>;
  issued_at: string;
}

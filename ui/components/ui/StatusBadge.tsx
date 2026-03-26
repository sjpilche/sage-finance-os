import { Badge } from "./Badge";

type RunStatus =
  | "pending" | "extracting" | "profiling" | "mapping" | "staging"
  | "validating" | "certifying" | "promoting" | "complete" | "failed" | "quarantined";

const statusConfig: Record<RunStatus, { label: string; variant: "default" | "success" | "warning" | "danger" | "info" }> = {
  pending: { label: "Pending", variant: "default" },
  extracting: { label: "Extracting", variant: "info" },
  profiling: { label: "Profiling", variant: "info" },
  mapping: { label: "Mapping", variant: "info" },
  staging: { label: "Staging", variant: "info" },
  validating: { label: "Validating", variant: "info" },
  certifying: { label: "Certifying", variant: "info" },
  promoting: { label: "Promoting", variant: "info" },
  complete: { label: "Complete", variant: "success" },
  failed: { label: "Failed", variant: "danger" },
  quarantined: { label: "Quarantined", variant: "warning" },
};

export function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status as RunStatus] || { label: status, variant: "default" as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

export interface AgingBucket {
  label: string;
  count: number;
  amount: number;
}

export interface AgingResult {
  type: "ar" | "ap";
  buckets: AgingBucket[];
  total_count: number;
  total_amount: number;
}

export interface ARAgingByCustomer {
  customer_code: string;
  customer_name: string;
  invoice_count: number;
  total_balance: number;
  oldest_due_date?: string;
  max_days_outstanding: number;
}

export interface VarianceDetail {
  account_number: string;
  account_name: string;
  account_type: string;
  budget: number;
  actual: number;
  variance: number;
  variance_pct: number;
  is_flagged: boolean;
  direction: "favorable" | "unfavorable" | "on_budget";
}

export interface VarianceSummary {
  total_budget: number;
  total_actual: number;
  total_variance: number;
  accounts_analyzed: number;
  accounts_flagged: number;
}

export interface VarianceReport {
  fiscal_year: number;
  fiscal_period?: number;
  threshold_pct: number;
  summary: VarianceSummary;
  details: VarianceDetail[];
}

export interface ProfitabilitySegment {
  dimension_value: string;
  revenue: number;
  expenses: number;
  net_income: number;
  margin_pct: number;
}

export interface ProfitabilitySummary {
  total_revenue: number;
  total_expenses: number;
  total_net_income: number;
  total_margin_pct: number;
  segment_count: number;
}

export interface ProfitabilityReport {
  fiscal_year: number;
  fiscal_period?: number;
  dimension: string;
  summary: ProfitabilitySummary;
  segments: ProfitabilitySegment[];
}

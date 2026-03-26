export interface StatementLine {
  line_key: string;
  display_name: string;
  line_type: "header" | "detail" | "subtotal" | "total";
  parent_key: string | null;
  sort_order: number;
  amount: number;
}

export interface IncomeStatementResponse {
  statement: "income_statement";
  fiscal_year: number;
  fiscal_period?: number;
  lines: StatementLine[];
}

export interface BalanceSheetResponse {
  statement: "balance_sheet";
  fiscal_year: number;
  sections: Record<string, number>;
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
}

export interface MetricDefinition {
  name: string;
  display_name: string;
  description: string;
  unit: "currency" | "percentage" | "days" | "ratio" | "count";
  direction: "higher_better" | "lower_better" | "neutral";
}

export interface KPI {
  metric_name: string;
  display_name: string;
  category: string;
  direction: string;
  fiscal_year: number;
  fiscal_period: number;
  value: number | null;
  unit: string;
  computed_at: string;
}

export interface PeriodStatus {
  fiscal_year: number;
  fiscal_period: number;
  status: "open" | "closing" | "closed" | "locked";
  closed_by?: string;
  closed_at?: string;
}

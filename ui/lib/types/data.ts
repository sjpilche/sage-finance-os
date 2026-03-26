export interface GLEntry {
  gl_entry_id: string;
  posting_date: string;
  document_number: string;
  description: string;
  account_number: string;
  amount: number;
  debit_amount: number;
  credit_amount: number;
  currency_code: string;
  dimension_1?: string;
  dimension_2?: string;
  dimension_3?: string;
  source_module: string;
  fiscal_year: number;
  fiscal_period: number;
  created_at: string;
}

export interface TrialBalanceRow {
  tb_id: string;
  as_of_date: string;
  account_number: string;
  account_name: string;
  beginning_balance: number;
  total_debits: number;
  total_credits: number;
  ending_balance: number;
  currency_code: string;
  created_at: string;
}

export interface APInvoice {
  ap_invoice_id: string;
  vendor_code: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string | null;
  total_amount: number;
  paid_amount: number;
  balance: number;
  currency_code: string;
  status: "open" | "partial" | "paid" | "void";
  description: string;
  created_at: string;
}

export interface ARInvoice {
  ar_invoice_id: string;
  customer_code: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string | null;
  total_amount: number;
  paid_amount: number;
  balance: number;
  currency_code: string;
  status: "open" | "partial" | "paid" | "void";
  description: string;
  created_at: string;
}

export interface Vendor {
  vendor_id: string;
  vendor_code: string;
  vendor_name: string;
  status: string;
  payment_terms: string;
  contact_email: string;
  created_at: string;
}

export interface Customer {
  customer_id: string;
  customer_code: string;
  customer_name: string;
  status: string;
  payment_terms: string;
  contact_email: string;
  credit_limit: number | null;
  created_at: string;
}

export interface COAEntry {
  coa_id: string;
  account_number: string;
  account_name: string;
  account_type: "Asset" | "Liability" | "Equity" | "Revenue" | "Expense" | "Other";
  normal_balance: "debit" | "credit";
  is_active: boolean;
  parent_account: string | null;
  created_at: string;
}

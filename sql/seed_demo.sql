-- Sage Finance OS — Demo Seed Data
-- Run after migrations to populate the database with realistic demo data.

-- Use the default tenant
DO $$
DECLARE
  t_id UUID;
BEGIN
  SELECT tenant_id INTO t_id FROM platform.tenants WHERE slug = 'default';

  -- ============================================================
  -- CHART OF ACCOUNTS (25 accounts)
  -- ============================================================
  INSERT INTO contract.chart_of_accounts (coa_id, tenant_id, account_number, account_name, account_type, normal_balance, is_active)
  VALUES
    -- Assets
    (gen_random_uuid(), t_id, '1000', 'Cash and Equivalents', 'Asset', 'debit', true),
    (gen_random_uuid(), t_id, '1100', 'Accounts Receivable', 'Asset', 'debit', true),
    (gen_random_uuid(), t_id, '1200', 'Inventory', 'Asset', 'debit', true),
    (gen_random_uuid(), t_id, '1300', 'Prepaid Expenses', 'Asset', 'debit', true),
    (gen_random_uuid(), t_id, '1500', 'Fixed Assets', 'Asset', 'debit', true),
    (gen_random_uuid(), t_id, '1510', 'Accumulated Depreciation', 'Asset', 'credit', true),
    -- Liabilities
    (gen_random_uuid(), t_id, '2000', 'Accounts Payable', 'Liability', 'credit', true),
    (gen_random_uuid(), t_id, '2100', 'Accrued Liabilities', 'Liability', 'credit', true),
    (gen_random_uuid(), t_id, '2200', 'Short-Term Debt', 'Liability', 'credit', true),
    (gen_random_uuid(), t_id, '2500', 'Long-Term Debt', 'Liability', 'credit', true),
    -- Equity
    (gen_random_uuid(), t_id, '3000', 'Common Stock', 'Equity', 'credit', true),
    (gen_random_uuid(), t_id, '3100', 'Retained Earnings', 'Equity', 'credit', true),
    -- Revenue
    (gen_random_uuid(), t_id, '4000', 'Product Revenue', 'Revenue', 'credit', true),
    (gen_random_uuid(), t_id, '4100', 'Service Revenue', 'Revenue', 'credit', true),
    (gen_random_uuid(), t_id, '4200', 'Interest Income', 'Revenue', 'credit', true),
    -- Expenses
    (gen_random_uuid(), t_id, '5000', 'Cost of Goods Sold', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6000', 'Payroll & Benefits', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6100', 'Rent & Facilities', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6200', 'Sales & Marketing', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6300', 'General & Administrative', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6400', 'Depreciation & Amortization', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6500', 'Software & Technology', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6600', 'Travel & Entertainment', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '6700', 'Professional Fees', 'Expense', 'debit', true),
    (gen_random_uuid(), t_id, '7000', 'Interest Expense', 'Expense', 'debit', true)
  ON CONFLICT (tenant_id, entity_id, account_number) DO NOTHING;

  -- ============================================================
  -- VENDORS (10)
  -- ============================================================
  INSERT INTO contract.vendor (vendor_id, tenant_id, vendor_code, vendor_name, status, payment_terms, contact_email)
  VALUES
    (gen_random_uuid(), t_id, 'V-001', 'Acme Supply Co', 'active', 'Net 30', 'ap@acmesupply.com'),
    (gen_random_uuid(), t_id, 'V-002', 'CloudFirst Hosting', 'active', 'Net 15', 'billing@cloudfirst.io'),
    (gen_random_uuid(), t_id, 'V-003', 'Metro Office Leasing', 'active', 'Net 30', 'payments@metroleasing.com'),
    (gen_random_uuid(), t_id, 'V-004', 'Pinnacle Consulting', 'active', 'Net 45', 'invoices@pinnacle.com'),
    (gen_random_uuid(), t_id, 'V-005', 'National Insurance Corp', 'active', 'Net 30', 'premiums@natins.com'),
    (gen_random_uuid(), t_id, 'V-006', 'FastShip Logistics', 'active', 'Net 15', 'ar@fastship.com'),
    (gen_random_uuid(), t_id, 'V-007', 'TechParts Direct', 'active', 'Net 30', 'sales@techparts.com'),
    (gen_random_uuid(), t_id, 'V-008', 'GreenClean Services', 'active', 'Net 30', 'billing@greenclean.com'),
    (gen_random_uuid(), t_id, 'V-009', 'DataSafe Security', 'active', 'Net 30', 'accounts@datasafe.com'),
    (gen_random_uuid(), t_id, 'V-010', 'Summit Legal Group', 'active', 'Net 60', 'billing@summitlegal.com')
  ON CONFLICT (tenant_id, vendor_code) DO NOTHING;

  -- ============================================================
  -- CUSTOMERS (10)
  -- ============================================================
  INSERT INTO contract.customer (customer_id, tenant_id, customer_code, customer_name, status, credit_limit, payment_terms, contact_email)
  VALUES
    (gen_random_uuid(), t_id, 'C-001', 'Northstar Industries', 'active', 500000, 'Net 30', 'ap@northstar.com'),
    (gen_random_uuid(), t_id, 'C-002', 'BluePeak Technologies', 'active', 250000, 'Net 30', 'accounts@bluepeak.io'),
    (gen_random_uuid(), t_id, 'C-003', 'Riverside Healthcare', 'active', 750000, 'Net 45', 'finance@riverside.org'),
    (gen_random_uuid(), t_id, 'C-004', 'Atlas Manufacturing', 'active', 400000, 'Net 30', 'ap@atlasmanuf.com'),
    (gen_random_uuid(), t_id, 'C-005', 'Civic Solutions Group', 'active', 300000, 'Net 30', 'billing@civicsolutions.com'),
    (gen_random_uuid(), t_id, 'C-006', 'Pacific Retail Corp', 'active', 600000, 'Net 45', 'finance@pacificretail.com'),
    (gen_random_uuid(), t_id, 'C-007', 'Keystone Energy', 'active', 1000000, 'Net 30', 'ap@keystoneenergy.com'),
    (gen_random_uuid(), t_id, 'C-008', 'Summit Education', 'active', 200000, 'Net 60', 'accounts@summited.org'),
    (gen_random_uuid(), t_id, 'C-009', 'Vanguard Financial', 'active', 500000, 'Net 30', 'ap@vanguardfin.com'),
    (gen_random_uuid(), t_id, 'C-010', 'Horizon Aerospace', 'active', 800000, 'Net 45', 'finance@horizonaero.com')
  ON CONFLICT (tenant_id, customer_code) DO NOTHING;

  -- ============================================================
  -- GL ENTRIES (sample across FY2025, periods 1-12)
  -- ============================================================
  INSERT INTO contract.gl_entry (gl_entry_id, tenant_id, posting_date, document_number, description, account_number, amount, debit_amount, credit_amount, currency_code, dimension_1, fiscal_year, fiscal_period)
  VALUES
    -- January revenue
    (gen_random_uuid(), t_id, '2025-01-15', 'INV-2501', 'Product sale - Northstar', '4000', -125000, 0, 125000, 'USD', 'Sales', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-15', 'INV-2501', 'AR - Northstar', '1100', 125000, 125000, 0, 'USD', 'Sales', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-20', 'INV-2502', 'Service revenue - BluePeak', '4100', -85000, 0, 85000, 'USD', 'Services', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-20', 'INV-2502', 'AR - BluePeak', '1100', 85000, 85000, 0, 'USD', 'Services', 2025, 1),
    -- January expenses
    (gen_random_uuid(), t_id, '2025-01-31', 'PAY-2501', 'January payroll', '6000', 95000, 95000, 0, 'USD', 'Operations', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-31', 'PAY-2501', 'Cash - payroll', '1000', -95000, 0, 95000, 'USD', 'Operations', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-31', 'RENT-2501', 'Office rent', '6100', 18000, 18000, 0, 'USD', 'Operations', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-31', 'RENT-2501', 'Cash - rent', '1000', -18000, 0, 18000, 'USD', 'Operations', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-28', 'COGS-2501', 'Cost of goods - January', '5000', 62000, 62000, 0, 'USD', 'Operations', 2025, 1),
    (gen_random_uuid(), t_id, '2025-01-28', 'COGS-2501', 'Inventory - January', '1200', -62000, 0, 62000, 'USD', 'Operations', 2025, 1),

    -- February
    (gen_random_uuid(), t_id, '2025-02-10', 'INV-2503', 'Product sale - Atlas', '4000', -142000, 0, 142000, 'USD', 'Sales', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-10', 'INV-2503', 'AR - Atlas', '1100', 142000, 142000, 0, 'USD', 'Sales', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-18', 'INV-2504', 'Service revenue - Riverside', '4100', -96000, 0, 96000, 'USD', 'Services', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-18', 'INV-2504', 'AR - Riverside', '1100', 96000, 96000, 0, 'USD', 'Services', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-28', 'PAY-2502', 'February payroll', '6000', 97000, 97000, 0, 'USD', 'Operations', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-28', 'PAY-2502', 'Cash - payroll', '1000', -97000, 0, 97000, 'USD', 'Operations', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-28', 'RENT-2502', 'Office rent', '6100', 18000, 18000, 0, 'USD', 'Operations', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-15', 'MKT-2501', 'Marketing campaign Q1', '6200', 25000, 25000, 0, 'USD', 'Marketing', 2025, 2),
    (gen_random_uuid(), t_id, '2025-02-20', 'COGS-2502', 'Cost of goods - February', '5000', 71000, 71000, 0, 'USD', 'Operations', 2025, 2),

    -- March
    (gen_random_uuid(), t_id, '2025-03-05', 'INV-2505', 'Product sale - Keystone', '4000', -175000, 0, 175000, 'USD', 'Sales', 2025, 3),
    (gen_random_uuid(), t_id, '2025-03-05', 'INV-2505', 'AR - Keystone', '1100', 175000, 175000, 0, 'USD', 'Sales', 2025, 3),
    (gen_random_uuid(), t_id, '2025-03-15', 'INV-2506', 'Service revenue - Horizon', '4100', -110000, 0, 110000, 'USD', 'Services', 2025, 3),
    (gen_random_uuid(), t_id, '2025-03-31', 'PAY-2503', 'March payroll', '6000', 99000, 99000, 0, 'USD', 'Operations', 2025, 3),
    (gen_random_uuid(), t_id, '2025-03-31', 'RENT-2503', 'Office rent', '6100', 18000, 18000, 0, 'USD', 'Operations', 2025, 3),
    (gen_random_uuid(), t_id, '2025-03-25', 'COGS-2503', 'Cost of goods - March', '5000', 85000, 85000, 0, 'USD', 'Operations', 2025, 3),
    (gen_random_uuid(), t_id, '2025-03-20', 'GA-2501', 'G&A expenses Q1', '6300', 12000, 12000, 0, 'USD', 'Admin', 2025, 3),
    (gen_random_uuid(), t_id, '2025-03-31', 'DEP-2501', 'Q1 depreciation', '6400', 8500, 8500, 0, 'USD', 'Operations', 2025, 3);

  -- ============================================================
  -- TRIAL BALANCE (as of 2025-03-31)
  -- ============================================================
  INSERT INTO contract.trial_balance (tb_id, tenant_id, as_of_date, account_number, account_name, beginning_balance, total_debits, total_credits, ending_balance)
  VALUES
    (gen_random_uuid(), t_id, '2025-03-31', '1000', 'Cash and Equivalents', 850000, 0, 228000, 622000),
    (gen_random_uuid(), t_id, '2025-03-31', '1100', 'Accounts Receivable', 0, 623000, 180000, 443000),
    (gen_random_uuid(), t_id, '2025-03-31', '1200', 'Inventory', 320000, 0, 218000, 102000),
    (gen_random_uuid(), t_id, '2025-03-31', '1300', 'Prepaid Expenses', 36000, 0, 9000, 27000),
    (gen_random_uuid(), t_id, '2025-03-31', '1500', 'Fixed Assets', 450000, 0, 0, 450000),
    (gen_random_uuid(), t_id, '2025-03-31', '1510', 'Accumulated Depreciation', -125000, 0, 8500, -133500),
    (gen_random_uuid(), t_id, '2025-03-31', '2000', 'Accounts Payable', -180000, 95000, 120000, -205000),
    (gen_random_uuid(), t_id, '2025-03-31', '2100', 'Accrued Liabilities', -45000, 0, 15000, -60000),
    (gen_random_uuid(), t_id, '2025-03-31', '2200', 'Short-Term Debt', -100000, 0, 0, -100000),
    (gen_random_uuid(), t_id, '2025-03-31', '2500', 'Long-Term Debt', -350000, 25000, 0, -325000),
    (gen_random_uuid(), t_id, '2025-03-31', '3000', 'Common Stock', -500000, 0, 0, -500000),
    (gen_random_uuid(), t_id, '2025-03-31', '3100', 'Retained Earnings', -356000, 0, 0, -356000),
    (gen_random_uuid(), t_id, '2025-03-31', '4000', 'Product Revenue', 0, 0, 442000, -442000),
    (gen_random_uuid(), t_id, '2025-03-31', '4100', 'Service Revenue', 0, 0, 291000, -291000),
    (gen_random_uuid(), t_id, '2025-03-31', '5000', 'Cost of Goods Sold', 0, 218000, 0, 218000),
    (gen_random_uuid(), t_id, '2025-03-31', '6000', 'Payroll & Benefits', 0, 291000, 0, 291000),
    (gen_random_uuid(), t_id, '2025-03-31', '6100', 'Rent & Facilities', 0, 54000, 0, 54000),
    (gen_random_uuid(), t_id, '2025-03-31', '6200', 'Sales & Marketing', 0, 25000, 0, 25000),
    (gen_random_uuid(), t_id, '2025-03-31', '6300', 'General & Administrative', 0, 12000, 0, 12000),
    (gen_random_uuid(), t_id, '2025-03-31', '6400', 'Depreciation & Amortization', 0, 8500, 0, 8500);

  -- ============================================================
  -- AP INVOICES (12 - mix of open/partial/paid)
  -- ============================================================
  INSERT INTO contract.ap_invoice (ap_invoice_id, tenant_id, vendor_code, invoice_number, invoice_date, due_date, total_amount, paid_amount, balance, status, description)
  VALUES
    (gen_random_uuid(), t_id, 'V-001', 'AS-4501', '2025-01-10', '2025-02-09', 32000, 32000, 0, 'paid', 'Q1 supplies order'),
    (gen_random_uuid(), t_id, 'V-002', 'CF-1122', '2025-02-01', '2025-02-16', 8500, 8500, 0, 'paid', 'February hosting'),
    (gen_random_uuid(), t_id, 'V-003', 'MOL-880', '2025-01-01', '2025-01-31', 18000, 18000, 0, 'paid', 'January rent'),
    (gen_random_uuid(), t_id, 'V-003', 'MOL-881', '2025-02-01', '2025-02-28', 18000, 18000, 0, 'paid', 'February rent'),
    (gen_random_uuid(), t_id, 'V-003', 'MOL-882', '2025-03-01', '2025-03-31', 18000, 0, 18000, 'open', 'March rent'),
    (gen_random_uuid(), t_id, 'V-004', 'PC-2250', '2025-02-15', '2025-04-01', 45000, 20000, 25000, 'partial', 'Strategy consulting engagement'),
    (gen_random_uuid(), t_id, 'V-005', 'NI-Q1-25', '2025-01-15', '2025-02-14', 12000, 12000, 0, 'paid', 'Q1 insurance premium'),
    (gen_random_uuid(), t_id, 'V-006', 'FS-3344', '2025-03-10', '2025-03-25', 4200, 4200, 0, 'paid', 'March shipping'),
    (gen_random_uuid(), t_id, 'V-007', 'TP-7890', '2025-03-05', '2025-04-04', 28000, 0, 28000, 'open', 'Component order #7890'),
    (gen_random_uuid(), t_id, 'V-008', 'GC-550', '2025-03-01', '2025-03-31', 3500, 0, 3500, 'open', 'March cleaning services'),
    (gen_random_uuid(), t_id, 'V-009', 'DS-1001', '2025-02-20', '2025-03-22', 15000, 0, 15000, 'open', 'Annual security audit'),
    (gen_random_uuid(), t_id, 'V-010', 'SL-445', '2024-12-15', '2025-02-13', 22000, 0, 22000, 'open', 'Legal retainer - overdue')
  ON CONFLICT DO NOTHING;

  -- ============================================================
  -- AR INVOICES (12 - mix of open/partial/paid)
  -- ============================================================
  INSERT INTO contract.ar_invoice (ar_invoice_id, tenant_id, customer_code, invoice_number, invoice_date, due_date, total_amount, paid_amount, balance, status, description)
  VALUES
    (gen_random_uuid(), t_id, 'C-001', 'SI-2501', '2025-01-15', '2025-02-14', 125000, 125000, 0, 'paid', 'Product sale - January'),
    (gen_random_uuid(), t_id, 'C-002', 'SI-2502', '2025-01-20', '2025-02-19', 85000, 85000, 0, 'paid', 'Consulting services - January'),
    (gen_random_uuid(), t_id, 'C-004', 'SI-2503', '2025-02-10', '2025-03-12', 142000, 100000, 42000, 'partial', 'Product sale - February'),
    (gen_random_uuid(), t_id, 'C-003', 'SI-2504', '2025-02-18', '2025-04-04', 96000, 0, 96000, 'open', 'Healthcare platform services'),
    (gen_random_uuid(), t_id, 'C-007', 'SI-2505', '2025-03-05', '2025-04-04', 175000, 0, 175000, 'open', 'Energy systems deployment'),
    (gen_random_uuid(), t_id, 'C-010', 'SI-2506', '2025-03-15', '2025-04-29', 110000, 0, 110000, 'open', 'Aerospace consulting Q1'),
    (gen_random_uuid(), t_id, 'C-005', 'SI-2507', '2025-03-20', '2025-04-19', 38000, 0, 38000, 'open', 'Software licenses'),
    (gen_random_uuid(), t_id, 'C-006', 'SI-2508', '2025-03-22', '2025-05-06', 67000, 0, 67000, 'open', 'Retail POS system'),
    (gen_random_uuid(), t_id, 'C-009', 'SI-2509', '2025-03-25', '2025-04-24', 52000, 0, 52000, 'open', 'Financial platform access'),
    (gen_random_uuid(), t_id, 'C-008', 'SI-2510', '2024-11-15', '2025-01-14', 28000, 0, 28000, 'open', 'Training program - OVERDUE'),
    (gen_random_uuid(), t_id, 'C-001', 'SI-2511', '2024-12-10', '2025-01-09', 45000, 0, 45000, 'open', 'Year-end product sale - OVERDUE'),
    (gen_random_uuid(), t_id, 'C-004', 'SI-2512', '2024-10-05', '2024-11-04', 33000, 0, 33000, 'open', 'Legacy invoice - 90+ days')
  ON CONFLICT DO NOTHING;

  -- ============================================================
  -- BUDGET LINES (FY2025 P1-P3, key accounts)
  -- ============================================================
  INSERT INTO contract.budget_line (budget_line_id, tenant_id, department_code, account_number, fiscal_year, fiscal_period, budget_amount)
  VALUES
    -- Revenue budgets
    (gen_random_uuid(), t_id, 'Sales', '4000', 2025, 1, 130000),
    (gen_random_uuid(), t_id, 'Sales', '4000', 2025, 2, 135000),
    (gen_random_uuid(), t_id, 'Sales', '4000', 2025, 3, 160000),
    (gen_random_uuid(), t_id, 'Services', '4100', 2025, 1, 90000),
    (gen_random_uuid(), t_id, 'Services', '4100', 2025, 2, 95000),
    (gen_random_uuid(), t_id, 'Services', '4100', 2025, 3, 100000),
    -- Expense budgets
    (gen_random_uuid(), t_id, 'Operations', '5000', 2025, 1, 60000),
    (gen_random_uuid(), t_id, 'Operations', '5000', 2025, 2, 65000),
    (gen_random_uuid(), t_id, 'Operations', '5000', 2025, 3, 75000),
    (gen_random_uuid(), t_id, 'Operations', '6000', 2025, 1, 92000),
    (gen_random_uuid(), t_id, 'Operations', '6000', 2025, 2, 94000),
    (gen_random_uuid(), t_id, 'Operations', '6000', 2025, 3, 96000),
    (gen_random_uuid(), t_id, 'Operations', '6100', 2025, 1, 18000),
    (gen_random_uuid(), t_id, 'Operations', '6100', 2025, 2, 18000),
    (gen_random_uuid(), t_id, 'Operations', '6100', 2025, 3, 18000),
    (gen_random_uuid(), t_id, 'Marketing', '6200', 2025, 1, 15000),
    (gen_random_uuid(), t_id, 'Marketing', '6200', 2025, 2, 20000),
    (gen_random_uuid(), t_id, 'Marketing', '6200', 2025, 3, 20000)
  ON CONFLICT DO NOTHING;

  -- ============================================================
  -- WATERMARKS (make data look "fresh")
  -- ============================================================
  INSERT INTO platform.watermarks (watermark_id, tenant_id, object_name, last_value, last_sync_at, row_count)
  VALUES
    (gen_random_uuid(), t_id, 'gl_entry', '2025-03-31', NOW() - INTERVAL '2 hours', 27),
    (gen_random_uuid(), t_id, 'chart_of_accounts', '2025-03-31', NOW() - INTERVAL '2 hours', 25),
    (gen_random_uuid(), t_id, 'trial_balance', '2025-03-31', NOW() - INTERVAL '2 hours', 20),
    (gen_random_uuid(), t_id, 'ap_invoice', '2025-03-31', NOW() - INTERVAL '2 hours', 12),
    (gen_random_uuid(), t_id, 'ar_invoice', '2025-03-31', NOW() - INTERVAL '2 hours', 12),
    (gen_random_uuid(), t_id, 'vendor', '2025-03-31', NOW() - INTERVAL '2 hours', 10),
    (gen_random_uuid(), t_id, 'customer', '2025-03-31', NOW() - INTERVAL '2 hours', 10)
  ON CONFLICT (tenant_id, connection_id, object_name) DO UPDATE SET
    last_sync_at = EXCLUDED.last_sync_at,
    row_count = EXCLUDED.row_count;

  -- ============================================================
  -- QUALITY SCORECARD (one good run)
  -- ============================================================
  INSERT INTO audit.scorecard_results (scorecard_id, run_id, tenant_id, accuracy, completeness, consistency, validity, uniqueness, timeliness, composite, gate_status)
  VALUES
    (gen_random_uuid(), gen_random_uuid(), t_id, 100.0, 97.5, 100.0, 100.0, 100.0, 98.0, 99.1, 'certified');

  -- ============================================================
  -- PLATFORM EVENTS (sample)
  -- ============================================================
  INSERT INTO workflow.events (event_id, event_type, source, payload)
  VALUES
    (gen_random_uuid(), 'sync_started', 'pipeline', '{"mode": "full", "objects": 7}'),
    (gen_random_uuid(), 'sync_complete', 'pipeline', '{"records_extracted": 116, "records_loaded": 116, "duration_sec": 12.4}'),
    (gen_random_uuid(), 'quality_passed', 'trust', '{"composite": 99.1, "verdict": "CERTIFIED"}'),
    (gen_random_uuid(), 'kpi_computed', 'semantic', '{"fiscal_year": 2025, "metrics_computed": 18}');

END $$;

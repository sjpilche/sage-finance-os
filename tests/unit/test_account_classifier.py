"""Tests for app.semantic.account_classifier."""

from app.semantic.account_classifier import classify_account


def test_asset_cash():
    assert classify_account("Asset", "Cash in Bank - Operating") == "cash"
    assert classify_account("Asset", "Petty Cash") == "cash"
    assert classify_account("Asset", "Checking Account") == "cash"


def test_asset_ar():
    assert classify_account("Asset", "Accounts Receivable - Trade") == "accounts_receivable"
    assert classify_account("Asset", "A/R - Retainage") == "accounts_receivable"


def test_asset_inventory():
    assert classify_account("Asset", "Raw Materials Inventory") == "inventory"


def test_asset_fixed():
    assert classify_account("Asset", "Office Equipment") == "property_equipment"
    assert classify_account("Asset", "Accumulated Depreciation - Equipment") == "accumulated_depreciation"


def test_liability_ap():
    assert classify_account("Liability", "Accounts Payable") == "accounts_payable"
    assert classify_account("Liability", "Trade Payables") == "accounts_payable"


def test_liability_accrued():
    assert classify_account("Liability", "Accrued Liabilities") == "accrued_liabilities"


def test_liability_debt():
    assert classify_account("Liability", "Long-Term Debt") == "long_term_debt"
    assert classify_account("Liability", "Current Portion of Loan") == "current_debt"


def test_equity():
    assert classify_account("Equity", "Common Stock") == "common_stock"
    assert classify_account("Equity", "Retained Earnings") == "retained_earnings"


def test_revenue():
    assert classify_account("Revenue", "Service Revenue") == "operating_revenue"
    assert classify_account("Revenue", "Interest Income") == "interest_income"
    assert classify_account("Revenue", "Other Income") == "other_income"


def test_expense_classification():
    assert classify_account("Expense", "Payroll Expense") == "payroll"
    assert classify_account("Expense", "Salaries and Wages") == "payroll"
    assert classify_account("Expense", "Rent Expense") == "rent_facilities"
    assert classify_account("Expense", "Depreciation Expense") == "depreciation"
    assert classify_account("Expense", "Interest Expense") == "interest_expense"
    assert classify_account("Expense", "Advertising Expense") == "sales_marketing"
    assert classify_account("Expense", "Office Supplies") == "general_admin"
    assert classify_account("Expense", "Cost of Goods Sold") == "direct_costs"


def test_fallback():
    assert classify_account("Asset", "Something Unknown") == "other_current_assets"
    assert classify_account("Other", "Weird Thing") == "other_opex"

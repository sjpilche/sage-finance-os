"""Tests for Sage Intacct transform functions."""

from decimal import Decimal

from app.ingestion.connectors.sage_intacct.transform import (
    SAGE_TRANSFORMERS,
    transform_sage_gl_detail,
    transform_sage_accounts,
    transform_sage_ap_bills,
    transform_sage_ar_invoices,
    transform_sage_vendors,
    transform_sage_customers,
)


def test_gl_detail_basic():
    records = [{"BATCH_DATE": "03/15/2026", "ACCOUNTNO": "1000", "AMOUNT": "1500.00", "CURRENCY": "USD"}]
    result = transform_sage_gl_detail(records)
    assert len(result) == 1
    r = result[0]
    assert r["account_number"] == "1000"
    assert r["amount"] == Decimal("1500.00")
    assert r["debit_amount"] == Decimal("1500.00")
    assert r["credit_amount"] == Decimal("0")


def test_gl_detail_negative_is_credit():
    records = [{"BATCH_DATE": "03/15/2026", "ACCOUNTNO": "4000", "AMOUNT": "-2500.00"}]
    result = transform_sage_gl_detail(records)
    r = result[0]
    assert r["debit_amount"] == Decimal("0")
    assert r["credit_amount"] == Decimal("2500.00")


def test_gl_detail_dimensions():
    records = [{"BATCH_DATE": "03/15/2026", "ACCOUNTNO": "5000", "AMOUNT": "100",
                "DEPARTMENTID": "ADMIN", "LOCATIONID": "HQ", "CLASSID": "OVERHEAD"}]
    result = transform_sage_gl_detail(records)
    r = result[0]
    assert r["dimension_1"] == "ADMIN"
    assert r["dimension_2"] == "HQ"
    assert r["dimension_3"] == "OVERHEAD"


def test_gl_detail_skips_bad_records():
    records = [
        {"BATCH_DATE": "03/15/2026", "ACCOUNTNO": "1000", "AMOUNT": "100"},
        None,  # bad record — should be skipped
    ]
    # The None will cause an AttributeError in .get() but transform catches it
    result = transform_sage_gl_detail(records)
    assert len(result) == 1


def test_accounts_transform():
    records = [{"ACCOUNTNO": "1000", "TITLE": "Cash", "ACCOUNTTYPE": "Asset",
                "NORMALBALANCE": "debit", "STATUS": "active"}]
    result = transform_sage_accounts(records)
    assert len(result) == 1
    assert result[0]["account_number"] == "1000"
    assert result[0]["is_active"] is True


def test_ap_bills_transform():
    records = [{"VENDORID": "V001", "RECORDID": "INV-100", "TOTALDUE": "5000",
                "TOTALPAID": "2000", "WHENCREATED": "03/01/2026", "CURRENCY": "USD"}]
    result = transform_sage_ap_bills(records)
    assert result[0]["vendor_code"] == "V001"
    assert result[0]["total_amount"] == Decimal("5000")
    assert result[0]["balance"] == Decimal("3000")


def test_ar_invoices_transform():
    records = [{"CUSTOMERID": "C001", "RECORDID": "SI-200", "TOTALDUE": "10000",
                "TOTALPAID": "10000", "WHENCREATED": "02/15/2026"}]
    result = transform_sage_ar_invoices(records)
    assert result[0]["customer_code"] == "C001"
    assert result[0]["balance"] == Decimal("0")


def test_vendors_transform():
    records = [{"VENDORID": "V001", "NAME": "Acme Corp", "STATUS": "active",
                "DISPLAYCONTACT_EMAIL1": "ap@acme.com"}]
    result = transform_sage_vendors(records)
    assert result[0]["vendor_code"] == "V001"
    assert result[0]["contact_email"] == "ap@acme.com"
    assert result[0]["status"] == "active"


def test_customers_transform():
    records = [{"CUSTOMERID": "C001", "NAME": "Big Client LLC", "STATUS": "inactive"}]
    result = transform_sage_customers(records)
    assert result[0]["customer_code"] == "C001"
    assert result[0]["status"] == "inactive"


def test_dispatcher_has_all_objects():
    expected = {"GLDETAIL", "GLACCOUNT", "TRIALBALANCE", "APBILL", "ARINVOICE", "VENDOR", "CUSTOMER"}
    assert set(SAGE_TRANSFORMERS.keys()) == expected

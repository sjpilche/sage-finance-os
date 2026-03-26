"""
sage_intacct.transform
======================
Pure-function transformers that normalize raw Sage Intacct XML-parsed dicts
into canonical column names for contract table writers.

All functions are pure (no DB, no side effects) and error-tolerant:
bad records are skipped with a warning log, never raise.

Adapted from DataClean — identical logic, standalone module.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import Decimal, InvalidOperation

log = logging.getLogger(__name__)


# -- Helpers -------------------------------------------------------------------


def _dec(value) -> Decimal | None:
    """Safely convert a value to Decimal, or return None."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _str(value) -> str:
    """Coerce to string, empty string for None."""
    if value is None:
        return ""
    return str(value).strip()


def _debit_credit(amount: Decimal | None) -> tuple[Decimal, Decimal]:
    """Split a signed amount into (debit, credit) where debit >= 0."""
    if amount is None:
        return Decimal(0), Decimal(0)
    if amount >= 0:
        return amount, Decimal(0)
    return Decimal(0), abs(amount)


# -- GLDETAIL -> gl_entry ------------------------------------------------------


def transform_sage_gl_detail(records: list[dict]) -> list[dict]:
    """Transform Sage Intacct GLDETAIL records into gl_entry rows."""
    rows: list[dict] = []
    for i, rec in enumerate(records):
        try:
            amount = _dec(rec.get("AMOUNT", 0)) or Decimal(0)
            debit, credit = _debit_credit(amount)

            rows.append({
                "posting_date": _str(rec.get("BATCH_DATE", rec.get("ENTRY_DATE", ""))),
                "document_number": _str(rec.get("DOCNUMBER", rec.get("DOCUMENT", ""))),
                "description": _str(rec.get("DESCRIPTION", rec.get("MEMO", ""))),
                "account_number": _str(rec.get("ACCOUNTNO", "")),
                "account_name": _str(rec.get("ACCOUNTTITLE", "")),
                "amount": amount,
                "debit_amount": debit,
                "credit_amount": credit,
                "currency_code": _str(rec.get("CURRENCY", "USD")),
                "dimension_1": _str(rec.get("DEPARTMENTID", "")),
                "dimension_2": _str(rec.get("LOCATIONID", "")),
                "dimension_3": _str(rec.get("CLASSID", "")),
                "source_module": _str(rec.get("BOOKID", rec.get("MODULE", ""))),
                "source_system": "sage_intacct",
                "external_id": _str(rec.get("RECORDNO", rec.get("RECORDID", ""))),
            })
        except Exception as exc:
            log.warning("sage_transform: skipping bad GLDETAIL record %d: %s", i, exc)
    return rows


# -- GLACCOUNT -> chart_of_accounts --------------------------------------------


def transform_sage_accounts(records: list[dict]) -> list[dict]:
    """Transform Sage Intacct GLACCOUNT records into chart_of_accounts rows."""
    rows: list[dict] = []
    for i, rec in enumerate(records):
        try:
            status = _str(rec.get("STATUS", "active"))
            rows.append({
                "account_number": _str(rec.get("ACCOUNTNO", "")),
                "account_name": _str(rec.get("TITLE", rec.get("DESCRIPTION", ""))),
                "account_type": _str(rec.get("ACCOUNTTYPE", "")),
                "normal_balance": _str(rec.get("NORMALBALANCE", "")),
                "is_active": status.lower() == "active",
                "parent_account": _str(rec.get("PARENTID", "")),
                "source_system": "sage_intacct",
                "external_id": _str(rec.get("RECORDNO", rec.get("ACCOUNTNO", ""))),
            })
        except Exception as exc:
            log.warning("sage_transform: skipping bad GLACCOUNT record %d: %s", i, exc)
    return rows


# -- TRIALBALANCE -> trial_balance ---------------------------------------------


def transform_sage_trial_balance(records: list[dict]) -> list[dict]:
    """Transform Sage Intacct get_trialbalance results into trial_balance rows."""
    rows: list[dict] = []
    for i, rec in enumerate(records):
        try:
            begin = _dec(rec.get("BEGINBALANCE", rec.get("BEGINBAL", 0))) or Decimal(0)
            end = _dec(rec.get("ENDBALANCE", rec.get("ENDBAL", 0))) or Decimal(0)
            debit = _dec(rec.get("TOTALDEBIT", rec.get("DEBIT", 0))) or Decimal(0)
            credit = _dec(rec.get("TOTALCREDIT", rec.get("CREDIT", 0))) or Decimal(0)

            rows.append({
                "account_number": _str(rec.get("ACCOUNTNO", "")),
                "account_name": _str(rec.get("ACCOUNTTITLE", rec.get("TITLE", ""))),
                "beginning_balance": begin,
                "ending_balance": end,
                "total_debits": debit,
                "total_credits": credit,
                "source_system": "sage_intacct",
                "external_id": _str(rec.get("ACCOUNTNO", "")),
            })
        except Exception as exc:
            log.warning("sage_transform: skipping bad TRIALBALANCE record %d: %s", i, exc)
    return rows


# -- APBILL -> ap_invoice ------------------------------------------------------


def transform_sage_ap_bills(records: list[dict]) -> list[dict]:
    """Transform Sage Intacct APBILL records into ap_invoice rows."""
    rows: list[dict] = []
    for i, rec in enumerate(records):
        try:
            total_due = _dec(rec.get("TOTALDUE", 0)) or Decimal(0)
            total_paid = _dec(rec.get("TOTALPAID", 0)) or Decimal(0)

            rows.append({
                "vendor_code": _str(rec.get("VENDORID", "")),
                "vendor_name": _str(rec.get("VENDORNAME", "")),
                "invoice_number": _str(rec.get("RECORDID", rec.get("DOCNUMBER", ""))),
                "invoice_date": _str(rec.get("WHENCREATED", rec.get("WHENPOSTED", ""))),
                "due_date": _str(rec.get("WHENDUE", "")),
                "total_amount": total_due,
                "paid_amount": total_paid,
                "balance": total_due - total_paid,
                "description": _str(rec.get("DESCRIPTION", "")),
                "currency_code": _str(rec.get("CURRENCY", "USD")),
                "status": _str(rec.get("STATE", rec.get("STATUS", ""))),
                "source_system": "sage_intacct",
                "external_id": _str(rec.get("RECORDNO", "")),
            })
        except Exception as exc:
            log.warning("sage_transform: skipping bad APBILL record %d: %s", i, exc)
    return rows


# -- ARINVOICE -> ar_invoice ---------------------------------------------------


def transform_sage_ar_invoices(records: list[dict]) -> list[dict]:
    """Transform Sage Intacct ARINVOICE records into ar_invoice rows."""
    rows: list[dict] = []
    for i, rec in enumerate(records):
        try:
            total_due = _dec(rec.get("TOTALDUE", 0)) or Decimal(0)
            total_paid = _dec(rec.get("TOTALPAID", rec.get("TOTALCOLLECTED", 0))) or Decimal(0)

            rows.append({
                "customer_code": _str(rec.get("CUSTOMERID", "")),
                "customer_name": _str(rec.get("CUSTOMERNAME", "")),
                "invoice_number": _str(rec.get("RECORDID", rec.get("DOCNUMBER", ""))),
                "invoice_date": _str(rec.get("WHENCREATED", rec.get("WHENPOSTED", ""))),
                "due_date": _str(rec.get("WHENDUE", "")),
                "total_amount": total_due,
                "paid_amount": total_paid,
                "balance": total_due - total_paid,
                "description": _str(rec.get("DESCRIPTION", "")),
                "currency_code": _str(rec.get("CURRENCY", "USD")),
                "status": _str(rec.get("STATE", rec.get("STATUS", ""))),
                "source_system": "sage_intacct",
                "external_id": _str(rec.get("RECORDNO", "")),
            })
        except Exception as exc:
            log.warning("sage_transform: skipping bad ARINVOICE record %d: %s", i, exc)
    return rows


# -- VENDOR -> vendor ----------------------------------------------------------


def transform_sage_vendors(records: list[dict]) -> list[dict]:
    """Transform Sage Intacct VENDOR records into vendor master rows."""
    rows: list[dict] = []
    for i, rec in enumerate(records):
        try:
            status = _str(rec.get("STATUS", "active"))
            rows.append({
                "vendor_code": _str(rec.get("VENDORID", "")),
                "vendor_name": _str(rec.get("NAME", rec.get("DISPLAYCONTACT_COMPANYNAME", ""))),
                "contact_email": _str(rec.get("DISPLAYCONTACT_EMAIL1", rec.get("EMAIL1", ""))),
                "payment_terms": _str(rec.get("TERMNAME", "")),
                "status": "active" if status.lower() == "active" else "inactive",
                "address": {
                    "line1": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_ADDRESS1", "")),
                    "city": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_CITY", "")),
                    "state": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_STATE", "")),
                    "postal_code": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_ZIP", "")),
                    "country": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_COUNTRY", "")),
                },
                "source_system": "sage_intacct",
                "external_id": _str(rec.get("RECORDNO", rec.get("VENDORID", ""))),
            })
        except Exception as exc:
            log.warning("sage_transform: skipping bad VENDOR record %d: %s", i, exc)
    return rows


# -- CUSTOMER -> customer ------------------------------------------------------


def transform_sage_customers(records: list[dict]) -> list[dict]:
    """Transform Sage Intacct CUSTOMER records into customer master rows."""
    rows: list[dict] = []
    for i, rec in enumerate(records):
        try:
            status = _str(rec.get("STATUS", "active"))
            rows.append({
                "customer_code": _str(rec.get("CUSTOMERID", "")),
                "customer_name": _str(rec.get("NAME", rec.get("DISPLAYCONTACT_COMPANYNAME", ""))),
                "contact_email": _str(rec.get("DISPLAYCONTACT_EMAIL1", rec.get("EMAIL1", ""))),
                "payment_terms": _str(rec.get("TERMNAME", "")),
                "credit_limit": _dec(rec.get("CREDITLIMIT")),
                "status": "active" if status.lower() == "active" else "inactive",
                "address": {
                    "line1": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_ADDRESS1", "")),
                    "city": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_CITY", "")),
                    "state": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_STATE", "")),
                    "postal_code": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_ZIP", "")),
                    "country": _str(rec.get("DISPLAYCONTACT_MAILADDRESS_COUNTRY", "")),
                },
                "source_system": "sage_intacct",
                "external_id": _str(rec.get("RECORDNO", rec.get("CUSTOMERID", ""))),
            })
        except Exception as exc:
            log.warning("sage_transform: skipping bad CUSTOMER record %d: %s", i, exc)
    return rows


# -- Dispatcher ----------------------------------------------------------------

SAGE_TRANSFORMERS: dict[str, Callable[[list[dict]], list[dict]]] = {
    "GLDETAIL": transform_sage_gl_detail,
    "GLACCOUNT": transform_sage_accounts,
    "TRIALBALANCE": transform_sage_trial_balance,
    "APBILL": transform_sage_ap_bills,
    "ARINVOICE": transform_sage_ar_invoices,
    "VENDOR": transform_sage_vendors,
    "CUSTOMER": transform_sage_customers,
}

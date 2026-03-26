"""
sage_intacct.objects
====================
Object catalog for Sage Intacct connector.

Centralizes transport routing, API object names, canonical mappings,
and human-readable descriptions for every supported Intacct object.

Adapted from DataClean — identical content, standalone module.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntacctObject:
    """Metadata for one extractable Sage Intacct object."""

    api_name: str           # Intacct API object name (e.g. "APBILL")
    canonical: str          # Canonical target (e.g. "ap_invoice")
    transport: str          # "xml" or "rest"
    method: str             # XML method: "readByQuery", "get_trialbalance", etc.
    description: str        # Human-readable description
    watermark_field: str    # Field for incremental sync (empty = full-sync only)


# -- Object Catalog -----------------------------------------------------------

OBJECT_CATALOG: dict[str, IntacctObject] = {
    "GLDETAIL": IntacctObject(
        api_name="GLDETAIL",
        canonical="gl_entry",
        transport="xml",
        method="readByQuery",
        description="General ledger detail (journal line items)",
        watermark_field="WHENMODIFIED",
    ),
    "GLACCOUNT": IntacctObject(
        api_name="GLACCOUNT",
        canonical="chart_of_accounts",
        transport="xml",
        method="readByQuery",
        description="Chart of accounts (GL account master)",
        watermark_field="WHENMODIFIED",
    ),
    "TRIALBALANCE": IntacctObject(
        api_name="TRIALBALANCE",
        canonical="trial_balance",
        transport="xml",
        method="get_trialbalance",
        description="Trial balance (period-based, legacy function)",
        watermark_field="",  # Full-sync only — period-based pull
    ),
    "APBILL": IntacctObject(
        api_name="APBILL",
        canonical="ap_invoice",
        transport="xml",
        method="readByQuery",
        description="Accounts payable bills",
        watermark_field="WHENMODIFIED",
    ),
    "ARINVOICE": IntacctObject(
        api_name="ARINVOICE",
        canonical="ar_invoice",
        transport="xml",
        method="readByQuery",
        description="Accounts receivable invoices",
        watermark_field="WHENMODIFIED",
    ),
    "VENDOR": IntacctObject(
        api_name="VENDOR",
        canonical="vendor",
        transport="xml",
        method="readByQuery",
        description="Vendor master records",
        watermark_field="WHENMODIFIED",
    ),
    "CUSTOMER": IntacctObject(
        api_name="CUSTOMER",
        canonical="customer",
        transport="xml",
        method="readByQuery",
        description="Customer master records",
        watermark_field="WHENMODIFIED",
    ),
}

# Quick-lookup helpers
OBJECT_NAMES = list(OBJECT_CATALOG.keys())

OBJECT_TO_CANONICAL: dict[str, str] = {
    k: v.canonical for k, v in OBJECT_CATALOG.items()
}

CANONICAL_TO_OBJECTS: dict[str, str] = {
    v.canonical: k for k, v in OBJECT_CATALOG.items()
}

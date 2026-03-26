"""
sage_intacct.connector
======================
Sage Intacct connector — implements ``BaseConnector`` for extracting
financial data from Sage Intacct via the XML Web Services API.

Adapted from DataClean — import paths updated for Sage Finance OS.

Authentication: DB vault → constructor config → environment variables.
Extraction: readByQuery/readMore pagination, GLDETAIL date-range chunking,
            legacy get_trialbalance for TB.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from datetime import datetime, timedelta

from ..base import BaseConnector
from .config import SageIntacctConfig
from .objects import OBJECT_CATALOG, OBJECT_NAMES
from .transform import SAGE_TRANSFORMERS
from .transport import SageIntacctAuthError, XMLTransport

log = logging.getLogger(__name__)

# Default date range for GLDETAIL when no watermark is provided (12 months)
_GLDETAIL_DEFAULT_MONTHS = 12


class SageIntacctConnector(BaseConnector):
    """
    Sage Intacct XML Web Services + REST API connector.

    Parameters
    ----------
    config : dict with Sage Intacct connection settings, or empty for env-var mode.
    conn   : Optional psycopg2 connection for DB vault lookup.
    tenant_id : Optional tenant UUID for DB vault lookup.
    """

    def __init__(
        self,
        config: dict | None = None,
        conn=None,
        tenant_id: str | None = None,
    ) -> None:
        super().__init__(config or {})

        self._sage_config: SageIntacctConfig | None = None
        self._xml_transport: XMLTransport | None = None

        # 3-tier credential resolution: DB vault -> constructor -> env vars
        if conn and tenant_id:
            self._sage_config = SageIntacctConfig.from_db_vault(conn, tenant_id)

        if self._sage_config is None:
            self._sage_config = SageIntacctConfig.from_env()

    @property
    def source_type(self) -> str:
        return "sage_intacct"

    def _get_transport(self) -> XMLTransport:
        """Lazy-init and return the XML transport."""
        if self._xml_transport is None:
            if not self._sage_config.has_xml_credentials:
                raise SageIntacctAuthError(
                    "Missing Sage Intacct credentials. Required: sender_id, "
                    "sender_password, company_id, user_id, user_password. "
                    "Set via environment variables (SAGE_INTACCT_*) or DB vault."
                )
            self._xml_transport = XMLTransport(self._sage_config)
        return self._xml_transport

    # -- BaseConnector Interface -----------------------------------------------

    def test_connection(self) -> dict:
        """Verify connectivity by acquiring an API session."""
        transport = self._get_transport()
        result = transport.test()

        if result.get("ok"):
            try:
                modules = self._probe_modules(transport)
                result["modules"] = modules
                result["message"] = (
                    f"Connected to Sage Intacct company {self._sage_config.company_id}"
                    f" — modules: {', '.join(modules) if modules else 'unknown'}"
                )
            except Exception:
                pass  # Module probe is best-effort

        return result

    def get_schema(self) -> list[dict]:
        """Return available Intacct objects with descriptions and estimated row counts."""
        transport = self._get_transport()
        schema: list[dict] = []

        for name, obj in OBJECT_CATALOG.items():
            entry: dict = {
                "name": name,
                "description": obj.description,
                "estimated_rows": None,
                "canonical_target": obj.canonical,
            }

            if obj.method == "readByQuery":
                try:
                    probe = transport.read_by_query(name, page_size=1)
                    entry["estimated_rows"] = probe.get("total_count", None)
                except Exception:
                    log.debug("sage_intacct: schema probe failed for %s", name)

            schema.append(entry)

        return schema

    def extract(
        self,
        object_name: str,
        watermark: str | None = None,
        batch_size: int = 1000,
    ) -> Generator[list[dict], None, None]:
        """Yield batches of records for *object_name*."""
        if object_name not in OBJECT_CATALOG:
            raise ValueError(
                f"Unknown Sage Intacct object {object_name!r}. "
                f"Supported: {sorted(OBJECT_NAMES)}"
            )

        obj = OBJECT_CATALOG[object_name]
        transport = self._get_transport()
        batch_size = min(batch_size, 2000)  # Intacct cap

        if obj.method == "get_trialbalance":
            yield from self._extract_trial_balance(transport, watermark)
        elif object_name == "GLDETAIL":
            yield from self._extract_gldetail(transport, watermark, batch_size)
        else:
            yield from self._extract_standard(transport, object_name, watermark, batch_size)

    # -- Extraction Strategies -------------------------------------------------

    def _extract_standard(
        self, transport: XMLTransport, object_name: str,
        watermark: str | None, batch_size: int,
    ) -> Generator[list[dict], None, None]:
        """Standard readByQuery + readMore pagination."""
        obj = OBJECT_CATALOG[object_name]
        query = ""
        if watermark and obj.watermark_field:
            query = f"{obj.watermark_field} >= '{_format_intacct_datetime(watermark)}'"

        log.info("sage_intacct: extracting %s (watermark=%s, batch=%d)",
                 object_name, watermark or "full", batch_size)

        result = transport.read_by_query(object_name, query=query, page_size=batch_size)
        total_fetched = 0

        records = self._transform_records(object_name, result["records"])
        if records:
            yield records
            total_fetched += len(records)

        while result["num_remaining"] > 0 and result["result_id"]:
            result = self._read_more_with_retry(
                transport, result["result_id"], object_name, query, batch_size
            )
            records = self._transform_records(object_name, result["records"])
            if records:
                yield records
                total_fetched += len(records)

        log.info("sage_intacct: %s extraction complete — %d records", object_name, total_fetched)

    def _extract_gldetail(
        self, transport: XMLTransport, watermark: str | None, batch_size: int,
    ) -> Generator[list[dict], None, None]:
        """GLDETAIL extraction with mandatory date-range filtering."""
        if watermark:
            query = f"WHENMODIFIED >= '{_format_intacct_datetime(watermark)}'"
            log.info("sage_intacct: extracting GLDETAIL incremental from %s", watermark)
            yield from self._paginated_read(transport, "GLDETAIL", query, batch_size)
        else:
            log.info("sage_intacct: extracting GLDETAIL (full, %d monthly chunks)",
                     _GLDETAIL_DEFAULT_MONTHS)
            today = datetime.now()
            for months_ago in range(_GLDETAIL_DEFAULT_MONTHS, 0, -1):
                start = today - timedelta(days=months_ago * 30)
                end = today - timedelta(days=(months_ago - 1) * 30)
                query = (
                    f"BATCH_DATE >= '{start.strftime('%m/%d/%Y')}' "
                    f"AND BATCH_DATE <= '{end.strftime('%m/%d/%Y')}'"
                )
                yield from self._paginated_read(transport, "GLDETAIL", query, batch_size)

    def _extract_trial_balance(
        self, transport: XMLTransport, watermark: str | None,
    ) -> Generator[list[dict], None, None]:
        """Trial balance via legacy get_trialbalance (always full-sync)."""
        log.info("sage_intacct: extracting TRIALBALANCE")
        records = transport.get_trial_balance()
        transformed = self._transform_records("TRIALBALANCE", records)
        if transformed:
            yield transformed
        log.info("sage_intacct: TRIALBALANCE — %d records", len(transformed))

    def _paginated_read(
        self, transport: XMLTransport, object_name: str, query: str, batch_size: int,
    ) -> Generator[list[dict], None, None]:
        """Generic paginated readByQuery + readMore loop with session retry."""
        result = transport.read_by_query(object_name, query=query, page_size=batch_size)
        records = self._transform_records(object_name, result["records"])
        if records:
            yield records

        while result["num_remaining"] > 0 and result["result_id"]:
            result = self._read_more_with_retry(
                transport, result["result_id"], object_name, query, batch_size
            )
            records = self._transform_records(object_name, result["records"])
            if records:
                yield records

    def _read_more_with_retry(
        self, transport: XMLTransport, result_id: str,
        object_name: str, query: str, batch_size: int,
    ) -> dict:
        """readMore with session-expiry recovery."""
        try:
            return transport.read_more(result_id)
        except SageIntacctAuthError:
            log.warning(
                "sage_intacct: session expired mid-pagination for %s — "
                "remaining pages will be picked up on next incremental sync.",
                object_name,
            )
            transport._session_id = None
            transport._session_expires = 0.0
            return {"records": [], "total_count": 0, "num_remaining": 0, "result_id": ""}

    # -- Transform -------------------------------------------------------------

    def _transform_records(self, object_name: str, raw_records: list[dict]) -> list[dict]:
        """Apply connector-specific transform if registered."""
        if not raw_records:
            return []
        transformer = SAGE_TRANSFORMERS.get(object_name)
        if transformer:
            return transformer(raw_records)
        return raw_records

    # -- Helpers ---------------------------------------------------------------

    def _probe_modules(self, transport: XMLTransport) -> list[str]:
        """Best-effort probe for which modules (AP, AR, GL) are enabled."""
        modules: list[str] = []
        for label, obj_name in [("GL", "GLACCOUNT"), ("AP", "APBILL"), ("AR", "ARINVOICE")]:
            try:
                transport.read_by_query(obj_name, page_size=1)
                modules.append(label)
            except Exception:
                pass
        return modules


def _format_intacct_datetime(iso_str: str) -> str:
    """Convert ISO-8601 datetime to Intacct query format (MM/DD/YYYY HH:MM:SS)."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(iso_str[:19], fmt)
            return dt.strftime("%m/%d/%Y %H:%M:%S")
        except ValueError:
            continue
    return iso_str

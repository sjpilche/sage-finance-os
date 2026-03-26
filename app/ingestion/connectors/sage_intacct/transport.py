"""
sage_intacct.transport
======================
Dual transport layer for Sage Intacct API communication.

XMLTransport — primary transport for all finance object extraction.
RESTTransport — secondary transport for OAuth 2.0 and modern endpoints.

Adapted from DataClean — import paths updated, otherwise identical.
"""

from __future__ import annotations

import logging
import time
import uuid
import xml.etree.ElementTree as ET
from typing import Any

import requests

from .config import REST_BASE_URL, XML_GATEWAY_URL, SageIntacctConfig

log = logging.getLogger(__name__)

# -- Errors --------------------------------------------------------------------


class SageIntacctAPIError(Exception):
    """Raised when the Sage Intacct API returns an error response."""

    def __init__(self, message: str, error_code: str = "", *, raw: str = ""):
        self.error_code = error_code
        self.raw = raw
        super().__init__(message)


class SageIntacctAuthError(SageIntacctAPIError):
    """Raised on authentication / authorization failures."""


class SageIntacctRateLimitError(SageIntacctAPIError):
    """Raised when rate-limited (HTTP 429)."""


# -- XML Transport -------------------------------------------------------------


class XMLTransport:
    """
    Sage Intacct XML Web Services transport.

    Handles envelope construction, session-based authentication,
    retry logic (429 / 524), and XML response parsing.
    """

    MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 120  # seconds — generous for GLDETAIL

    def __init__(self, config: SageIntacctConfig) -> None:
        self._config = config
        self._session_id: str | None = None
        self._session_expires: float = 0.0
        self._http = requests.Session()
        self._http.headers.update({"Content-Type": "application/xml"})

    # -- Public API ------------------------------------------------------------

    def test(self) -> dict:
        """Verify connectivity by acquiring an API session."""
        start = time.monotonic()
        try:
            self._acquire_session()
            latency = int((time.monotonic() - start) * 1000)
            return {
                "ok": True,
                "message": f"Connected to company {self._config.company_id}",
                "latency_ms": latency,
                "company_id": self._config.company_id,
                "entity_id": self._config.entity_id or "(top-level)",
            }
        except SageIntacctAuthError as exc:
            latency = int((time.monotonic() - start) * 1000)
            return {"ok": False, "message": f"Authentication failed: {exc}", "latency_ms": latency}
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return {"ok": False, "message": f"Connection failed: {exc}", "latency_ms": latency}

    def read_by_query(
        self, object_name: str, *, query: str = "", fields: str = "*", page_size: int = 1000,
    ) -> dict:
        """Execute a ``readByQuery`` call. Returns {records, total_count, num_remaining, result_id}."""
        func_xml = f"""<readByQuery>
    <object>{object_name}</object>
    <fields>{fields}</fields>
    <query>{_xml_escape(query)}</query>
    <pagesize>{page_size}</pagesize>
</readByQuery>"""
        result = self._call_function(func_xml)
        return self._parse_read_result(result)

    def read_more(self, result_id: str) -> dict:
        """Fetch next page of a paginated ``readByQuery`` result."""
        func_xml = f"""<readMore>
    <resultId>{result_id}</resultId>
</readMore>"""
        result = self._call_function(func_xml)
        return self._parse_read_result(result)

    def get_trial_balance(
        self, *, reporting_period: str = "", start_date: str = "", end_date: str = "",
    ) -> list[dict]:
        """Execute the legacy ``get_trialbalance`` function."""
        if reporting_period:
            func_xml = f"""<get_trialbalance>
    <reportingperiodname>{_xml_escape(reporting_period)}</reportingperiodname>
</get_trialbalance>"""
        elif start_date and end_date:
            func_xml = f"""<get_trialbalance>
    <startdate>{_xml_escape(start_date)}</startdate>
    <enddate>{_xml_escape(end_date)}</enddate>
</get_trialbalance>"""
        else:
            func_xml = "<get_trialbalance />"

        result = self._call_function(func_xml)
        return _elements_to_dicts(result)

    def inspect(self, object_name: str) -> dict:
        """Call ``inspect`` to get object metadata (field names, types)."""
        func_xml = f"""<inspect>
    <object>{object_name}</object>
</inspect>"""
        result = self._call_function(func_xml)
        return _element_to_dict(result) if result is not None else {}

    def get_objects(self) -> list[str]:
        """Return list of available API object names via ``getObjectList``."""
        func_xml = "<getObjectList />"
        result = self._call_function(func_xml)
        objects = []
        if result is not None:
            for child in result:
                if child.text:
                    objects.append(child.text.strip())
        return objects

    # -- Session Management ----------------------------------------------------

    def _acquire_session(self) -> str:
        """Acquire or reuse a session ID (cached ~25 min)."""
        if self._session_id and time.monotonic() < self._session_expires:
            return self._session_id

        log.info("sage_intacct: acquiring new API session for company %s", self._config.company_id)
        func_xml = "<getAPISession />"
        envelope = self._build_envelope(func_xml, use_session=False)
        resp_root = self._send_request(envelope)
        result = self._extract_result(resp_root)

        session_el = result.find(".//sessionid")
        if session_el is None or not session_el.text:
            raise SageIntacctAuthError("getAPISession did not return a session ID")

        self._session_id = session_el.text.strip()
        self._session_expires = time.monotonic() + (25 * 60)
        log.info("sage_intacct: session acquired (company=%s, entity=%s)",
                 self._config.company_id, self._config.entity_id or "top-level")
        return self._session_id

    # -- Envelope Construction -------------------------------------------------

    def _build_envelope(self, function_xml: str, *, use_session: bool = True) -> str:
        """Build the full XML request envelope."""
        control_id = str(uuid.uuid4())

        if use_session:
            session_id = self._acquire_session()
            auth_block = f"""<authentication>
            <sessionid>{session_id}</sessionid>
        </authentication>"""
        else:
            auth_block = f"""<authentication>
            <login>
                <userid>{_xml_escape(self._config.user_id)}</userid>
                <companyid>{_xml_escape(self._config.company_id)}</companyid>
                <password>{_xml_escape(self._config.user_password)}</password>
                {self._entity_xml()}
            </login>
        </authentication>"""

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<request>
    <control>
        <senderid>{_xml_escape(self._config.sender_id)}</senderid>
        <password>{_xml_escape(self._config.sender_password)}</password>
        <controlid>{control_id}</controlid>
        <uniqueid>false</uniqueid>
        <dtdversion>3.0</dtdversion>
        <includewhitespace>false</includewhitespace>
    </control>
    <operation>
        {auth_block}
        <content>
            <function controlid="{control_id}">
                {function_xml}
            </function>
        </content>
    </operation>
</request>"""

    def _entity_xml(self) -> str:
        """Return ``<locationid>`` element if multi-entity is configured."""
        if self._config.entity_id:
            return f"<locationid>{_xml_escape(self._config.entity_id)}</locationid>"
        return ""

    # -- HTTP + Retry ----------------------------------------------------------

    def _call_function(self, function_xml: str) -> ET.Element | None:
        """Build envelope, send, extract result element."""
        envelope = self._build_envelope(function_xml, use_session=True)
        resp_root = self._send_request(envelope)
        return self._extract_result(resp_root)

    def _send_request(self, xml_body: str) -> ET.Element:
        """POST to the XML gateway with retry logic (429, 524, connection errors)."""
        last_exc: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = self._http.post(
                    XML_GATEWAY_URL, data=xml_body.encode("utf-8"), timeout=self.DEFAULT_TIMEOUT,
                )

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "5"))
                    log.warning("sage_intacct: rate limited (429), waiting %ds (attempt %d/%d)",
                                retry_after, attempt, self.MAX_RETRIES)
                    if attempt < self.MAX_RETRIES:
                        time.sleep(retry_after)
                        continue
                    raise SageIntacctRateLimitError(f"Rate limited after {self.MAX_RETRIES} attempts")

                if resp.status_code == 524:
                    wait = 2 ** attempt
                    log.warning("sage_intacct: gateway timeout (524), waiting %ds (attempt %d/%d)",
                                wait, attempt, self.MAX_RETRIES)
                    if attempt < self.MAX_RETRIES:
                        time.sleep(wait)
                        continue
                    raise SageIntacctAPIError(
                        "Query timed out — try a shorter date range", error_code="524",
                    )

                if resp.status_code != 200:
                    raise SageIntacctAPIError(
                        f"HTTP {resp.status_code}: {resp.text[:500]}",
                        error_code=str(resp.status_code), raw=resp.text[:2000],
                    )

                return ET.fromstring(resp.content)

            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                wait = 2 ** attempt
                log.warning("sage_intacct: connection error, waiting %ds (attempt %d/%d): %s",
                            wait, attempt, self.MAX_RETRIES, exc)
                if attempt < self.MAX_RETRIES:
                    time.sleep(wait)
                    continue

        raise SageIntacctAPIError(f"Failed after {self.MAX_RETRIES} attempts: {last_exc}")

    # -- Response Parsing ------------------------------------------------------

    def _extract_result(self, root: ET.Element) -> ET.Element | None:
        """Extract the ``<result>`` element, checking for errors."""
        control_status = root.findtext(".//control/status", default="")
        if control_status.lower() == "failure":
            err_msg = _extract_error_message(root, ".//control//errormessage")
            raise SageIntacctAPIError(
                f"Control-level failure: {err_msg}",
                raw=ET.tostring(root, encoding="unicode")[:2000],
            )

        result = root.find(".//result")
        if result is None:
            raise SageIntacctAPIError(
                "No <result> element in response",
                raw=ET.tostring(root, encoding="unicode")[:2000],
            )

        status = result.findtext("status", default="")
        if status.lower() == "failure":
            err_msg = _extract_error_message(result, ".//errormessage")
            err_no = result.findtext(".//errorno", default="")
            if any(kw in err_msg.lower() for kw in ("invalid credentials", "login", "session", "authorization")):
                self._session_id = None
                self._session_expires = 0.0
                raise SageIntacctAuthError(err_msg, error_code=err_no)
            raise SageIntacctAPIError(err_msg, error_code=err_no)

        return result.find("data")

    def _parse_read_result(self, data: ET.Element | None) -> dict:
        """Parse a ``readByQuery`` / ``readMore`` data element."""
        if data is None:
            return {"records": [], "total_count": 0, "num_remaining": 0, "result_id": ""}
        records = _elements_to_dicts(data)
        return {
            "records": records,
            "total_count": int(data.get("totalcount", "0")),
            "num_remaining": int(data.get("numremaining", "0")),
            "result_id": data.get("resultId", "") or data.get("resultid", ""),
        }


# -- REST Transport ------------------------------------------------------------


class RESTTransport:
    """Sage Intacct REST API transport (OAuth 2.0 Bearer token)."""

    TOKEN_URL = "https://oauth.intacct.com/ia/api/v1/token"
    AUTH_URL = "https://oauth.intacct.com/ia/api/v1/authorize"

    def __init__(self, config: SageIntacctConfig) -> None:
        self._config = config
        self._access_token: str = ""
        self._token_expires: float = 0.0
        self._http = requests.Session()

    def get_auth_url(self, state: str) -> str:
        """Generate OAuth 2.0 authorization URL for redirect."""
        params = {
            "client_id": self._config.client_id,
            "redirect_uri": self._config.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "openid profile email",
        }
        qs = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())
        return f"{self.AUTH_URL}?{qs}"

    def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for access + refresh tokens."""
        resp = self._http.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "redirect_uri": self._config.redirect_uri,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise SageIntacctAuthError(
                f"OAuth token exchange failed: {resp.status_code} {resp.text[:500]}"
            )
        return resp.json()

    def get(self, path: str, **kwargs: Any) -> dict:
        """Authenticated GET against the REST API."""
        self._ensure_token()
        resp = self._http.get(
            f"{REST_BASE_URL}/{path.lstrip('/')}",
            headers={"Authorization": f"Bearer {self._access_token}"},
            timeout=30, **kwargs,
        )
        resp.raise_for_status()
        return resp.json()

    def _ensure_token(self) -> None:
        if not self._access_token:
            raise SageIntacctAuthError("No REST API access token — complete OAuth flow first")


# -- XML Helpers ---------------------------------------------------------------


def _xml_escape(text: str) -> str:
    """Escape XML special characters in text content."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;").replace("'", "&apos;")
    )


def _extract_error_message(root: ET.Element, xpath: str) -> str:
    """Pull human-readable error text from Intacct error elements."""
    parts: list[str] = []
    for err_msg_el in root.findall(xpath):
        for error in err_msg_el.findall("error"):
            desc = error.findtext("description") or error.findtext("description2") or ""
            correction = error.findtext("correction") or ""
            msg = desc.strip()
            if correction.strip():
                msg += f" (fix: {correction.strip()})"
            if msg:
                parts.append(msg)
        if not parts:
            desc = err_msg_el.findtext("description") or err_msg_el.findtext("description2") or ""
            if desc.strip():
                parts.append(desc.strip())
    return "; ".join(parts) if parts else "Unknown error"


def _element_to_dict(el: ET.Element) -> dict:
    """Convert a single XML element and its children to a flat dict."""
    result: dict[str, Any] = {}
    for child in el:
        tag = child.tag
        if len(child):
            for sub in child:
                result[f"{tag}_{sub.tag}"] = sub.text or ""
        else:
            result[tag] = child.text or ""
    return result


def _elements_to_dicts(parent: ET.Element) -> list[dict]:
    """Convert child elements of *parent* to a list of flat dicts."""
    records: list[dict] = []
    skip_tags = {"listtype", "count", "totalcount", "numremaining", "resultId", "resultid"}
    for child in parent:
        if child.tag in skip_tags:
            continue
        records.append(_element_to_dict(child))
    return records

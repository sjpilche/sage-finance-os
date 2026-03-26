"""
sage_intacct.config
===================
Sage Intacct connection configuration and credential management.

Adapted from DataClean — import paths updated for Sage Finance OS.

Required environment variables (when not using DB vault):
    SAGE_INTACCT_SENDER_ID, SAGE_INTACCT_SENDER_PASSWORD,
    SAGE_INTACCT_COMPANY_ID, SAGE_INTACCT_USER_ID, SAGE_INTACCT_USER_PASSWORD

Optional:
    SAGE_INTACCT_ENTITY_ID, SAGE_INTACCT_CLIENT_ID,
    SAGE_INTACCT_CLIENT_SECRET, SAGE_INTACCT_REDIRECT_URI
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

log = logging.getLogger(__name__)

# Sage Intacct XML Web Services gateway (single global endpoint)
XML_GATEWAY_URL = "https://api.intacct.com/ia/xml/xmlgw.phtml"

# Sage Intacct REST API base URL
REST_BASE_URL = "https://api.intacct.com/ia/api/v1"


@dataclass(frozen=True)
class SageIntacctConfig:
    """Immutable config for a Sage Intacct connection."""

    # XML Web Services credentials (primary — required for extraction)
    sender_id: str
    sender_password: str
    company_id: str
    user_id: str
    user_password: str

    # Multi-entity support (empty string = top-level / single-entity)
    entity_id: str = ""

    # OAuth 2.0 credentials (optional — for REST API / connection UX)
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""

    @classmethod
    def from_env(cls) -> SageIntacctConfig:
        """Build config from ``SAGE_INTACCT_*`` environment variables."""
        return cls(
            sender_id=os.environ.get("SAGE_INTACCT_SENDER_ID", ""),
            sender_password=os.environ.get("SAGE_INTACCT_SENDER_PASSWORD", ""),
            company_id=os.environ.get("SAGE_INTACCT_COMPANY_ID", ""),
            user_id=os.environ.get("SAGE_INTACCT_USER_ID", ""),
            user_password=os.environ.get("SAGE_INTACCT_USER_PASSWORD", ""),
            entity_id=os.environ.get("SAGE_INTACCT_ENTITY_ID", ""),
            client_id=os.environ.get("SAGE_INTACCT_CLIENT_ID", ""),
            client_secret=os.environ.get("SAGE_INTACCT_CLIENT_SECRET", ""),
            redirect_uri=os.environ.get("SAGE_INTACCT_REDIRECT_URI", ""),
        )

    @classmethod
    def from_db_vault(cls, conn, tenant_id: str) -> SageIntacctConfig | None:
        """
        Load config from ``platform.connections`` DB vault.

        Returns None if no active Sage Intacct connection is configured.
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT credentials FROM platform.connections
                    WHERE tenant_id = %s
                      AND provider = 'sage_intacct'
                      AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (tenant_id,),
                )
                row = cur.fetchone()
        except Exception:
            log.warning("sage_intacct: DB vault lookup failed", exc_info=True)
            return None

        if row is None:
            return None

        creds = row["credentials"] if isinstance(row, dict) else row[0]
        if isinstance(creds, str):
            import json
            creds = json.loads(creds)

        return cls(
            sender_id=creds.get("sender_id", ""),
            sender_password=creds.get("sender_password", ""),
            company_id=creds.get("company_id", ""),
            user_id=creds.get("user_id", ""),
            user_password=creds.get("user_password", ""),
            entity_id=creds.get("entity_id", ""),
            client_id=creds.get("client_id", ""),
            client_secret=creds.get("client_secret", ""),
            redirect_uri=creds.get("redirect_uri", ""),
        )

    @property
    def has_xml_credentials(self) -> bool:
        """True if all required XML Web Services credentials are present."""
        return bool(
            self.sender_id
            and self.sender_password
            and self.company_id
            and self.user_id
            and self.user_password
        )

    @property
    def has_oauth_credentials(self) -> bool:
        """True if OAuth 2.0 credentials are present for REST API."""
        return bool(self.client_id and self.client_secret)

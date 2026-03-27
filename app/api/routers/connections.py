"""
Connection management endpoints — CRUD for Sage Intacct connections.

POST   /v1/connections          — Create a new connection
GET    /v1/connections          — List connections
GET    /v1/connections/{id}     — Get connection detail
POST   /v1/connections/{id}/test — Test connection
DELETE /v1/connections/{id}     — Delete connection
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.models.responses import wrap_response
from app.core.crypto import encrypt_credentials, decrypt_credentials, is_encrypted
from app.core.deps import require_db
from app.core.errors import NotFoundError, ValidationError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/connections", tags=["connections"])

# Default tenant for single-tenant V1
_DEFAULT_TENANT = "default"


class ConnectionCreate(BaseModel):
    name: str
    credentials: dict  # sender_id, sender_password, company_id, user_id, user_password, entity_id


class ConnectionUpdate(BaseModel):
    name: str | None = None
    credentials: dict | None = None


async def _get_default_tenant_id(conn: asyncpg.Connection) -> str:
    """Get the default tenant UUID."""
    row = await conn.fetchrow(
        "SELECT tenant_id FROM platform.tenants WHERE slug = $1", _DEFAULT_TENANT
    )
    if not row:
        raise ValidationError("Default tenant not found — run migrations first")
    return str(row["tenant_id"])


@router.post("")
async def create_connection(body: ConnectionCreate, conn: asyncpg.Connection = Depends(require_db)):
    """Create a new Sage Intacct connection."""
    tenant_id = await _get_default_tenant_id(conn)

    # Validate required credential fields
    required = ["sender_id", "sender_password", "company_id", "user_id", "user_password"]
    missing = [f for f in required if not body.credentials.get(f)]
    if missing:
        raise ValidationError(f"Missing required credentials: {', '.join(missing)}")

    row = await conn.fetchrow(
        """
        INSERT INTO platform.connections (tenant_id, provider, name, credentials, status)
        VALUES ($1, 'sage_intacct', $2, $3, 'pending')
        RETURNING connection_id, tenant_id, provider, name, status, created_at
        """,
        tenant_id, body.name, encrypt_credentials(body.credentials),
    )

    return wrap_response({
        "connection_id": str(row["connection_id"]),
        "name": row["name"],
        "provider": row["provider"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
    })


@router.get("")
async def list_connections(conn: asyncpg.Connection = Depends(require_db)):
    """List all connections."""
    tenant_id = await _get_default_tenant_id(conn)

    rows = await conn.fetch(
        """
        SELECT connection_id, provider, name, status, last_tested_at, created_at
        FROM platform.connections
        WHERE tenant_id = $1
        ORDER BY created_at DESC
        """,
        tenant_id,
    )

    connections = [
        {
            "connection_id": str(r["connection_id"]),
            "provider": r["provider"],
            "name": r["name"],
            "status": r["status"],
            "last_tested_at": r["last_tested_at"].isoformat() if r["last_tested_at"] else None,
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]

    return wrap_response(connections)


@router.get("/{connection_id}")
async def get_connection(connection_id: UUID, conn: asyncpg.Connection = Depends(require_db)):
    """Get connection detail (credentials redacted)."""
    row = await conn.fetchrow(
        """
        SELECT connection_id, tenant_id, provider, name, credentials, status,
               last_tested_at, created_at, updated_at
        FROM platform.connections
        WHERE connection_id = $1
        """,
        connection_id,
    )
    if not row:
        raise NotFoundError(f"Connection {connection_id} not found")

    # Decrypt and redact sensitive fields
    raw_creds = row["credentials"] or ""
    creds = decrypt_credentials(raw_creds) if raw_creds and is_encrypted(raw_creds) else (json.loads(raw_creds) if raw_creds else {})
    redacted = {k: ("***" if "password" in k.lower() or "secret" in k.lower() else v)
                for k, v in creds.items()}

    return wrap_response({
        "connection_id": str(row["connection_id"]),
        "provider": row["provider"],
        "name": row["name"],
        "credentials": redacted,
        "status": row["status"],
        "last_tested_at": row["last_tested_at"].isoformat() if row["last_tested_at"] else None,
        "created_at": row["created_at"].isoformat(),
    })


@router.post("/{connection_id}/test")
async def test_connection(connection_id: UUID, conn: asyncpg.Connection = Depends(require_db)):
    """Test a Sage Intacct connection."""
    import asyncio

    row = await conn.fetchrow(
        "SELECT credentials FROM platform.connections WHERE connection_id = $1",
        connection_id,
    )
    if not row:
        raise NotFoundError(f"Connection {connection_id} not found")

    raw_creds = row["credentials"] or ""
    creds = decrypt_credentials(raw_creds) if raw_creds and is_encrypted(raw_creds) else (json.loads(raw_creds) if raw_creds else {})

    # Run connector test in thread (sync requests library)
    from app.ingestion.connectors.sage_intacct import SageIntacctConnector

    def _test():
        connector = SageIntacctConnector(config=creds)
        return connector.test_connection()

    result = await asyncio.to_thread(_test)

    # Update connection status
    new_status = "active" if result.get("ok") else "failed"
    await conn.execute(
        """
        UPDATE platform.connections
        SET status = $1, last_tested_at = $2, updated_at = $2
        WHERE connection_id = $3
        """,
        new_status, datetime.now(timezone.utc), connection_id,
    )

    return wrap_response(result)


@router.delete("/{connection_id}")
async def delete_connection(connection_id: UUID, conn: asyncpg.Connection = Depends(require_db)):
    """Delete a connection."""
    result = await conn.execute(
        "DELETE FROM platform.connections WHERE connection_id = $1", connection_id,
    )
    if result == "DELETE 0":
        raise NotFoundError(f"Connection {connection_id} not found")

    return wrap_response({"deleted": True, "connection_id": str(connection_id)})

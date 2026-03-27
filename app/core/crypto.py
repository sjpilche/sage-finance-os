"""
Credential encryption utilities — Fernet symmetric encryption for secrets at rest.

Encrypts Sage Intacct credentials before storage in platform.connections.
Decrypts on retrieval for connector use.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging

from cryptography.fernet import Fernet

from app.config import get_settings

log = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Derive a Fernet key from the CERT_SIGNING_KEY setting."""
    key_material = get_settings().CERT_SIGNING_KEY.encode()
    # Fernet requires a 32-byte URL-safe base64 key. Derive from signing key.
    derived = hashlib.sha256(key_material).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


def encrypt_credentials(credentials: dict) -> str:
    """Encrypt a credentials dict to a base64 string for DB storage."""
    plaintext = json.dumps(credentials).encode()
    return _get_fernet().encrypt(plaintext).decode()


def decrypt_credentials(encrypted: str) -> dict:
    """Decrypt a stored credential string back to a dict."""
    plaintext = _get_fernet().decrypt(encrypted.encode())
    return json.loads(plaintext)


def is_encrypted(value: str) -> bool:
    """Check if a value looks like Fernet-encrypted data (starts with gAAAAA)."""
    return value.startswith("gAAAAA")

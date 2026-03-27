"""
trust.certificate
=================
Certificate of Data Health — HMAC-SHA256 signed proof of data certification.

Adapted from DataClean's certification/certificate.py.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from app.trust.scorecard import ScoreCard

log = logging.getLogger(__name__)


@dataclass
class Certificate:
    certificate_id: str
    run_id: str
    tenant_id: str
    composite_score: float
    verdict: str
    gate_passed: bool
    dimensions_summary: dict
    evidence_hash: str
    signature: str
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["issued_at"] = self.issued_at.isoformat()
        return d


def _get_signing_key() -> bytes:
    """Resolve HMAC signing key from settings."""
    from app.config import get_settings
    return get_settings().CERT_SIGNING_KEY.encode()


def generate_certificate(scorecard: ScoreCard) -> Certificate:
    """Generate a Certificate of Data Health from a computed scorecard."""
    cert_id = str(uuid.uuid4())

    dims_summary = {
        name: {"raw_score": dim.raw_score, "weighted_score": dim.weighted_score}
        for name, dim in scorecard.dimensions.items()
    }

    payload = json.dumps({
        "certificate_id": cert_id,
        "run_id": scorecard.run_id,
        "tenant_id": scorecard.tenant_id,
        "composite_score": scorecard.composite_score,
        "verdict": scorecard.verdict,
        "evidence_hash": scorecard.evidence_hash,
    }, sort_keys=True)

    signature = hmac.new(_get_signing_key(), payload.encode(), hashlib.sha256).hexdigest()

    cert = Certificate(
        certificate_id=cert_id,
        run_id=scorecard.run_id,
        tenant_id=scorecard.tenant_id,
        composite_score=scorecard.composite_score,
        verdict=scorecard.verdict,
        gate_passed=scorecard.gate_passed,
        dimensions_summary=dims_summary,
        evidence_hash=scorecard.evidence_hash,
        signature=signature,
    )

    log.info("certificate: cert=%s run=%s verdict=%s", cert_id, scorecard.run_id, scorecard.verdict)
    return cert


def verify_certificate(certificate: Certificate) -> bool:
    """Verify the HMAC signature on a certificate."""
    payload = json.dumps({
        "certificate_id": certificate.certificate_id,
        "run_id": certificate.run_id,
        "tenant_id": certificate.tenant_id,
        "composite_score": certificate.composite_score,
        "verdict": certificate.verdict,
        "evidence_hash": certificate.evidence_hash,
    }, sort_keys=True)

    expected = hmac.new(_get_signing_key(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(certificate.signature, expected)


def persist_certificate(conn, certificate: Certificate) -> None:
    """Write the certificate to audit.certificates."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit.certificates
                (run_id, tenant_id, signature, scorecard_snapshot)
            VALUES (%s, %s, %s, %s::jsonb)
            """,
            (
                certificate.run_id,
                certificate.tenant_id,
                certificate.signature,
                json.dumps(certificate.to_dict(), default=str),
            ),
        )
    conn.commit()
    log.info("persist_certificate: run=%s", certificate.run_id)

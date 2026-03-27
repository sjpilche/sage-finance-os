"""Tests for app.trust.certificate — HMAC-SHA256 certificate generation and verification."""

import os
from unittest.mock import patch

from app.trust.certificate import Certificate, generate_certificate, verify_certificate
from app.trust.scorecard import compute_scorecard


def _make_scorecard(verdict="CERTIFIED", composite=100.0):
    """Build a test scorecard via the real compute engine."""
    dq = {
        "results": {
            "gl_entry": [
                {"check_name": f"check_{i}", "severity": "critical", "passed": True}
                for i in range(5)
            ],
        },
        "total": 5,
        "passed": 5,
        "failed": 0,
        "critical_failures": 0,
        "pass_rate": 1.0,
    }
    return compute_scorecard("run-cert-test", "tenant-1", dq, {"gl_entry": 500})


def test_generate_certificate_creates_valid_cert():
    sc = _make_scorecard()
    cert = generate_certificate(sc)
    assert cert.run_id == "run-cert-test"
    assert cert.tenant_id == "tenant-1"
    assert cert.gate_passed is True
    assert cert.verdict == "CERTIFIED"
    assert len(cert.signature) == 64  # SHA-256 hex digest
    assert cert.certificate_id  # non-empty UUID


def test_verify_certificate_passes_for_valid():
    sc = _make_scorecard()
    cert = generate_certificate(sc)
    assert verify_certificate(cert) is True


def test_verify_certificate_fails_for_tampered():
    sc = _make_scorecard()
    cert = generate_certificate(sc)
    cert.composite_score = 50.0  # tamper
    assert verify_certificate(cert) is False


def test_verify_certificate_fails_for_tampered_signature():
    sc = _make_scorecard()
    cert = generate_certificate(sc)
    cert.signature = "a" * 64  # fake signature
    assert verify_certificate(cert) is False


def test_certificate_to_dict():
    sc = _make_scorecard()
    cert = generate_certificate(sc)
    d = cert.to_dict()
    assert "certificate_id" in d
    assert "signature" in d
    assert "issued_at" in d
    assert isinstance(d["issued_at"], str)


def test_different_signing_key_fails_verification():
    sc = _make_scorecard()
    cert = generate_certificate(sc)

    # Change signing key after generation — must clear settings singleton
    import app.config as cfg
    original = cfg._settings
    try:
        cfg._settings = None
        with patch.dict(os.environ, {"CERT_SIGNING_KEY": "different-key"}):
            assert verify_certificate(cert) is False
    finally:
        cfg._settings = original


def test_certificate_deterministic_for_same_scorecard():
    """Same scorecard should produce different cert IDs but same signature pattern."""
    sc = _make_scorecard()
    cert1 = generate_certificate(sc)
    cert2 = generate_certificate(sc)
    # Different cert IDs (UUID)
    assert cert1.certificate_id != cert2.certificate_id
    # But signatures differ because cert_id is in the payload
    assert cert1.signature != cert2.signature

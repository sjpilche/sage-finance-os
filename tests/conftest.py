"""
Shared test fixtures for Sage Finance OS.

Provides mock DB connections, test settings overrides, and sample data factories.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    """Ensure test environment doesn't hit real databases."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/test_db")
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
    monkeypatch.setenv("CERT_SIGNING_KEY", "test-signing-key")
    monkeypatch.setenv("RUN_MIGRATIONS", "false")


@pytest.fixture
def mock_sync_conn():
    """Mock psycopg2 connection with cursor context manager."""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    cursor.rowcount = 1
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture
def mock_cursor(mock_sync_conn):
    """Return the mock cursor from mock_sync_conn for assertion convenience."""
    return mock_sync_conn.cursor.return_value.__enter__.return_value


@pytest.fixture
def sample_dq_summary():
    """Sample DQ summary with all checks passing."""
    return {
        "results": {
            "gl_entry": [
                {"check_name": "null_posting_date", "severity": "critical", "passed": True},
                {"check_name": "null_account_number", "severity": "critical", "passed": True},
                {"check_name": "debit_credit_balance", "severity": "critical", "passed": True},
                {"check_name": "completeness_description", "severity": "warning", "passed": True},
            ],
            "trial_balance": [
                {"check_name": "tb_balance", "severity": "critical", "passed": True},
            ],
        },
        "total": 5,
        "passed": 5,
        "failed": 0,
        "critical_failures": 0,
        "pass_rate": 1.0,
    }


@pytest.fixture
def sample_dq_summary_failing():
    """Sample DQ summary with critical failures."""
    return {
        "results": {
            "gl_entry": [
                {"check_name": "null_posting_date", "severity": "critical", "passed": False},
                {"check_name": "null_account_number", "severity": "critical", "passed": True},
                {"check_name": "debit_credit_balance", "severity": "critical", "passed": False},
                {"check_name": "completeness_description", "severity": "warning", "passed": False},
            ],
        },
        "total": 4,
        "passed": 1,
        "failed": 3,
        "critical_failures": 2,
        "pass_rate": 0.25,
    }


@pytest.fixture
def sample_write_counts():
    """Sample write counts from contract writers."""
    return {
        "gl_entry": 1000,
        "trial_balance": 150,
        "ap_invoice": 200,
        "ar_invoice": 180,
        "vendor": 50,
        "customer": 75,
        "chart_of_accounts": 300,
    }

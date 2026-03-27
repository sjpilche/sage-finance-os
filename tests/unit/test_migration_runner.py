"""Tests for app.core.migration_runner — retry logic and file discovery."""

import time
from unittest.mock import MagicMock, patch, call

import psycopg2
import pytest

from app.core.migration_runner import _connect_with_retry, _get_migration_files, MAX_RETRIES


def test_connect_succeeds_first_try():
    with patch("app.core.migration_runner.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        result = _connect_with_retry("postgresql://test@localhost/test")
        assert result == mock_conn
        mock_connect.assert_called_once()


def test_connect_retries_on_failure():
    with patch("app.core.migration_runner.psycopg2.connect") as mock_connect:
        with patch("app.core.migration_runner.time.sleep") as mock_sleep:
            mock_connect.side_effect = [
                psycopg2.OperationalError("refused"),
                psycopg2.OperationalError("refused"),
                MagicMock(),  # succeeds on 3rd try
            ]
            result = _connect_with_retry("postgresql://test@localhost/test")
            assert result is not None
            assert mock_connect.call_count == 3
            assert mock_sleep.call_count == 2
            # Exponential backoff: 1s, 2s
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)


def test_connect_raises_after_max_retries():
    with patch("app.core.migration_runner.psycopg2.connect") as mock_connect:
        with patch("app.core.migration_runner.time.sleep"):
            mock_connect.side_effect = psycopg2.OperationalError("refused")
            with pytest.raises(psycopg2.OperationalError, match="refused"):
                _connect_with_retry("postgresql://test@localhost/test")
            assert mock_connect.call_count == MAX_RETRIES


def test_connect_exponential_backoff():
    with patch("app.core.migration_runner.psycopg2.connect") as mock_connect:
        with patch("app.core.migration_runner.time.sleep") as mock_sleep:
            mock_connect.side_effect = [
                psycopg2.OperationalError("refused"),
                psycopg2.OperationalError("refused"),
                psycopg2.OperationalError("refused"),
                psycopg2.OperationalError("refused"),
                MagicMock(),  # succeeds on 5th try
            ]
            _connect_with_retry("postgresql://test@localhost/test")
            # Backoffs: 1, 2, 4, 8
            expected_sleeps = [call(1), call(2), call(4), call(8)]
            assert mock_sleep.call_args_list == expected_sleeps


def test_migration_files_discovered():
    """Verify migration file discovery finds numbered SQL files."""
    files = _get_migration_files()
    assert len(files) >= 7  # 001-007 migrations
    # All should be sorted
    ids = [f[0] for f in files]
    assert ids == sorted(ids)
    # All should start with 3-digit prefix
    for mid, path in files:
        assert mid[:3].isdigit()
        assert path.suffix == ".sql"

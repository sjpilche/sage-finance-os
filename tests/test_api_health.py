"""Tests for health check API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


@patch("app.core.migration_runner.run_migrations", return_value=0)
@patch("app.core.db.get_pool")
@patch("app.workflows.scheduler.register_default_jobs")
@patch("app.workflows.scheduler.start_scheduler")
def test_health_returns_200(mock_scheduler_start, mock_scheduler_reg, mock_pool, mock_migrate):
    mock_pool.return_value = AsyncMock()
    from app.main import app
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "healthy"
    assert body["data"]["service"] == "sage-finance-os"
    assert "meta" in body


@patch("app.core.migration_runner.run_migrations", return_value=0)
@patch("app.core.db.get_pool")
@patch("app.workflows.scheduler.register_default_jobs")
@patch("app.workflows.scheduler.start_scheduler")
def test_health_response_has_meta(mock_scheduler_start, mock_scheduler_reg, mock_pool, mock_migrate):
    mock_pool.return_value = AsyncMock()
    from app.main import app
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/health")
    meta = response.json()["meta"]
    assert "generated_at" in meta
    assert "version" in meta

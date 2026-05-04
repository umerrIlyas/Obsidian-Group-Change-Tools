"""Smoke test for the FastAPI app: /health responds with the configured providers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    from changetools.config import get_settings
    from changetools.main import create_app

    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "groq"
    assert body["llm_credentials"] is True
    assert body["embedding_provider"] == "local"


def test_request_id_header_propagated(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-Id": "test-req-id"})
    assert response.headers["X-Request-Id"] == "test-req-id"


def test_request_id_generated_when_absent(client: TestClient) -> None:
    response = client.get("/health")
    assert "X-Request-Id" in response.headers
    assert len(response.headers["X-Request-Id"]) > 10

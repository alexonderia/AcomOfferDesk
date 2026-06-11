from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_uow
from app.api.v1 import router as v1_router
from app.core.config import settings
from app.services.max_start import MaxStartResult


@pytest.fixture
def max_api_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "max_bot_enabled", True)

    class DummyUow:
        max_users = None
        users = None
        requests = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)

    app = FastAPI()
    app.include_router(v1_router)
    dummy_uow = DummyUow()

    async def override_uow():
        return dummy_uow

    app.dependency_overrides[get_uow] = override_uow
    return TestClient(app), dummy_uow


def test_max_start_returns_403_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "max_bot_enabled", False)
    app = FastAPI()
    app.include_router(v1_router)
    client = TestClient(app)

    response = client.post("/api/v1/max/start", json={"max_user_id": "123"})

    assert response.status_code == 403


def test_max_start_success(max_api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _dummy_uow = max_api_client
    expected = MaxStartResult(action="pending", registration_url=None, requests=[])
    monkeypatch.setattr(
        "app.api.v1.max.MaxStartService.handle_start",
        AsyncMock(return_value=expected),
    )

    response = client.post("/api/v1/max/start", json={"max_user_id": "123"})

    assert response.status_code == 200
    assert response.json() == {"action": "pending", "registration_url": None, "requests": []}


def test_max_start_invalid_payload_returns_422(max_api_client) -> None:
    client, _dummy_uow = max_api_client

    response = client.post("/api/v1/max/start", json={})

    assert response.status_code == 422

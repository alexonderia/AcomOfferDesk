from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.dependencies import get_uow
from app.api.v1 import router as v1_router
from app.core.config import settings
from app.domain.exceptions import Forbidden
from app.services.max_start import MaxStartResult


@pytest.fixture
def max_api_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "max_bot_enabled", True)
    monkeypatch.setattr(settings, "bot_api_shared_secret", None)

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

    @app.exception_handler(Forbidden)
    async def forbidden_handler(request: Request, exc: Forbidden) -> JSONResponse:
        _ = request
        return JSONResponse(status_code=403, content={"detail": str(exc) or "Forbidden"})

    app.include_router(v1_router)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/api/v1/max/start", json={"max_user_id": "123"})

    assert response.status_code == 403


def test_max_start_success(max_api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _dummy_uow = max_api_client
    expected = MaxStartResult(action="pending", registration_url=None, existing_account_link_token=None, requests=[])
    monkeypatch.setattr(
        "app.api.v1.max.MaxStartService.handle_start",
        AsyncMock(return_value=expected),
    )

    response = client.post("/api/v1/max/start", json={"max_user_id": "123"})

    assert response.status_code == 200
    assert response.json() == {
        "action": "pending",
        "registration_url": None,
        "existing_account_link_token": None,
        "requests": [],
    }


def test_max_start_invalid_payload_returns_422(max_api_client) -> None:
    client, _dummy_uow = max_api_client

    response = client.post("/api/v1/max/start", json={})

    assert response.status_code == 422


def _app_with_forbidden_handler() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(Forbidden)
    async def forbidden_handler(request: Request, exc: Forbidden) -> JSONResponse:
        _ = request
        return JSONResponse(status_code=403, content={"detail": str(exc) or "Forbidden"})

    app.include_router(v1_router)
    return app


def test_max_start_forbidden_without_secret_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "max_bot_enabled", True)
    monkeypatch.setattr(settings, "bot_api_shared_secret", "s3cr3t")
    client = TestClient(_app_with_forbidden_handler(), raise_server_exceptions=False)

    response = client.post("/api/v1/max/start", json={"max_user_id": "123"})

    assert response.status_code == 403


def test_max_start_forbidden_with_wrong_secret_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "max_bot_enabled", True)
    monkeypatch.setattr(settings, "bot_api_shared_secret", "s3cr3t")
    client = TestClient(_app_with_forbidden_handler(), raise_server_exceptions=False)

    response = client.post(
        "/api/v1/max/start",
        json={"max_user_id": "123"},
        headers={"X-Bot-Api-Secret": "wrong"},
    )

    assert response.status_code == 403


def test_max_start_succeeds_with_correct_secret_header(
    max_api_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _dummy_uow = max_api_client
    monkeypatch.setattr(settings, "bot_api_shared_secret", "s3cr3t")
    expected = MaxStartResult(action="pending", registration_url=None, existing_account_link_token=None, requests=[])
    monkeypatch.setattr(
        "app.api.v1.max.MaxStartService.handle_start",
        AsyncMock(return_value=expected),
    )

    response = client.post(
        "/api/v1/max/start",
        json={"max_user_id": "123"},
        headers={"X-Bot-Api-Secret": "s3cr3t"},
    )

    assert response.status_code == 200

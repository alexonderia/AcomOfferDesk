from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest

os.environ.setdefault("MAX_BOT_TOKEN", "test-token")
os.environ.setdefault("BACKEND_BASE_URL", "http://backend:8000")

from app.services.backend_client import BackendClient, BackendClientError


@pytest.mark.asyncio
async def test_start_sends_payload() -> None:
    client = BackendClient(base_url="http://backend:8000", timeout_seconds=5.0)
    mock_response = httpx.Response(
        200,
        json={
            "action": "register",
            "registration_url": "/api/v1/auth/oidc/register?max_token=abc",
            "requests": [],
        },
        request=httpx.Request("POST", "http://backend:8000/api/v1/max/start"),
    )

    with patch("app.services.backend_client.httpx.AsyncClient") as async_client_cls:
        async_client = AsyncMock()
        async_client.__aenter__.return_value = async_client
        async_client.post.return_value = mock_response
        async_client_cls.return_value = async_client

        result = await client.start("123", username="user")

    async_client.post.assert_awaited_once()
    sent_json = async_client.post.await_args.kwargs["json"]
    assert sent_json["max_user_id"] == "123"
    assert sent_json["username"] == "user"
    assert result.action == "register"
    assert result.registration_url == "http://backend:8000/api/v1/auth/oidc/register?max_token=abc"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "action"),
    [
        ({"action": "pending", "requests": []}, "pending"),
        ({"action": "blocked", "requests": []}, "blocked"),
        (
            {
                "action": "open_requests",
                "existing_account_link_token": None,
                "requests": [
                    {
                        "id": "1",
                        "description": "Test",
                        "deadline_at": "2026-06-10T12:00:00+00:00",
                        "url": "https://example.com/requests/1",
                    }
                ],
            },
            "open_requests",
        ),
    ],
)
async def test_start_parses_actions(payload: dict, action: str) -> None:
    client = BackendClient(base_url="http://backend:8000", timeout_seconds=5.0)
    mock_response = httpx.Response(
        200,
        json=payload,
        request=httpx.Request("POST", "http://backend:8000/api/v1/max/start"),
    )

    with patch("app.services.backend_client.httpx.AsyncClient") as async_client_cls:
        async_client = AsyncMock()
        async_client.__aenter__.return_value = async_client
        async_client.post.return_value = mock_response
        async_client_cls.return_value = async_client

        result = await client.start("123")

    assert result.action == action


@pytest.mark.asyncio
async def test_start_timeout_raises_backend_client_error() -> None:
    client = BackendClient(base_url="http://backend:8000", timeout_seconds=5.0)

    with patch("app.services.backend_client.httpx.AsyncClient") as async_client_cls:
        async_client = AsyncMock()
        async_client.__aenter__.return_value = async_client
        async_client.post.side_effect = httpx.TimeoutException("timeout")
        async_client_cls.return_value = async_client

        with pytest.raises(BackendClientError):
            await client.start("123")


@pytest.mark.asyncio
async def test_start_500_raises_backend_client_error() -> None:
    client = BackendClient(base_url="http://backend:8000", timeout_seconds=5.0)
    mock_response = httpx.Response(
        500,
        json={"detail": "error"},
        request=httpx.Request("POST", "http://backend:8000/api/v1/max/start"),
    )

    with patch("app.services.backend_client.httpx.AsyncClient") as async_client_cls:
        async_client = AsyncMock()
        async_client.__aenter__.return_value = async_client
        async_client.post.return_value = mock_response
        async_client_cls.return_value = async_client

        with pytest.raises(BackendClientError):
            await client.start("123")


@pytest.mark.asyncio
async def test_start_invalid_json_raises_backend_client_error() -> None:
    client = BackendClient(base_url="http://backend:8000", timeout_seconds=5.0)
    mock_response = httpx.Response(
        200,
        content=b"not-json",
        request=httpx.Request("POST", "http://backend:8000/api/v1/max/start"),
    )

    with patch("app.services.backend_client.httpx.AsyncClient") as async_client_cls:
        async_client = AsyncMock()
        async_client.__aenter__.return_value = async_client
        async_client.post.return_value = mock_response
        async_client_cls.return_value = async_client

        with pytest.raises(BackendClientError):
            await client.start("123")


@pytest.mark.asyncio
async def test_start_unknown_action_raises_backend_client_error() -> None:
    client = BackendClient(base_url="http://backend:8000", timeout_seconds=5.0)
    mock_response = httpx.Response(
        200,
        json={"action": "unknown"},
        request=httpx.Request("POST", "http://backend:8000/api/v1/max/start"),
    )

    with patch("app.services.backend_client.httpx.AsyncClient") as async_client_cls:
        async_client = AsyncMock()
        async_client.__aenter__.return_value = async_client
        async_client.post.return_value = mock_response
        async_client_cls.return_value = async_client

        with pytest.raises(BackendClientError):
            await client.start("123")

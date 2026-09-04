from __future__ import annotations

import pytest
from starlette.requests import Request

from app.api.v1 import auth


def _request(
    client_ip: str,
    *,
    forwarded_for: str | None = None,
    real_ip: str | None = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for:
        headers.append((b"x-forwarded-for", forwarded_for.encode("ascii")))
    if real_ip:
        headers.append((b"x-real-ip", real_ip.encode("ascii")))
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/password-reset/request",
            "headers": headers,
            "scheme": "https",
            "server": ("app.example", 443),
            "client": (client_ip, 12345),
        }
    )


class _MissingRepository:
    async def get_by_id(self, _value):
        return None


class _Uow:
    def __init__(self) -> None:
        self.users = _MissingRepository()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None


@pytest.mark.asyncio
async def test_password_reset_limiter_is_bounded_for_unique_logins() -> None:
    limiter = auth.PasswordResetRateLimiter(
        attempts=100,
        window_seconds=900,
        max_buckets=4,
    )

    for index in range(50):
        assert await limiter.allow(
            client_ip="203.0.113.10",
            login=f"user-{index}",
        )

    assert limiter.bucket_count == 5


@pytest.mark.asyncio
async def test_password_reset_per_ip_limit_cannot_be_bypassed() -> None:
    limiter = auth.PasswordResetRateLimiter(
        attempts=2,
        window_seconds=900,
        max_buckets=20,
    )

    assert await limiter.allow(client_ip="203.0.113.10", login="first")
    assert await limiter.allow(client_ip="203.0.113.10", login="second")
    assert not await limiter.allow(client_ip="203.0.113.10", login="third")


@pytest.mark.asyncio
async def test_password_reset_limiter_normalizes_login() -> None:
    limiter = auth.PasswordResetRateLimiter(
        attempts=1,
        window_seconds=900,
        max_buckets=20,
    )

    assert await limiter.allow(
        client_ip="203.0.113.10",
        login="  Example.User ",
    )
    assert not await limiter.allow(
        client_ip="203.0.113.11",
        login="example.user",
    )


@pytest.mark.asyncio
async def test_rate_limited_password_reset_keeps_generic_response(monkeypatch) -> None:
    limiter = auth.PasswordResetRateLimiter(
        attempts=1,
        window_seconds=900,
        max_buckets=20,
    )
    monkeypatch.setattr(auth, "password_reset_rate_limiter", limiter)
    request = _request("203.0.113.10")

    first = await auth.request_password_reset(
        auth.PasswordResetRequest(login="unknown-user"),
        request,
        _Uow(),
    )
    second = await auth.request_password_reset(
        auth.PasswordResetRequest(login="different-user"),
        request,
        _Uow(),
    )

    assert first.detail == second.detail
    assert "Если учётная запись существует" in second.detail


def test_backend_client_ip_uses_trusted_forwarded_chain(monkeypatch) -> None:
    monkeypatch.setattr(auth.settings, "trusted_proxy_cidrs_csv", "172.16.0.0/12")
    request = _request(
        "172.18.0.5",
        forwarded_for="198.51.100.20, 172.18.0.2",
        real_ip="172.18.0.2",
    )

    assert auth._client_ip(request) == "198.51.100.20"


def test_backend_client_ip_rejects_untrusted_forwarded_header(monkeypatch) -> None:
    monkeypatch.setattr(auth.settings, "trusted_proxy_cidrs_csv", "172.16.0.0/12")
    request = _request(
        "203.0.113.30",
        forwarded_for="198.51.100.99",
        real_ip="198.51.100.99",
    )

    assert auth._client_ip(request) == "203.0.113.30"

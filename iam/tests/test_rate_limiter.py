from __future__ import annotations

import pytest

from shared.client_ip import resolve_client_ip
from shared.rate_limiter import SlidingWindowRateLimiter

from iam_app.api import LoginRateLimiter
from iam_app.errors import RateLimited


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.mark.asyncio
async def test_rate_limiter_removes_expired_buckets_globally() -> None:
    clock = _Clock()
    limiter = SlidingWindowRateLimiter(
        attempts=2,
        window_seconds=10,
        max_buckets=10,
        cleanup_interval_seconds=1,
        clock=clock,
    )
    assert await limiter.allow("first")
    assert await limiter.allow("second")
    assert limiter.bucket_count == 2

    clock.now = 11
    assert await limiter.allow("current")

    assert limiter.bucket_count == 1


@pytest.mark.asyncio
async def test_rate_limiter_has_hard_bucket_bound_for_unique_keys() -> None:
    limiter = SlidingWindowRateLimiter(
        attempts=2,
        window_seconds=60,
        max_buckets=3,
    )

    for index in range(20):
        assert await limiter.allow(f"login:user-{index}")

    assert limiter.bucket_count == 3


@pytest.mark.asyncio
async def test_login_rate_limit_cannot_be_bypassed_with_different_logins() -> None:
    limiter = LoginRateLimiter(attempts=2, window_seconds=60, max_buckets=20)

    await limiter.check(client_ip="203.0.113.10", login="first")
    await limiter.check(client_ip="203.0.113.10", login="second")

    with pytest.raises(RateLimited):
        await limiter.check(client_ip="203.0.113.10", login="third")


@pytest.mark.asyncio
async def test_login_rate_limiter_stays_bounded_for_unique_logins() -> None:
    limiter = LoginRateLimiter(attempts=100, window_seconds=60, max_buckets=4)

    for index in range(50):
        await limiter.check(
            client_ip="203.0.113.10",
            login=f"user-{index}",
        )

    assert limiter.bucket_count == 5


@pytest.mark.asyncio
async def test_login_rate_limit_normalizes_login() -> None:
    limiter = LoginRateLimiter(attempts=1, window_seconds=60, max_buckets=20)

    await limiter.check(client_ip="203.0.113.10", login="  Example.User ")

    with pytest.raises(RateLimited):
        await limiter.check(client_ip="203.0.113.11", login="example.user")


def test_client_ip_uses_forwarded_chain_from_trusted_proxy() -> None:
    assert resolve_client_ip(
        peer_host="172.18.0.5",
        forwarded_for="198.51.100.20, 172.18.0.2",
        real_ip="172.18.0.2",
        trusted_proxy_cidrs=("172.16.0.0/12",),
    ) == "198.51.100.20"


def test_client_ip_ignores_spoofed_header_from_untrusted_peer() -> None:
    assert resolve_client_ip(
        peer_host="203.0.113.30",
        forwarded_for="198.51.100.99",
        real_ip="198.51.100.99",
        trusted_proxy_cidrs=("172.16.0.0/12",),
    ) == "203.0.113.30"

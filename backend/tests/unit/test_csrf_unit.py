from __future__ import annotations

from starlette.requests import Request

from app.core.config import settings
from app.core.csrf import csrf_failure_reason


def _request(*, method: str, cookie: str = "", csrf: str = "", origin: str = "") -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if cookie:
        headers.append((b"cookie", cookie.encode("ascii")))
    if csrf:
        headers.append((b"x-csrf-token", csrf.encode("ascii")))
    if origin:
        headers.append((b"origin", origin.encode("ascii")))
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/v1/users/me/profile",
            "headers": headers,
            "scheme": "https",
            "server": ("app.example", 443),
            "client": ("127.0.0.1", 12345),
        }
    )


def test_safe_request_and_unauthenticated_post_do_not_require_csrf() -> None:
    assert csrf_failure_reason(_request(method="GET")) is None
    assert csrf_failure_reason(_request(method="POST")) is None


def test_authenticated_post_requires_matching_double_submit_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "web_base_url", "https://app.example")
    auth_cookie = f"{settings.iam_access_cookie_name}=access"
    assert csrf_failure_reason(_request(method="POST", cookie=auth_cookie)) == "csrf_token_mismatch"
    cookie = f"{auth_cookie}; {settings.iam_csrf_cookie_name}=csrf-value"
    assert (
        csrf_failure_reason(
            _request(method="POST", cookie=cookie, csrf="other", origin="https://app.example")
        )
        == "csrf_token_mismatch"
    )


def test_authenticated_post_rejects_cross_origin_and_accepts_exact_origin(monkeypatch) -> None:
    monkeypatch.setattr(settings, "web_base_url", "https://app.example")
    cookie = (
        f"{settings.iam_access_cookie_name}=access; "
        f"{settings.iam_csrf_cookie_name}=csrf-value"
    )
    assert (
        csrf_failure_reason(
            _request(method="POST", cookie=cookie, csrf="csrf-value", origin="https://evil.example")
        )
        == "origin_not_allowed"
    )
    assert (
        csrf_failure_reason(
            _request(method="POST", cookie=cookie, csrf="csrf-value", origin="https://app.example")
        )
        is None
    )

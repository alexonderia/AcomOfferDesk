from __future__ import annotations

import hmac
from urllib.parse import urlparse

from fastapi import Request

from app.core.config import settings


_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Password setup/reset authenticate with a one-time token in the form body,
# not with the browser session. A plain HTML form cannot send X-CSRF-Token,
# so the session CSRF check would block the legitimate password flow.
_TOKEN_FORM_PATHS = frozenset(
    {
        "/api/v1/auth/password/setup",
        "/api/v1/auth/password/reset",
    }
)


def _allowed_origins() -> set[str]:
    values = {
        value.rstrip("/")
        for value in (
            *settings.resolved_cors_allow_origins,
            settings.web_base_url,
            settings.public_backend_base_url,
        )
        if value
    }
    return values


def csrf_failure_reason(request: Request) -> str | None:
    if request.method.upper() in _SAFE_METHODS:
        return None
    if request.url.path in _TOKEN_FORM_PATHS:
        return None
    has_auth_cookie = bool(
        request.cookies.get(settings.iam_access_cookie_name)
        or request.cookies.get(settings.iam_refresh_cookie_name)
    )
    if not has_auth_cookie:
        return None

    cookie_token = request.cookies.get(settings.iam_csrf_cookie_name, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        return "csrf_token_mismatch"

    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return "missing_origin"
    parsed = urlparse(source)
    source_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    if source_origin not in _allowed_origins():
        return "origin_not_allowed"
    return None

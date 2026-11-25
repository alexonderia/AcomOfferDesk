from __future__ import annotations

import hmac
import logging
from urllib.parse import parse_qs, urlparse

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings


_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_PASSWORD_FORM_PATHS = {"/api/v1/auth/password/setup", "/api/v1/auth/password/reset"}
logger = logging.getLogger(__name__)


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


def csrf_failure_reason(request: Request, *, form_token: str = "") -> str | None:
    if request.method.upper() in _SAFE_METHODS:
        return None
    has_auth_cookie = bool(
        request.cookies.get(settings.iam_access_cookie_name)
        or request.cookies.get(settings.iam_refresh_cookie_name)
    )
    if not has_auth_cookie:
        return None

    cookie_token = request.cookies.get(settings.iam_csrf_cookie_name, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if request.url.path in _PASSWORD_FORM_PATHS and not header_token:
        header_token = form_token
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token.encode("utf-8"), header_token.encode("utf-8")):
        return "csrf_token_mismatch"

    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return "missing_origin"
    parsed = urlparse(source)
    source_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    if source_origin not in _allowed_origins():
        return "origin_not_allowed"
    return None


async def csrf_protection(request: Request, call_next):
    form_token = ""
    if (
        request.method == "POST"
        and request.url.path in _PASSWORD_FORM_PATHS
        and request.headers.get("content-type", "").split(";", 1)[0] == "application/x-www-form-urlencoded"
    ):
        # Read the cached body so the downstream password form receives it unchanged.
        body = await request.body()
        if len(body) <= 8192:
            try:
                tokens = parse_qs(body.decode("utf-8"), max_num_fields=8).get("csrf_token", [])
                if len(tokens) == 1:
                    form_token = tokens[0]
            except (UnicodeDecodeError, ValueError):
                pass
    failure_reason = csrf_failure_reason(request, form_token=form_token)
    if failure_reason is not None:
        logger.warning("csrf_request_rejected path=%s method=%s reason=%s", request.url.path, request.method, failure_reason)
        return JSONResponse(status_code=403, content={"detail": "Запрос отклонён проверкой безопасности."})
    return await call_next(request)

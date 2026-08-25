from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1 import auth as auth_api
from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import AuthenticationUnavailable, ServiceUnavailable, Unauthorized
from app.infrastructure.iam_client import IamTokenBundle


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_api.router, prefix="/api/v1")

    @app.exception_handler(Unauthorized)
    async def unauthorized_handler(request, exc):
        _ = request
        return JSONResponse(status_code=401, content={"detail": str(exc) or "Unauthorized"})

    @app.exception_handler(ServiceUnavailable)
    async def unavailable_handler(request, exc):
        _ = request
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "reason_code": exc.reason_code},
        )

    return app


def _current_user() -> CurrentUser:
    return CurrentUser(
        user_id="user-1",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="economist",
        role_id=6,
        status="active",
        permissions=frozenset({"requests.read"}),
    )


def _bundle() -> IamTokenBundle:
    return IamTokenBundle(
        access_token="new-access-token",
        access_token_expires_at=4_102_444_800,
        refresh_token="new-refresh-token",
        refresh_token_expires_at=4_102_531_200,
    )


def _set_refresh_cookie(client: TestClient) -> None:
    client.cookies.set(
        settings.iam_refresh_cookie_name,
        "old-refresh-token",
        path="/api/v1/auth",
    )


def test_refresh_returns_session_and_rotated_http_only_cookies(monkeypatch) -> None:
    class _IamClient:
        async def refresh(self, refresh_token: str) -> IamTokenBundle:
            assert refresh_token == "old-refresh-token"
            return _bundle()

    async def _resolve_current_user(_claims) -> CurrentUser:
        return _current_user()

    monkeypatch.setattr(auth_api, "IamClient", _IamClient)
    monkeypatch.setattr(auth_api, "decode_iam_access_token", lambda _token: object())
    monkeypatch.setattr(auth_api, "resolve_iam_current_user", _resolve_current_user)

    with TestClient(_build_app()) as client:
        _set_refresh_cookie(client)
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json()["data"]["permissions"] == ["requests.read"]
    set_cookies = response.headers.get_list("set-cookie")
    assert any(f"{settings.iam_access_cookie_name}=new-access-token" in value for value in set_cookies)
    assert any(f"{settings.iam_refresh_cookie_name}=new-refresh-token" in value for value in set_cookies)
    assert all("HttpOnly" in value for value in set_cookies if settings.iam_csrf_cookie_name not in value)


def test_refresh_without_cookie_is_terminal_and_does_not_create_session() -> None:
    with TestClient(_build_app()) as client:
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.headers.get_list("set-cookie") == []


def test_expired_or_revoked_refresh_clears_auth_cookies(monkeypatch) -> None:
    class _IamClient:
        async def refresh(self, _refresh_token: str) -> IamTokenBundle:
            raise Unauthorized("IAM request rejected")

    monkeypatch.setattr(auth_api, "IamClient", _IamClient)

    with TestClient(_build_app()) as client:
        _set_refresh_cookie(client)
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    set_cookies = response.headers.get_list("set-cookie")
    assert any(settings.iam_access_cookie_name in value and "Max-Age=0" in value for value in set_cookies)
    assert any(settings.iam_refresh_cookie_name in value and "Max-Age=0" in value for value in set_cookies)


def test_iam_unavailable_returns_typed_503_without_clearing_refresh_cookie(monkeypatch) -> None:
    class _IamClient:
        async def refresh(self, _refresh_token: str) -> IamTokenBundle:
            raise AuthenticationUnavailable()

    monkeypatch.setattr(auth_api, "IamClient", _IamClient)

    with TestClient(_build_app()) as client:
        _set_refresh_cookie(client)
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 503
    assert response.json()["reason_code"] == "AUTH_SERVICE_UNAVAILABLE"
    assert response.headers.get_list("set-cookie") == []


def test_identity_rejected_after_iam_refresh_is_terminal(monkeypatch) -> None:
    class _IamClient:
        async def refresh(self, _refresh_token: str) -> IamTokenBundle:
            return _bundle()

    async def _reject_identity(_claims) -> CurrentUser:
        raise Unauthorized("Invalid IAM binding")

    monkeypatch.setattr(auth_api, "IamClient", _IamClient)
    monkeypatch.setattr(auth_api, "decode_iam_access_token", lambda _token: object())
    monkeypatch.setattr(auth_api, "resolve_iam_current_user", _reject_identity)

    with TestClient(_build_app()) as client:
        _set_refresh_cookie(client)
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert any(
        settings.iam_refresh_cookie_name in value and "Max-Age=0" in value
        for value in response.headers.get_list("set-cookie")
    )

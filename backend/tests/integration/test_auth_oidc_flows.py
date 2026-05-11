"""Integration tests for OIDC callback/refresh/logout negative paths."""

from __future__ import annotations

from types import SimpleNamespace

from app.api.v1 import auth as auth_api
from app.core.config import settings
from app.core.oidc_state_tokens import build_oidc_authorization_start
from app.domain.exceptions import Conflict, Forbidden, Unauthorized
from app.services.keycloak_oidc import KeycloakAccessTokenClaims, KeycloakTokenBundle


class _NoopUow:
    async def __aenter__(self) -> "_NoopUow":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


class _ExistingEmailUsersRepo:
    async def list_by_email(self, *, email: str):
        _ = email
        return [SimpleNamespace(id="existing-user")]


class _ExistingEmailUow(_NoopUow):
    def __init__(self) -> None:
        self.users = _ExistingEmailUsersRepo()


def _build_keycloak_claims(*, subject: str = "kc-subject", email: str | None = None) -> KeycloakAccessTokenClaims:
    return KeycloakAccessTokenClaims(
        subject=subject,
        issuer=settings.resolved_keycloak_issuer_url,
        issued_at=1700000000,
        expires_at=1700003600,
        preferred_username="user",
        full_name="User Name",
        given_name="User",
        family_name="Name",
        email=email,
        email_verified=True,
        realm_roles=frozenset(),
        api_roles=frozenset(),
    )


def test_callback_without_code_or_state_returns_session_expired_redirect(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    response = test_client.get("/api/v1/auth/callback", follow_redirects=False)

    assert response.status_code == 302
    assert "auth_error=session_expired" in response.headers["location"]


def test_callback_with_wrong_state_returns_session_expired_redirect(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    start = build_oidc_authorization_start(next_path="/", flow="login", redirect_uri=settings.keycloak_callback_url)

    response = test_client.get(
        "/api/v1/auth/callback",
        params={"code": "code-1", "state": "different-state"},
        cookies={settings.keycloak_state_cookie_name: start.cookie_token},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "auth_error=session_expired" in response.headers["location"]


def test_callback_with_missing_state_cookie_returns_session_expired_redirect(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    response = test_client.get(
        "/api/v1/auth/callback",
        params={"code": "code-1", "state": "state-1"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "auth_error=session_expired" in response.headers["location"]


def test_callback_with_broken_state_cookie_returns_session_expired_redirect(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    response = test_client.get(
        "/api/v1/auth/callback",
        params={"code": "code-1", "state": "state-1"},
        cookies={settings.keycloak_state_cookie_name: "broken-cookie-token"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "auth_error=session_expired" in response.headers["location"]


def test_callback_registration_invite_email_mismatch_redirects_invalid(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    start = build_oidc_authorization_start(
        next_path="/account",
        flow="register",
        redirect_uri=settings.keycloak_callback_url,
        registration_email="invite@example.com",
    )

    async def _fake_exchange_code_for_tokens(*, code: str, code_verifier: str, redirect_uri: str | None):
        _ = (code, code_verifier, redirect_uri)
        return KeycloakTokenBundle(
            access_token="access",
            refresh_token="refresh",
            expires_in=300,
            refresh_expires_in=3600,
        )

    async def _fake_decode_keycloak_access_token(token: str):
        _ = token
        return _build_keycloak_claims(email="another@example.com")

    monkeypatch.setattr(auth_api, "exchange_code_for_tokens", _fake_exchange_code_for_tokens)
    monkeypatch.setattr(auth_api, "decode_keycloak_access_token", _fake_decode_keycloak_access_token)

    response = test_client.get(
        "/api/v1/auth/callback",
        params={"code": "code-1", "state": start.state},
        cookies={settings.keycloak_state_cookie_name: start.cookie_token},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "registration-link-status?reason=invalid" in response.headers["location"]


def test_callback_repeated_registration_with_existing_email_redirects_already_registered(
    test_client,
    monkeypatch,
    set_uow,
):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    set_uow(_ExistingEmailUow())
    start = build_oidc_authorization_start(
        next_path="/account",
        flow="register",
        redirect_uri=settings.keycloak_callback_url,
        registration_email="invite@example.com",
    )

    async def _fake_exchange_code_for_tokens(*, code: str, code_verifier: str, redirect_uri: str | None):
        _ = (code, code_verifier, redirect_uri)
        return KeycloakTokenBundle(
            access_token="access",
            refresh_token="refresh",
            expires_in=300,
            refresh_expires_in=3600,
        )

    async def _fake_decode_keycloak_access_token(token: str):
        _ = token
        return _build_keycloak_claims(email="invite@example.com")

    monkeypatch.setattr(auth_api, "exchange_code_for_tokens", _fake_exchange_code_for_tokens)
    monkeypatch.setattr(auth_api, "decode_keycloak_access_token", _fake_decode_keycloak_access_token)

    response = test_client.get(
        "/api/v1/auth/callback",
        params={"code": "code-1", "state": start.state},
        cookies={settings.keycloak_state_cookie_name: start.cookie_token},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "registration-link-status?reason=already_registered" in response.headers["location"]


def test_refresh_without_cookie_returns_401(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    response = test_client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing credentials"


def test_refresh_with_invalid_cookie_returns_401_and_clears_cookie(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    async def _fake_refresh_tokens(*, refresh_token: str):
        _ = refresh_token
        raise Unauthorized("Invalid refresh")

    monkeypatch.setattr(auth_api, "refresh_tokens", _fake_refresh_tokens)

    response = test_client.post(
        "/api/v1/auth/refresh",
        cookies={settings.keycloak_refresh_cookie_name: "invalid-refresh"},
    )

    assert response.status_code == 401
    set_cookie_header = response.headers.get("set-cookie", "")
    assert settings.keycloak_refresh_cookie_name in set_cookie_header
    assert "Max-Age=0" in set_cookie_header


def test_logout_clears_cookie_even_if_keycloak_services_fail(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    async def _fake_logout_refresh_token(*, refresh_token: str) -> None:
        _ = refresh_token
        raise Forbidden("provider unavailable")

    async def _fake_decode_keycloak_access_token(token: str):
        _ = token
        return _build_keycloak_claims(subject="kc-user")

    async def _fake_logout_user_sessions(self, *, user_id: str) -> None:
        _ = (self, user_id)
        raise Conflict("admin api unavailable")

    monkeypatch.setattr(auth_api, "logout_refresh_token", _fake_logout_refresh_token)
    monkeypatch.setattr(auth_api, "looks_like_keycloak_token", lambda _token: True)
    monkeypatch.setattr(auth_api, "decode_keycloak_access_token", _fake_decode_keycloak_access_token)
    monkeypatch.setattr(auth_api.KeycloakAdminService, "logout_user_sessions", _fake_logout_user_sessions)

    response = test_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer token"},
        cookies={settings.keycloak_refresh_cookie_name: "refresh-token"},
    )

    assert response.status_code == 204
    set_cookie_header = response.headers.get("set-cookie", "")
    assert settings.keycloak_refresh_cookie_name in set_cookie_header

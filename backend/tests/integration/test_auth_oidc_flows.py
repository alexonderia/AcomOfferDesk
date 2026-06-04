"""Integration tests for OIDC callback/refresh/logout positive and negative paths."""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from app.api.v1 import auth as auth_api
from app.core.config import settings
from app.core.oidc_state_tokens import build_oidc_authorization_start
from app.core.registration_invite_tokens import RegistrationInviteTokenCodec
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


class _NoExistingEmailUsersRepo:
    async def list_by_email(self, *, email: str):
        _ = email
        return []

    async def get_role_by_id(self, role_id: int):
        return SimpleNamespace(role="Контрагент", id=role_id)


class _ExistingEmailUow(_NoopUow):
    def __init__(self) -> None:
        self.users = _ExistingEmailUsersRepo()


class _NoExistingEmailUow(_NoopUow):
    def __init__(self) -> None:
        self.users = _NoExistingEmailUsersRepo()
        self.user_auth_accounts = None
        self.user_contact_channels = None
        self.profiles = None


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
        middle_name=None,
        email=email,
        email_verified=True,
        realm_roles=frozenset(),
        api_roles=frozenset(),
    )


def _collect_set_cookie_headers(response) -> list[str]:
    raw_headers = getattr(response, "headers", None)
    if raw_headers is None:
        return []
    if hasattr(raw_headers, "get_list"):
        return raw_headers.get_list("set-cookie")
    single_header = raw_headers.get("set-cookie", "")
    return [single_header] if single_header else []


def _get_with_cookie(test_client, path: str, *, cookie_name: str, cookie_value: str, **kwargs):
    test_client.cookies.set(cookie_name, cookie_value)
    try:
        return test_client.get(path, **kwargs)
    finally:
        test_client.cookies.delete(cookie_name)


def _post_with_cookie(test_client, path: str, *, cookie_name: str, cookie_value: str, **kwargs):
    test_client.cookies.set(cookie_name, cookie_value)
    try:
        return test_client.post(path, **kwargs)
    finally:
        test_client.cookies.delete(cookie_name)


def test_callback_without_code_or_state_returns_session_expired_redirect(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    response = test_client.get("/api/v1/auth/callback", follow_redirects=False)

    assert response.status_code == 302
    assert "auth_error=session_expired" in response.headers["location"]


def test_callback_with_wrong_state_returns_session_expired_redirect(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    start = build_oidc_authorization_start(next_path="/", flow="login", redirect_uri=settings.keycloak_callback_url)

    response = _get_with_cookie(
        test_client,
        "/api/v1/auth/callback",
        cookie_name=settings.keycloak_state_cookie_name,
        cookie_value=start.cookie_token,
        params={"code": "code-1", "state": "different-state"},
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

    response = _get_with_cookie(
        test_client,
        "/api/v1/auth/callback",
        cookie_name=settings.keycloak_state_cookie_name,
        cookie_value="broken-cookie-token",
        params={"code": "code-1", "state": "state-1"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "auth_error=session_expired" in response.headers["location"]


def test_callback_with_valid_state_sets_refresh_cookie_and_redirects_to_spa(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    start = build_oidc_authorization_start(
        next_path="/pm-dashboard?tab=plan",
        flow="login",
        redirect_uri=settings.keycloak_callback_url,
    )
    observed: dict[str, object] = {}

    async def _fake_exchange_code_for_tokens(*, code: str, code_verifier: str, redirect_uri: str | None):
        observed["exchange_code"] = code
        observed["exchange_verifier"] = code_verifier
        observed["exchange_redirect_uri"] = redirect_uri
        return KeycloakTokenBundle(
            access_token="access-ok",
            refresh_token="refresh-ok",
            expires_in=300,
            refresh_expires_in=7200,
        )

    async def _fake_decode_keycloak_access_token(token: str):
        observed["decoded_token"] = token
        return _build_keycloak_claims(subject="kc-positive-login", email="linked@example.com")

    class _FakeIdentitySyncService:
        def __init__(self, **kwargs):
            observed["sync_ctor_keys"] = sorted(kwargs.keys())

        async def sync_keycloak_identity(self, claims: KeycloakAccessTokenClaims, *, allow_user_creation: bool = False):
            observed["sync_subject"] = claims.subject
            observed["sync_email"] = claims.email
            observed["allow_user_creation"] = allow_user_creation
            return SimpleNamespace(user=SimpleNamespace(id="linked-user", id_role=4, status="active"))

    monkeypatch.setattr(auth_api, "exchange_code_for_tokens", _fake_exchange_code_for_tokens)
    monkeypatch.setattr(auth_api, "decode_keycloak_access_token", _fake_decode_keycloak_access_token)
    monkeypatch.setattr(auth_api, "IdentitySyncService", _FakeIdentitySyncService)

    response = _get_with_cookie(
        test_client,
        "/api/v1/auth/callback",
        cookie_name=settings.keycloak_state_cookie_name,
        cookie_value=start.cookie_token,
        params={"code": "code-positive", "state": start.state},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("/auth/callback?next=/pm-dashboard?tab=plan")

    assert observed["exchange_code"] == "code-positive"
    assert observed["exchange_verifier"] == start.code_verifier
    assert observed["exchange_redirect_uri"] == settings.keycloak_callback_url
    assert observed["decoded_token"] == "access-ok"
    assert observed["sync_subject"] == "kc-positive-login"
    assert observed["sync_email"] == "linked@example.com"
    assert observed["allow_user_creation"] is False

    set_cookie_headers = _collect_set_cookie_headers(response)
    assert any(settings.keycloak_refresh_cookie_name in header and "Max-Age=7200" in header for header in set_cookie_headers)
    assert any(settings.keycloak_state_cookie_name in header and "Max-Age=0" in header for header in set_cookie_headers)


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

    response = _get_with_cookie(
        test_client,
        "/api/v1/auth/callback",
        cookie_name=settings.keycloak_state_cookie_name,
        cookie_value=start.cookie_token,
        params={"code": "code-1", "state": start.state},
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

    response = _get_with_cookie(
        test_client,
        "/api/v1/auth/callback",
        cookie_name=settings.keycloak_state_cookie_name,
        cookie_value=start.cookie_token,
        params={"code": "code-1", "state": start.state},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "registration-link-status?reason=already_registered" in response.headers["location"]


def test_invite_registration_callback_success_creates_review_identity_and_redirects_to_account(
    test_client,
    monkeypatch,
    set_uow,
):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    set_uow(_NoExistingEmailUow())
    invite_codec = RegistrationInviteTokenCodec(
        secret=settings.email_verification_secret,
        ttl_seconds=settings.tg_register_ttl_seconds,
    )
    invite_token = invite_codec.create_token(email="new-contractor@example.com")
    observed: dict[str, object] = {}

    begin_response = test_client.get(
        "/api/v1/auth/oidc/register",
        params={"invite_token": invite_token, "next_path": "/account"},
        follow_redirects=False,
    )

    assert begin_response.status_code == 302
    login_url = begin_response.headers["location"]
    parsed_login = urlsplit(login_url)
    login_query = parse_qs(parsed_login.query)
    assert login_query.get("prompt") == ["create"]
    assert "state" in login_query
    callback_state = login_query["state"][0]

    state_cookie = begin_response.cookies.get(settings.keycloak_state_cookie_name)
    assert state_cookie

    async def _fake_exchange_code_for_tokens(*, code: str, code_verifier: str, redirect_uri: str | None):
        observed["exchange_code"] = code
        observed["exchange_verifier"] = code_verifier
        observed["exchange_redirect_uri"] = redirect_uri
        return KeycloakTokenBundle(
            access_token="access-register",
            refresh_token="refresh-register",
            expires_in=300,
            refresh_expires_in=5400,
        )

    async def _fake_decode_keycloak_access_token(token: str):
        observed["decoded_token"] = token
        return _build_keycloak_claims(subject="kc-invite", email="new-contractor@example.com")

    def _fake_schedule_registration_review_required_notification(**kwargs):
        observed["review_notification_kwargs"] = kwargs
        return True

    class _FakeIdentitySyncService:
        def __init__(self, **kwargs):
            observed["sync_ctor_keys"] = sorted(kwargs.keys())

        async def sync_keycloak_identity(self, claims: KeycloakAccessTokenClaims, *, allow_user_creation: bool = False):
            observed["sync_subject"] = claims.subject
            observed["sync_email"] = claims.email
            observed["allow_user_creation"] = allow_user_creation
            return SimpleNamespace(
                user=SimpleNamespace(id="new_contractor", id_role=settings.contractor_role_id, status="review"),
                created_local_user=True,
            )

    monkeypatch.setattr(auth_api, "exchange_code_for_tokens", _fake_exchange_code_for_tokens)
    monkeypatch.setattr(auth_api, "decode_keycloak_access_token", _fake_decode_keycloak_access_token)
    monkeypatch.setattr(auth_api, "IdentitySyncService", _FakeIdentitySyncService)
    monkeypatch.setattr(
        auth_api,
        "schedule_registration_review_required_notification",
        _fake_schedule_registration_review_required_notification,
    )

    callback_response = _get_with_cookie(
        test_client,
        "/api/v1/auth/callback",
        cookie_name=settings.keycloak_state_cookie_name,
        cookie_value=state_cookie,
        params={"code": "register-code", "state": callback_state},
        follow_redirects=False,
    )

    assert callback_response.status_code == 302
    assert callback_response.headers["location"].endswith("/auth/callback?next=/account")
    assert observed["exchange_code"] == "register-code"
    assert observed["decoded_token"] == "access-register"
    assert observed["sync_subject"] == "kc-invite"
    assert observed["sync_email"] == "new-contractor@example.com"
    assert observed["allow_user_creation"] is True
    assert observed["review_notification_kwargs"]["user_id"] == "new_contractor"
    assert observed["review_notification_kwargs"]["actor_user_id"] == "new_contractor"
    assert observed["review_notification_kwargs"]["role_id"] == settings.contractor_role_id
    assert observed["review_notification_kwargs"]["source"] == "oidc_invite_registration"

    set_cookie_headers = _collect_set_cookie_headers(callback_response)
    assert any(settings.keycloak_refresh_cookie_name in header and "Max-Age=5400" in header for header in set_cookie_headers)
    assert any(settings.keycloak_state_cookie_name in header and "Max-Age=0" in header for header in set_cookie_headers)


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

    response = _post_with_cookie(
        test_client,
        "/api/v1/auth/refresh",
        cookie_name=settings.keycloak_refresh_cookie_name,
        cookie_value="invalid-refresh",
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

    response = _post_with_cookie(
        test_client,
        "/api/v1/auth/logout",
        cookie_name=settings.keycloak_refresh_cookie_name,
        cookie_value="refresh-token",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 204
    set_cookie_headers = _collect_set_cookie_headers(response)
    assert any(settings.keycloak_refresh_cookie_name in header for header in set_cookie_headers)


def test_logout_is_idempotent_without_cookie_and_tolerates_broken_bearer(test_client, monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    calls = {"provider_logout": 0, "decode": 0, "admin_logout": 0}

    async def _fake_logout_refresh_token(*, refresh_token: str) -> None:
        _ = refresh_token
        calls["provider_logout"] += 1

    async def _fake_decode_keycloak_access_token(token: str):
        _ = token
        calls["decode"] += 1
        raise Unauthorized("Broken bearer")

    async def _fake_logout_user_sessions(self, *, user_id: str) -> None:
        _ = (self, user_id)
        calls["admin_logout"] += 1

    monkeypatch.setattr(auth_api, "logout_refresh_token", _fake_logout_refresh_token)
    monkeypatch.setattr(auth_api, "looks_like_keycloak_token", lambda _token: True)
    monkeypatch.setattr(auth_api, "decode_keycloak_access_token", _fake_decode_keycloak_access_token)
    monkeypatch.setattr(auth_api.KeycloakAdminService, "logout_user_sessions", _fake_logout_user_sessions)

    first = test_client.post("/api/v1/auth/logout")
    second = test_client.post("/api/v1/auth/logout")
    broken_bearer = test_client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer broken-token"})

    assert first.status_code == 204
    assert second.status_code == 204
    assert broken_bearer.status_code == 204

    broken_set_cookie_headers = _collect_set_cookie_headers(broken_bearer)
    assert any(settings.keycloak_refresh_cookie_name in header and "Max-Age=0" in header for header in broken_set_cookie_headers)
    assert calls["provider_logout"] == 0
    assert calls["decode"] == 1
    assert calls["admin_logout"] == 0

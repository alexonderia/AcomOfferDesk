"""Session/auth contract tests for `/api/v1/auth/refresh`.

Focus:
- required fields are present in the session payload;
- permissions source is Keycloak-like role claims, not local role-id mapping.
- refresh token rotation and stale-cookie handling stay consistent.
"""

from app.api.v1 import auth as auth_api
from app.core.config import settings
from app.domain.exceptions import Unauthorized
from app.domain.permissions import PermissionCodes
from app.schemas.auth import LoginResponse
from app.services.keycloak_oidc import KeycloakTokenBundle


class _FakeUow:
    async def __aenter__(self) -> "_FakeUow":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def _post_with_cookie(test_client, path: str, *, cookie_name: str, cookie_value: str):
    test_client.cookies.set(cookie_name, cookie_value)
    try:
        return test_client.post(path)
    finally:
        test_client.cookies.delete(cookie_name)


def _collect_set_cookie_headers(response) -> list[str]:
    if hasattr(response.headers, "get_list"):
        return response.headers.get_list("set-cookie")
    single_header = response.headers.get("set-cookie", "")
    return [single_header] if single_header else []


def _build_login_response(*, access_token: str = "access-token") -> LoginResponse:
    return LoginResponse(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "access_token_expires_at": 999999,
            "user_id": "contractor-1",
            "login": "contractor-1",
            "role_id": settings.contractor_role_id,
            "status": "active",
            "auth_provider": "keycloak",
            "business_access": True,
            "onboarding_state": None,
            "permissions": [PermissionCodes.USERS_READ],
            "app_roles": ["app.contractor"],
            "delegation_roles": [],
        }
    )


def _build_login_payload(*, access_token: str = "access-token") -> dict[str, object]:
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "access_token_expires_at": 999999,
        "user_id": "contractor-1",
        "login": "contractor-1",
        "role_id": settings.contractor_role_id,
        "status": "active",
        "auth_provider": "keycloak",
        "business_access": True,
        "onboarding_state": None,
        "permissions": [PermissionCodes.USERS_READ],
        "app_roles": ["app.contractor"],
        "delegation_roles": [],
    }


def test_refresh_session_contract_contains_permissions_and_roles(test_client, monkeypatch, set_uow):
    set_uow(_FakeUow())
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    async def _fake_refresh_tokens(*, refresh_token: str) -> KeycloakTokenBundle:
        assert refresh_token == "refresh-token"
        return KeycloakTokenBundle(
            access_token="access-token",
            refresh_token="refresh-token-next",
            expires_in=300,
            refresh_expires_in=3600,
        )

    async def _fake_build_keycloak_auth_response(*, access_token: str, uow):
        _ = (access_token, uow)
        data = _build_login_payload(access_token="access-token")
        data["delegation_roles"] = ["delegation.request-reader"]
        return LoginResponse(data=data)

    monkeypatch.setattr(auth_api, "refresh_tokens", _fake_refresh_tokens)
    monkeypatch.setattr(auth_api, "_build_keycloak_auth_response", _fake_build_keycloak_auth_response)

    response = _post_with_cookie(
        test_client,
        "/api/v1/auth/refresh",
        cookie_name=settings.keycloak_refresh_cookie_name,
        cookie_value="refresh-token",
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["permissions"] == [PermissionCodes.USERS_READ]
    assert payload["app_roles"] == ["app.contractor"]
    assert payload["delegation_roles"] == ["delegation.request-reader"]
    assert payload["status"] == "active"
    assert payload["role_id"] == settings.contractor_role_id
    assert payload["business_access"] is True
    assert payload["onboarding_state"] is None


def test_refresh_session_permissions_do_not_depend_on_role_id(test_client, monkeypatch, set_uow):
    set_uow(_FakeUow())
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    async def _fake_refresh_tokens(*, refresh_token: str) -> KeycloakTokenBundle:
        _ = refresh_token
        return KeycloakTokenBundle(
            access_token="access-token",
            refresh_token="refresh-token-next",
            expires_in=300,
            refresh_expires_in=3600,
        )

    async def _fake_build_keycloak_auth_response(*, access_token: str, uow):
        _ = (access_token, uow)
        return LoginResponse(data=_build_login_payload(access_token=access_token))

    monkeypatch.setattr(auth_api, "refresh_tokens", _fake_refresh_tokens)
    monkeypatch.setattr(auth_api, "_build_keycloak_auth_response", _fake_build_keycloak_auth_response)

    response = _post_with_cookie(
        test_client,
        "/api/v1/auth/refresh",
        cookie_name=settings.keycloak_refresh_cookie_name,
        cookie_value="refresh-token",
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    # Contractor role does not imply users.read by local role map.
    assert payload["role_id"] == settings.contractor_role_id
    assert PermissionCodes.USERS_READ in payload["permissions"]


def test_refresh_rotation_updates_refresh_cookie_and_repeated_refresh_is_consistent(test_client, monkeypatch, set_uow):
    set_uow(_FakeUow())
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    observed_tokens: list[str] = []
    rotation_map = {
        "refresh-token": KeycloakTokenBundle(
            access_token="access-1",
            refresh_token="refresh-token-2",
            expires_in=300,
            refresh_expires_in=1800,
        ),
        "refresh-token-2": KeycloakTokenBundle(
            access_token="access-2",
            refresh_token="refresh-token-3",
            expires_in=300,
            refresh_expires_in=2400,
        ),
    }

    async def _fake_refresh_tokens(*, refresh_token: str) -> KeycloakTokenBundle:
        observed_tokens.append(refresh_token)
        try:
            return rotation_map[refresh_token]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise Unauthorized("Invalid refresh") from exc

    async def _fake_build_keycloak_auth_response(*, access_token: str, uow):
        _ = uow
        return _build_login_response(access_token=access_token)

    monkeypatch.setattr(auth_api, "refresh_tokens", _fake_refresh_tokens)
    monkeypatch.setattr(auth_api, "_build_keycloak_auth_response", _fake_build_keycloak_auth_response)

    first = _post_with_cookie(
        test_client,
        "/api/v1/auth/refresh",
        cookie_name=settings.keycloak_refresh_cookie_name,
        cookie_value="refresh-token",
    )
    assert first.status_code == 200
    assert first.json()["data"]["access_token"] == "access-1"
    first_set_cookie_headers = _collect_set_cookie_headers(first)
    assert any(settings.keycloak_refresh_cookie_name in header and "refresh-token-2" in header and "Max-Age=1800" in header for header in first_set_cookie_headers)
    rotated_token = first.cookies.get(settings.keycloak_refresh_cookie_name)
    assert rotated_token == "refresh-token-2"

    second = _post_with_cookie(
        test_client,
        "/api/v1/auth/refresh",
        cookie_name=settings.keycloak_refresh_cookie_name,
        cookie_value=rotated_token,
    )
    assert second.status_code == 200
    assert second.json()["data"]["access_token"] == "access-2"
    second_set_cookie_headers = _collect_set_cookie_headers(second)
    assert any(settings.keycloak_refresh_cookie_name in header and "refresh-token-3" in header and "Max-Age=2400" in header for header in second_set_cookie_headers)

    assert observed_tokens == ["refresh-token", "refresh-token-2"]


def test_refresh_with_stale_cookie_returns_401_and_clears_cookie(test_client, monkeypatch, set_uow):
    set_uow(_FakeUow())
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    async def _fake_refresh_tokens(*, refresh_token: str) -> KeycloakTokenBundle:
        _ = refresh_token
        raise Unauthorized("Stale refresh token")

    monkeypatch.setattr(auth_api, "refresh_tokens", _fake_refresh_tokens)

    response = _post_with_cookie(
        test_client,
        "/api/v1/auth/refresh",
        cookie_name=settings.keycloak_refresh_cookie_name,
        cookie_value="stale-refresh-token",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing credentials"
    set_cookie_headers = _collect_set_cookie_headers(response)
    assert any(settings.keycloak_refresh_cookie_name in header and "Max-Age=0" in header for header in set_cookie_headers)

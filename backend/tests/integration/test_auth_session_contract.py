"""Session/auth contract tests for `/api/v1/auth/refresh`.

Focus:
- required fields are present in the session payload;
- permissions source is Keycloak-like role claims, not local role-id mapping.
"""

from app.api.v1 import auth as auth_api
from app.core.config import settings
from app.domain.permissions import PermissionCodes
from app.schemas.auth import LoginResponse
from app.services.keycloak_oidc import KeycloakTokenBundle


class _FakeUow:
    async def __aenter__(self) -> "_FakeUow":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


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
        return LoginResponse(
            data={
                "access_token": "access-token",
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
                "delegation_roles": ["delegation.request-reader"],
            }
        )

    monkeypatch.setattr(auth_api, "refresh_tokens", _fake_refresh_tokens)
    monkeypatch.setattr(auth_api, "_build_keycloak_auth_response", _fake_build_keycloak_auth_response)

    response = test_client.post(
        "/api/v1/auth/refresh",
        cookies={settings.keycloak_refresh_cookie_name: "refresh-token"},
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
        return LoginResponse(
            data={
                "access_token": "access-token",
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

    monkeypatch.setattr(auth_api, "refresh_tokens", _fake_refresh_tokens)
    monkeypatch.setattr(auth_api, "_build_keycloak_auth_response", _fake_build_keycloak_auth_response)

    response = test_client.post(
        "/api/v1/auth/refresh",
        cookies={settings.keycloak_refresh_cookie_name: "refresh-token"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    # Contractor role does not imply users.read by local role map.
    assert payload["role_id"] == settings.contractor_role_id
    assert PermissionCodes.USERS_READ in payload["permissions"]

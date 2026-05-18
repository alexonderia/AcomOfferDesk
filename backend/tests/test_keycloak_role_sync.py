import asyncio
import base64
import json

from app.core.config import settings
from app.scripts.sync_keycloak_user_app_roles import role_mapping_by_local_role_id
from app.services.keycloak_admin import KeycloakAdminService


def _run(coroutine):
    return asyncio.run(coroutine)


def _jwt_with_claims(payload: dict) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{encoded}.signature"


def test_role_mapping_by_local_role_id_matches_expected_app_roles():
    mapping = role_mapping_by_local_role_id()

    assert mapping[settings.superadmin_role_id] == "app.superadmin"
    assert mapping[settings.admin_role_id] == "app.admin"
    assert mapping[settings.project_manager_role_id] == "app.project_manager"
    assert mapping[settings.lead_economist_role_id] == "app.lead_economist"
    assert mapping[settings.economist_role_id] == "app.economist"
    assert mapping[settings.operator_role_id] == "app.operator"
    assert mapping[settings.contractor_role_id] == "app.contractor"


def test_replace_user_app_role_removes_only_conflicting_app_roles(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    service = KeycloakAdminService()

    removed_payload: dict[str, list[dict]] = {}
    added_payload: dict[str, list[dict]] = {}

    async def fake_get_user_client_role_mappings(*, keycloak_user_id, client_uuid, admin_token=None):
        return [
            {"id": "1", "name": "app.admin"},
            {"id": "2", "name": "delegation.user-manager"},
            {"id": "3", "name": "users.read"},
        ]

    async def fake_remove_user_client_roles(*, keycloak_user_id, client_uuid, roles, admin_token=None):
        removed_payload["roles"] = roles

    async def fake_get_client_role_by_name(*, client_uuid, role_name, admin_token=None):
        return {"id": "4", "name": role_name}

    async def fake_add_user_client_roles(*, keycloak_user_id, client_uuid, roles, admin_token=None):
        added_payload["roles"] = roles

    monkeypatch.setattr(service, "get_user_client_role_mappings", fake_get_user_client_role_mappings)
    monkeypatch.setattr(service, "remove_user_client_roles", fake_remove_user_client_roles)
    monkeypatch.setattr(service, "get_client_role_by_name", fake_get_client_role_by_name)
    monkeypatch.setattr(service, "add_user_client_roles", fake_add_user_client_roles)

    synced, removed_count = _run(
        service.replace_user_app_role(
            keycloak_user_id="kc-user",
            api_client_uuid="client-uuid",
            target_app_role="app.economist",
            admin_token="token",
        )
    )

    assert synced is True
    assert removed_count == 1
    assert [role["name"] for role in removed_payload["roles"]] == ["app.admin"]
    assert [role["name"] for role in added_payload["roles"]] == ["app.economist"]


def test_replace_user_app_role_is_idempotent_when_target_already_set(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    service = KeycloakAdminService()

    remove_called = {"value": False}
    add_called = {"value": False}

    async def fake_get_user_client_role_mappings(*, keycloak_user_id, client_uuid, admin_token=None):
        return [
            {"id": "1", "name": "app.economist"},
            {"id": "2", "name": "delegation.user-manager"},
            {"id": "3", "name": "users.read"},
        ]

    async def fake_remove_user_client_roles(*, keycloak_user_id, client_uuid, roles, admin_token=None):
        remove_called["value"] = True

    async def fake_add_user_client_roles(*, keycloak_user_id, client_uuid, roles, admin_token=None):
        add_called["value"] = True

    monkeypatch.setattr(service, "get_user_client_role_mappings", fake_get_user_client_role_mappings)
    monkeypatch.setattr(service, "remove_user_client_roles", fake_remove_user_client_roles)
    monkeypatch.setattr(service, "add_user_client_roles", fake_add_user_client_roles)

    synced, removed_count = _run(
        service.replace_user_app_role(
            keycloak_user_id="kc-user",
            api_client_uuid="client-uuid",
            target_app_role="app.economist",
            admin_token="token",
        )
    )

    assert synced is True
    assert removed_count == 0
    assert remove_called["value"] is False
    assert add_called["value"] is False


def test_sync_user_app_role_for_local_role_resolves_target_app_role(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    service = KeycloakAdminService()

    observed: dict[str, str] = {}

    async def fake_replace_user_app_role(*, keycloak_user_id, api_client_uuid, target_app_role, admin_token=None):
        observed["target_app_role"] = target_app_role
        return True, 0

    monkeypatch.setattr(service, "replace_user_app_role", fake_replace_user_app_role)

    synced, removed_count = _run(
        service.sync_user_app_role_for_local_role(
            keycloak_user_id="kc-user",
            api_client_uuid="client-uuid",
            local_role_id=123,
            role_mapping={123: "app.operator"},
            admin_token="token",
        )
    )

    assert synced is True
    assert removed_count == 0
    assert observed == {"target_app_role": "app.operator"}


def test_token_has_admin_claims_rejects_empty_service_account_token():
    token = _jwt_with_claims(
        {
            "azp": "acom-admin-service",
            "preferred_username": "service-account-acom-admin-service",
            "realm_access": None,
            "resource_access": None,
        }
    )

    assert KeycloakAdminService._token_has_admin_claims(token) is False


def test_get_admin_token_falls_back_to_password_grant_when_service_token_has_no_roles(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    service = KeycloakAdminService()
    service._realm = "acom-offerdesk"
    service._admin_realm = "master"

    service_token = _jwt_with_claims(
        {
            "azp": "acom-admin-service",
            "preferred_username": "service-account-acom-admin-service",
            "realm_access": None,
            "resource_access": None,
        }
    )

    observed_calls: list[dict[str, str]] = []

    async def fake_request_token(*, base_url: str, realm: str, form_data: dict[str, str]):
        observed_calls.append({"base_url": base_url, "realm": realm, "grant_type": form_data["grant_type"]})
        if form_data["grant_type"] == "client_credentials":
            return service_token
        return "password-grant-token"

    monkeypatch.setattr(service, "_candidate_base_urls", lambda: ("http://keycloak:8080/iam",))
    monkeypatch.setattr(service, "_candidate_password_grant_realms", lambda: ("acom-offerdesk", "master"))
    monkeypatch.setattr(service, "_request_token", fake_request_token)

    token = _run(service.get_admin_token())

    assert token == "password-grant-token"
    assert [call["grant_type"] for call in observed_calls] == [
        "client_credentials",
        "client_credentials",
        "password",
    ]
    assert [call["realm"] for call in observed_calls] == [
        "acom-offerdesk",
        "master",
        "acom-offerdesk",
    ]

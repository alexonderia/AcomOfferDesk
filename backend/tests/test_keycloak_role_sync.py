import asyncio

from app.core.config import settings
from app.scripts.sync_keycloak_user_app_roles import role_mapping_by_local_role_id
from app.services.keycloak_admin import KeycloakAdminService


def _run(coroutine):
    return asyncio.run(coroutine)


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

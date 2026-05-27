import asyncio

import pytest

from app.core.config import settings
from app.domain.exceptions import Conflict
from app.services.keycloak_admin import KeycloakAdminService
from app.services.keycloak_delegations import KeycloakDepartmentDelegationsService


def _run(coroutine):
    return asyncio.run(coroutine)


def test_sync_department_roles_adds_and_removes_only_department_roles(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    service = KeycloakDepartmentDelegationsService(keycloak_admin=KeycloakAdminService())

    removed_calls: list[list[dict]] = []
    added_calls: list[list[dict]] = []

    async def fake_get_admin_token():
        return "token"

    async def fake_get_client_uuid_by_client_id(*, client_id: str, admin_token: str):
        _ = (client_id, admin_token)
        return "client-uuid"

    async def fake_get_client_role_by_name(*, client_uuid: str, role_name: str, admin_token: str):
        _ = (client_uuid, admin_token)
        return {"id": f"id-{role_name}", "name": role_name}

    async def fake_get_user_client_role_mappings(*, keycloak_user_id: str, client_uuid: str, admin_token: str):
        _ = (keycloak_user_id, client_uuid, admin_token)
        return [
            {"id": "r1", "name": "delegation.department.requests.read"},
            {"id": "r2", "name": "delegation.custom.keep"},
            {"id": "r3", "name": "app.economist"},
            {"id": "r4", "name": "requests.read"},
        ]

    async def fake_remove_user_client_roles(*, keycloak_user_id: str, client_uuid: str, roles: list[dict], admin_token: str):
        _ = (keycloak_user_id, client_uuid, admin_token)
        removed_calls.append(roles)

    async def fake_add_user_client_roles(*, keycloak_user_id: str, client_uuid: str, roles: list[dict], admin_token: str):
        _ = (keycloak_user_id, client_uuid, admin_token)
        added_calls.append(roles)

    monkeypatch.setattr(service._keycloak_admin, "get_admin_token", fake_get_admin_token)
    monkeypatch.setattr(service._keycloak_admin, "get_client_uuid_by_client_id", fake_get_client_uuid_by_client_id)
    monkeypatch.setattr(service._keycloak_admin, "get_client_role_by_name", fake_get_client_role_by_name)
    monkeypatch.setattr(service._keycloak_admin, "get_user_client_role_mappings", fake_get_user_client_role_mappings)
    monkeypatch.setattr(service._keycloak_admin, "remove_user_client_roles", fake_remove_user_client_roles)
    monkeypatch.setattr(service._keycloak_admin, "add_user_client_roles", fake_add_user_client_roles)

    result = _run(
        service.sync_user_department_role_codes(
            keycloak_user_id="kc-user",
            requested_role_codes={"delegation.department.offers.accept"},
        )
    )

    assert result.added_role_codes == frozenset({"delegation.department.offers.accept"})
    assert result.removed_role_codes == frozenset({"delegation.department.requests.read"})
    flattened_removed = [item["name"] for batch in removed_calls for item in batch]
    flattened_added = [item["name"] for batch in added_calls for item in batch]
    assert "delegation.department.requests.read" in flattened_removed
    assert "delegation.department.offers.accept" in flattened_added
    assert "department.offers.accept" in flattened_added


def test_sync_department_roles_rejects_unknown_codes(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)
    service = KeycloakDepartmentDelegationsService(keycloak_admin=KeycloakAdminService())

    with pytest.raises(Conflict):
        _run(
            service.sync_user_department_role_codes(
                keycloak_user_id="kc-user",
                requested_role_codes={"delegation.department.unknown"},
            )
        )

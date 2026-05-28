from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.services.user_department_delegations import UserDepartmentDelegationsService


class _UsersRepo:
    def __init__(self) -> None:
        self._users = {
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active"),
            "eco-1": SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
            "pm-2": SimpleNamespace(id="pm-2", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-2": SimpleNamespace(id="lead-2", id_role=settings.lead_economist_role_id, id_parent="pm-2", status="active"),
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [(item.id, item.id_parent) for item in self._users.values() if item.status == "active"]


class _ProfilesRepo:
    async def get_by_id(self, user_id: str):
        return SimpleNamespace(id=user_id, full_name=f"Name {user_id}")


class _UserAuthAccountsRepo:
    async def get_by_user_provider(self, *, user_id: str, provider: str, include_inactive: bool = False):
        _ = include_inactive
        if provider != "keycloak":
            return None
        return SimpleNamespace(external_subject_id=f"kc-{user_id}")


class _KeycloakDelegations:
    async def list_user_enabled_department_role_codes(self, *, keycloak_user_id: str):
        _ = keycloak_user_id
        return frozenset({"delegation.department.requests.read"})

    async def sync_user_department_role_codes(self, *, keycloak_user_id: str, requested_role_codes: set[str]):
        _ = keycloak_user_id
        return SimpleNamespace(
            enabled_role_codes=frozenset(requested_role_codes),
            added_role_codes=frozenset(requested_role_codes),
            removed_role_codes=frozenset(),
        )


class _KeycloakAdmin:
    async def logout_user_sessions(self, *, user_id: str):
        _ = user_id
        return None


def _user(*, user_id: str, role_id: int) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status="active",
        permissions=frozenset(),
    )


@pytest.mark.asyncio
async def test_project_manager_can_manage_user_inside_own_department():
    service = UserDepartmentDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        keycloak_delegations=_KeycloakDelegations(),
        keycloak_admin=_KeycloakAdmin(),
    )

    result = await service.get_state(
        current_user=_user(user_id="pm-1", role_id=settings.project_manager_role_id),
        target_user_id="eco-1",
    )

    assert result.can_manage is True
    assert any(item.enabled for item in result.accesses)


@pytest.mark.asyncio
async def test_project_manager_cannot_manage_user_from_other_department():
    service = UserDepartmentDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        keycloak_delegations=_KeycloakDelegations(),
        keycloak_admin=_KeycloakAdmin(),
    )

    result = await service.get_state(
        current_user=_user(user_id="pm-1", role_id=settings.project_manager_role_id),
        target_user_id="lead-2",
    )

    assert result.can_manage is False
    with pytest.raises(Forbidden):
        await service.update_state(
            current_user=_user(user_id="pm-1", role_id=settings.project_manager_role_id),
            target_user_id="lead-2",
            requested_access_codes=["delegation.department.requests.read"],
        )


@pytest.mark.asyncio
async def test_lead_economist_cannot_manage_department_delegations():
    service = UserDepartmentDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        keycloak_delegations=_KeycloakDelegations(),
        keycloak_admin=_KeycloakAdmin(),
    )

    result = await service.get_state(
        current_user=_user(user_id="lead-1", role_id=settings.lead_economist_role_id),
        target_user_id="eco-1",
    )

    assert result.can_manage is False


@pytest.mark.asyncio
async def test_admin_cannot_manage_delegations_for_self():
    service = UserDepartmentDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        keycloak_delegations=_KeycloakDelegations(),
        keycloak_admin=_KeycloakAdmin(),
    )

    result = await service.get_state(
        current_user=_user(user_id="pm-1", role_id=settings.admin_role_id),
        target_user_id="pm-1",
    )

    assert result.can_manage is False

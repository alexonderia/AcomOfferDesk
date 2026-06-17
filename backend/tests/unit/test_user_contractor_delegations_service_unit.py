from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.services.user_contractor_delegations import UserContractorDelegationsService


class _UsersRepo:
    def __init__(self) -> None:
        self._users = {
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent=None, status="active"),
            "eco-1": SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)


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
    async def list_user_enabled_contractor_role_codes(self, *, keycloak_user_id: str):
        _ = keycloak_user_id
        return frozenset()

    async def sync_user_contractor_role_codes(self, *, keycloak_user_id: str, requested_role_codes: set[str]):
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


def _service() -> UserContractorDelegationsService:
    return UserContractorDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        keycloak_delegations=_KeycloakDelegations(),
        keycloak_admin=_KeycloakAdmin(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("manager_role_id", [settings.superadmin_role_id, settings.admin_role_id])
async def test_admin_roles_can_manage_contractor_delegations_for_lead_economist(manager_role_id: int):
    service = _service()

    result = await service.get_state(
        current_user=_user(user_id="manager-1", role_id=manager_role_id),
        target_user_id="lead-1",
    )

    assert result.can_manage is True
    assert len(result.accesses) == 1


@pytest.mark.asyncio
async def test_admin_cannot_manage_contractor_delegations_for_non_lead_economist():
    service = _service()

    result = await service.get_state(
        current_user=_user(user_id="admin-1", role_id=settings.admin_role_id),
        target_user_id="eco-1",
    )

    assert result.can_manage is False


@pytest.mark.asyncio
async def test_lead_economist_cannot_manage_contractor_delegations():
    service = _service()

    result = await service.get_state(
        current_user=_user(user_id="lead-1", role_id=settings.lead_economist_role_id),
        target_user_id="lead-1",
    )

    assert result.can_manage is False
    with pytest.raises(Forbidden):
        await service.update_state(
            current_user=_user(user_id="lead-1", role_id=settings.lead_economist_role_id),
            target_user_id="lead-1",
            requested_access_codes=["delegation.contractors.profile.status.update"],
        )

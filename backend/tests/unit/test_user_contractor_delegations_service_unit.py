from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.infrastructure.iam_client import IamAccountPermissions
from app.services.iam_permission_grants import ManagedPermissionGrantsResult
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
        if provider != "iam":
            return None
        return SimpleNamespace(external_subject_id=f"iam-{user_id}")


class _IamPermissionGrants:
    def __init__(self) -> None:
        self.permissions = IamAccountPermissions(
            permissions_from_role=frozenset({"contractors.read"}),
            individually_granted_permissions=frozenset(),
            effective_permissions=frozenset({"contractors.read"}),
        )
        self.requested_permissions: frozenset[str] | None = None

    async def get(self, *, account_id: str):
        assert account_id.startswith("iam-")
        return self.permissions

    async def replace_managed_grants(
        self,
        *,
        account_id: str,
        managed_permissions: frozenset[str],
        requested_permissions: frozenset[str],
    ):
        assert account_id.startswith("iam-")
        assert requested_permissions.issubset(managed_permissions)
        self.requested_permissions = requested_permissions
        self.permissions = IamAccountPermissions(
            permissions_from_role=self.permissions.permissions_from_role,
            individually_granted_permissions=requested_permissions,
            effective_permissions=(
                self.permissions.permissions_from_role | requested_permissions
            ),
        )
        return ManagedPermissionGrantsResult(self.permissions, changed=True)


def _user(*, user_id: str, role_id: int) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="test-role",
        role_id=role_id,
        status="active",
        permissions=frozenset(),
    )


def _service() -> UserContractorDelegationsService:
    return UserContractorDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        iam_permission_grants=_IamPermissionGrants(),
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

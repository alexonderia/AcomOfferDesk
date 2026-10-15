from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.infrastructure.iam_client import IamAccountPermissions
from app.services.iam_permission_grants import ManagedPermissionGrantsResult
from app.services.user_department_delegations import UserDepartmentDelegationsService


class _UsersRepo:
    def __init__(self) -> None:
        self._units = [(1, None), (2, 1), (10, None), (11, 10)]
        self._memberships = [
            ("pm-1", 1),
            ("lead-1", 2),
            ("eco-1", 2),
            ("pm-2", 10),
            ("lead-2", 11),
        ]
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

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_memberships(self):
        return list(self._memberships)


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
            permissions_from_role=frozenset({"department.requests.read"}),
            individually_granted_permissions=frozenset({"department.offers.accept"}),
            effective_permissions=frozenset(
                {"department.requests.read", "department.offers.accept"}
            ),
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


@pytest.mark.asyncio
async def test_project_manager_can_manage_user_inside_own_department():
    iam_grants = _IamPermissionGrants()
    service = UserDepartmentDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        iam_permission_grants=iam_grants,
    )

    result = await service.get_state(
        current_user=_user(user_id="pm-1", role_id=settings.project_manager_role_id),
        target_user_id="eco-1",
    )

    assert result.can_manage is True
    assert any(item.enabled for item in result.accesses)
    role_access = next(
        item for item in result.accesses if item.permission_code == "department.requests.read"
    )
    individual_access = next(
        item for item in result.accesses if item.permission_code == "department.offers.accept"
    )
    assert role_access.granted_via_role is True
    assert role_access.granted_individually is False
    assert individual_access.granted_individually is True

    updated = await service.update_state(
        current_user=_user(user_id="pm-1", role_id=settings.project_manager_role_id),
        target_user_id="eco-1",
        requested_access_codes=["delegation.department.requests.update"],
    )
    assert iam_grants.requested_permissions == frozenset({"department.requests.update"})
    assert next(
        item for item in updated.accesses if item.permission_code == "department.requests.read"
    ).enabled is True


@pytest.mark.asyncio
async def test_project_manager_cannot_manage_user_from_other_department():
    service = UserDepartmentDelegationsService(
        users=_UsersRepo(),
        profiles=_ProfilesRepo(),
        user_auth_accounts=_UserAuthAccountsRepo(),
        iam_permission_grants=_IamPermissionGrants(),
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
        iam_permission_grants=_IamPermissionGrants(),
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
        iam_permission_grants=_IamPermissionGrants(),
    )

    result = await service.get_state(
        current_user=_user(user_id="pm-1", role_id=settings.admin_role_id),
        target_user_id="pm-1",
    )

    assert result.can_manage is False

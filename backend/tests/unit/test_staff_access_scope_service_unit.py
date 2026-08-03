from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.permissions import PermissionCodes
from app.services.staff_access_scope import StaffAccessScopeService


class _UsersRepo:
    def __init__(self) -> None:
        self._users = {
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1"),
            "lead-2": SimpleNamespace(id="lead-2", id_role=settings.lead_economist_role_id, id_parent="lead-1"),
            "eco-1": SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1"),
            "eco-2": SimpleNamespace(id="eco-2", id_role=settings.economist_role_id, id_parent="lead-2"),
        }
        self._units = [
            (1, None),
            (2, 1),
            (3, 2),
        ]
        self._memberships = [
            ("pm-1", 1),
            ("lead-1", 2),
            ("lead-2", 3),
            ("eco-1", 2),
            ("eco-2", 3),
        ]

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [
            ("lead-1", "pm-1"),
            ("lead-2", "lead-1"),
            ("eco-1", "lead-1"),
            ("eco-2", "lead-2"),
        ]

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_memberships(self):
        return list(self._memberships)


class _UnitAwareUsersRepo(_UsersRepo):
    def __init__(self) -> None:
        super().__init__()
        self._users["cross-eco"] = SimpleNamespace(
            id="cross-eco",
            id_role=settings.economist_role_id,
            id_parent=None,
        )
        self._memberships = [
            ("pm-1", 1),
            ("lead-1", 2),
            ("cross-eco", 3),
        ]


def _current_user(*, user_id: str, role_id: int, permissions: frozenset[str] | None = None) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status="active",
        permissions=permissions or frozenset(),
    )


class _PeerModuleUsersRepo(_UsersRepo):
    def __init__(self) -> None:
        super().__init__()
        self._memberships = [
            ("pm-1", 1),
            ("lead-1", 2),
            ("lead-2", 3),
            ("eco-1", 2),
            ("eco-2", 2),
        ]


@pytest.mark.asyncio
async def test_peer_economist_can_view_but_cannot_manage_adjacent_module_request():
    service = StaffAccessScopeService(_PeerModuleUsersRepo())
    current_user = _current_user(user_id="eco-1", role_id=settings.economist_role_id)

    assert await service.can_view_request_owner(
        current_user=current_user,
        request_owner_user_id="eco-2",
    )
    assert await service.can_view_chat_for_request(
        current_user=current_user,
        request_owner_user_id="eco-2",
    )
    assert not await service.is_hierarchy_manager_of(
        current_user=current_user,
        request_owner_user_id="eco-2",
    )
    assert not await service.can_send_chat_for_request(
        current_user=current_user,
        request_owner_user_id="eco-2",
    )


@pytest.mark.asyncio
async def test_lead_economist_manages_own_module_request_owner():
    service = StaffAccessScopeService(_UsersRepo())
    current_user = _current_user(user_id="lead-1", role_id=settings.lead_economist_role_id)

    assert await service.is_hierarchy_manager_of(
        current_user=current_user,
        request_owner_user_id="eco-1",
    )
    assert await service.can_send_chat_for_request(
        current_user=current_user,
        request_owner_user_id="eco-1",
    )


@pytest.mark.asyncio
async def test_project_manager_manages_request_in_department():
    service = StaffAccessScopeService(_UsersRepo())
    current_user = _current_user(user_id="pm-1", role_id=settings.project_manager_role_id)

    assert await service.is_hierarchy_manager_of(
        current_user=current_user,
        request_owner_user_id="eco-2",
    )


@pytest.mark.asyncio
async def test_department_delegation_update_allows_manage_outside_hierarchy():
    service = StaffAccessScopeService(_UsersRepo())
    current_user = _current_user(
        user_id="eco-1",
        role_id=settings.economist_role_id,
        permissions=frozenset({PermissionCodes.DEPARTMENT_REQUESTS_UPDATE}),
    )

    assert await service.can_manage_request_owner(
        current_user=current_user,
        request_owner_user_id="eco-2",
    )


@pytest.mark.asyncio
async def test_resolve_manageable_owner_ids_returns_bulk_scope_for_single_pass_checks():
    service = StaffAccessScopeService(_UsersRepo())
    current_user = _current_user(
        user_id="lead-1",
        role_id=settings.lead_economist_role_id,
    )

    manageable = await service.resolve_manageable_owner_ids(
        current_user=current_user,
        candidate_owner_ids={"lead-1", "eco-1", "eco-2"},
    )

    assert manageable == {"lead-1", "eco-1", "eco-2"}


@pytest.mark.asyncio
async def test_module_root_for_nested_lead_and_economist_uses_nested_lead_and_supervising_lead():
    service = StaffAccessScopeService(_UsersRepo())

    lead_module_root = await service.resolve_module_root_user_id(
        user_id="lead-2",
        role_id=settings.lead_economist_role_id,
    )
    economist_module_root = await service.resolve_module_root_user_id(
        user_id="eco-2",
        role_id=settings.economist_role_id,
    )

    assert lead_module_root == "lead-2"
    assert economist_module_root == "lead-1"


@pytest.mark.asyncio
async def test_unit_descendant_scope_grants_management_even_without_user_parent_chain():
    service = StaffAccessScopeService(_UnitAwareUsersRepo())
    current_user = _current_user(user_id="lead-1", role_id=settings.lead_economist_role_id)

    assert await service.can_view_request_owner(
        current_user=current_user,
        request_owner_user_id="cross-eco",
    )
    assert await service.is_hierarchy_manager_of(
        current_user=current_user,
        request_owner_user_id="cross-eco",
    )

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services.department_scope import DepartmentScopeService


class _UsersRepo:
    def __init__(self) -> None:
        self._users = {
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active"),
            "eco-1": SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
            "eco-2": SimpleNamespace(id="eco-2", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
            "pm-2": SimpleNamespace(id="pm-2", id_role=settings.project_manager_role_id, id_parent="pm-1", status="active"),
            "lead-2": SimpleNamespace(id="lead-2", id_role=settings.lead_economist_role_id, id_parent="pm-2", status="active"),
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [(item.id, item.id_parent) for item in self._users.values() if item.status == "active"]


def _current_user(*, user_id: str, role_id: int) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status="active",
        permissions=frozenset(),
    )


@pytest.mark.asyncio
async def test_department_scope_for_economist_resolves_project_manager_subtree():
    service = DepartmentScopeService(_UsersRepo())

    owner_ids = await service.resolve_department_owner_ids_for_current_user(
        current_user=_current_user(user_id="eco-1", role_id=settings.economist_role_id),
    )

    assert set(owner_ids) == {"pm-1", "lead-1", "eco-1", "eco-2"}


@pytest.mark.asyncio
async def test_department_scope_for_project_manager_does_not_mix_nested_project_manager_department():
    service = DepartmentScopeService(_UsersRepo())

    owner_ids = await service.resolve_department_owner_ids_for_current_user(
        current_user=_current_user(user_id="pm-1", role_id=settings.project_manager_role_id),
    )

    assert set(owner_ids) == {"pm-1", "lead-1", "eco-1", "eco-2"}


@pytest.mark.asyncio
async def test_department_scope_membership_check_is_strict_to_current_department():
    service = DepartmentScopeService(_UsersRepo())

    current_user = _current_user(user_id="lead-1", role_id=settings.lead_economist_role_id)
    assert await service.is_user_in_current_user_department(
        current_user=current_user,
        target_user_id="eco-2",
    )
    assert not await service.is_user_in_current_user_department(
        current_user=current_user,
        target_user_id="lead-2",
    )


class _UnitAwareUsersRepo(_UsersRepo):
    """Users repo that also exposes active unit graph data.

    Units:
      1 "Департамент A" (root)
        2 "Отдел X"  -> 4 "Группа X1"
        3 "Отдел Y"
      10 "Департамент B" (separate root)
    """

    def __init__(self) -> None:
        super().__init__()
        self._units = [
            (1, None),
            (2, 1),
            (3, 1),
            (4, 2),
            (10, None),
        ]
        self._memberships = [
            ("pm-1", 1),
            ("lead-1", 2),
            ("eco-1", 4),
            ("lead-2", 3),
            ("pm-2", 10),
        ]

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_memberships(self):
        return list(self._memberships)


@pytest.mark.asyncio
async def test_department_scope_is_root_unit_subtree_when_user_has_units():
    service = DepartmentScopeService(_UnitAwareUsersRepo())

    pm_department = await service.resolve_department_owner_ids_for_current_user(
        current_user=_current_user(user_id="pm-1", role_id=settings.project_manager_role_id),
    )
    lead_department = await service.resolve_department_owner_ids_for_current_user(
        current_user=_current_user(user_id="lead-1", role_id=settings.lead_economist_role_id),
    )

    # Whole root unit (1) subtree: units {1,2,3,4}; unit 10 is a separate root.
    assert set(pm_department) == {"pm-1", "lead-1", "eco-1", "lead-2"}
    assert set(lead_department) == {"pm-1", "lead-1", "eco-1", "lead-2"}


@pytest.mark.asyncio
async def test_unit_scope_for_lead_is_only_their_own_unit_subtree():
    service = DepartmentScopeService(_UnitAwareUsersRepo())

    lead_unit_scope = await service.resolve_unit_scope_owner_ids_for_user(user_id="lead-1")

    # Subtree of lead's own unit (2): units {2,4}; excludes sibling unit 3 (lead-2).
    assert set(lead_unit_scope) == {"lead-1", "eco-1"}


@pytest.mark.asyncio
async def test_descendant_unit_scope_excludes_current_unit_members():
    service = DepartmentScopeService(_UnitAwareUsersRepo())

    descendant_scope = await service.resolve_descendant_unit_scope_owner_ids_for_user(user_id="lead-1")

    assert set(descendant_scope) == {"eco-1"}


@pytest.mark.asyncio
async def test_department_membership_spans_root_unit_but_not_other_root():
    service = DepartmentScopeService(_UnitAwareUsersRepo())

    current_user = _current_user(user_id="lead-1", role_id=settings.lead_economist_role_id)
    assert await service.is_user_in_current_user_department(
        current_user=current_user,
        target_user_id="lead-2",
    )
    assert not await service.is_user_in_current_user_department(
        current_user=current_user,
        target_user_id="pm-2",
    )


@pytest.mark.asyncio
async def test_user_has_active_unit_membership_reflects_graph():
    service = DepartmentScopeService(_UnitAwareUsersRepo())

    assert await service.user_has_active_unit_membership(user_id="lead-1")
    assert not await service.user_has_active_unit_membership(user_id="ghost")


@pytest.mark.asyncio
async def test_department_scope_falls_back_to_hierarchy_without_unit_membership():
    repo = _UnitAwareUsersRepo()
    # Drop all memberships -> no unit data -> hierarchy fallback.
    repo._memberships = []
    service = DepartmentScopeService(repo)

    department = await service.resolve_department_owner_ids_for_current_user(
        current_user=_current_user(user_id="eco-1", role_id=settings.economist_role_id),
    )

    assert set(department) == {"pm-1", "lead-1", "eco-1", "eco-2"}

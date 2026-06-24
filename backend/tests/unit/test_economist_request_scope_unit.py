"""Unit tests for unit-based request visibility of economist roles (РП, ВЭ, Э)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.permissions import PermissionCodes
from app.services.requests import RequestService


class _UsersRepo:
    """Hierarchy + unit graph fixture.

    Hierarchy (id_parent): pm-1 <- lead-1 <- eco-1 ; pm-1 <- lead-2 <- eco-2
    Units:
      1 root (Департамент A): pm-1
        2 "Отдел X": lead-1
          4 "Группа X1": eco-1
        3 "Отдел Y": lead-2, eco-2
    """

    def __init__(self) -> None:
        self._users = {
            "pm-1": SimpleNamespace(id="pm-1", id_role=settings.project_manager_role_id, id_parent=None, status="active"),
            "lead-1": SimpleNamespace(id="lead-1", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active"),
            "eco-1": SimpleNamespace(id="eco-1", id_role=settings.economist_role_id, id_parent="lead-1", status="active"),
            "lead-2": SimpleNamespace(id="lead-2", id_role=settings.lead_economist_role_id, id_parent="pm-1", status="active"),
            "eco-2": SimpleNamespace(id="eco-2", id_role=settings.economist_role_id, id_parent="lead-2", status="active"),
        }
        self._units = [(1, None), (2, 1), (3, 1), (4, 2)]
        self._memberships = [
            ("pm-1", 1),
            ("lead-1", 2),
            ("eco-1", 4),
            ("lead-2", 3),
            ("eco-2", 3),
        ]

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [(item.id, item.id_parent) for item in self._users.values() if item.status == "active"]

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_memberships(self):
        return list(self._memberships)


def _user(*, user_id: str, role_id: int, permissions: frozenset[str] | None = None) -> CurrentUser:
    return CurrentUser(
        user_id=user_id,
        role_id=role_id,
        status="active",
        permissions=permissions or frozenset(),
    )


def _build_service(users: _UsersRepo) -> RequestService:
    return RequestService(
        requests=AsyncMock(),
        files=AsyncMock(),
        users=users,
        offers=AsyncMock(),
        user_status_periods=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_project_manager_sees_whole_root_unit() -> None:
    service = _build_service(_UsersRepo())

    owner_ids = await service._resolve_visible_owner_ids_for_staff_scope(
        current_user=_user(user_id="pm-1", role_id=settings.project_manager_role_id),
    )

    assert set(owner_ids) == {"pm-1", "lead-1", "eco-1", "lead-2", "eco-2"}


@pytest.mark.asyncio
async def test_lead_with_units_sees_only_own_unit_subtree_and_subordinates() -> None:
    service = _build_service(_UsersRepo())

    owner_ids = await service._resolve_visible_owner_ids_for_staff_scope(
        current_user=_user(user_id="lead-1", role_id=settings.lead_economist_role_id),
    )

    # Own unit subtree (Отдел X + Группа X1) + hierarchy subordinates; excludes Отдел Y.
    assert set(owner_ids) == {"lead-1", "eco-1"}


@pytest.mark.asyncio
async def test_economist_with_units_sees_only_own_unit() -> None:
    service = _build_service(_UsersRepo())

    owner_ids = await service._resolve_visible_owner_ids_for_staff_scope(
        current_user=_user(user_id="eco-1", role_id=settings.economist_role_id),
    )

    assert set(owner_ids) == {"eco-1"}


@pytest.mark.asyncio
async def test_lead_with_department_delegation_sees_whole_root_unit() -> None:
    service = _build_service(_UsersRepo())

    owner_ids = await service._resolve_visible_owner_ids_for_staff_scope(
        current_user=_user(
            user_id="lead-1",
            role_id=settings.lead_economist_role_id,
            permissions=frozenset({PermissionCodes.DEPARTMENT_REQUESTS_READ}),
        ),
    )

    assert set(owner_ids) == {"pm-1", "lead-1", "eco-1", "lead-2", "eco-2"}


@pytest.mark.asyncio
async def test_lead_without_unit_membership_falls_back_to_full_department() -> None:
    users = _UsersRepo()
    # lead-1 is no longer a member of any unit -> rollout fallback to hierarchy department.
    users._memberships = [m for m in users._memberships if m[0] != "lead-1"]
    service = _build_service(users)

    owner_ids = await service._resolve_visible_owner_ids_for_staff_scope(
        current_user=_user(user_id="lead-1", role_id=settings.lead_economist_role_id),
    )

    assert set(owner_ids) == {"pm-1", "lead-1", "eco-1", "lead-2", "eco-2"}

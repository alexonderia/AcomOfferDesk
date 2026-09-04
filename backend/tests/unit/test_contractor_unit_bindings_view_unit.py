from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes
from app.services.contractor_units import ContractorUnitService


def _build_service() -> ContractorUnitService:
    users_repo = AsyncMock()
    users_repo.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id),
    )
    # PR #53 (Keycloak→IAM): zone check loads effective root units from
    # memberships; without this stub the admin's zone is empty → Forbidden.
    users_repo.list_active_units = AsyncMock(return_value=[(101, None), (202, None)])
    users_repo.list_active_unit_memberships = AsyncMock(
        return_value=[("admin-1", 101), ("contractor-1", 101)],
    )
    units_repo = AsyncMock()
    units_repo.list_user_root_unit_ids = AsyncMock(return_value=[101])
    units_repo.list_units = AsyncMock(
        return_value=[
            SimpleNamespace(id=101, id_parent=None, is_active=True, name="Финансы"),
            SimpleNamespace(id=202, id_parent=None, is_active=True, name="Логистика"),
        ],
    )
    return ContractorUnitService(users=users_repo, units=units_repo)


@pytest.mark.asyncio
async def test_admin_without_profile_read_can_view_bindings():
    service = _build_service()
    admin = CurrentUser(
        user_id="admin-1",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="admin",
        role_id=settings.admin_role_id,
        status="active",
        permissions=frozenset({PermissionCodes.USERS_STATUS_UPDATE}),
    )

    state = await service.list_bindings(current_user=admin, contractor_user_id="contractor-1")

    assert state.can_manage is True
    bound_by_unit = {item.unit_id: item.is_bound for item in state.items}
    manage_by_unit = {item.unit_id: item.can_manage for item in state.items}
    assert bound_by_unit == {101: True, 202: False}
    assert manage_by_unit == {101: True, 202: False}


@pytest.mark.asyncio
async def test_list_bindings_for_users_batches_in_one_membership_load():
    users_repo = AsyncMock()
    users_repo.list_active_units = AsyncMock(return_value=[(101, None), (202, None)])
    users_repo.list_active_unit_memberships = AsyncMock(
        return_value=[("contractor-1", 101), ("contractor-2", 202)],
    )
    units_repo = AsyncMock()
    units_repo.list_user_root_unit_ids = AsyncMock(return_value=[101, 202])
    units_repo.list_units = AsyncMock(
        return_value=[
            SimpleNamespace(id=101, id_parent=None, is_active=True, name="Финансы"),
            SimpleNamespace(id=202, id_parent=None, is_active=True, name="Логистика"),
        ],
    )
    service = ContractorUnitService(users=users_repo, units=units_repo)
    superadmin = CurrentUser(
        user_id="root",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="superadmin",
        role_id=settings.superadmin_role_id,
        status="active",
        permissions=frozenset({PermissionCodes.CONTRACTORS_PROFILE_READ}),
    )

    bindings = await service.list_bindings_for_users(
        current_user=superadmin,
        contractor_user_ids=["contractor-1", "contractor-2"],
    )

    assert set(bindings) == {"contractor-1", "contractor-2"}
    first = {item.unit_id: item.is_bound for item in bindings["contractor-1"].items}
    second = {item.unit_id: item.is_bound for item in bindings["contractor-2"].items}
    assert first == {101: True, 202: False}
    assert second == {101: False, 202: True}
    # Memberships are loaded once for the whole batch, not per contractor.
    users_repo.list_active_unit_memberships.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_without_view_or_manage_cannot_view_bindings():
    service = _build_service()
    user = CurrentUser(
        user_id="op-1",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="economist",
        role_id=settings.economist_role_id,
        status="active",
        permissions=frozenset(),
    )

    with pytest.raises(Forbidden):
        await service.list_bindings(current_user=user, contractor_user_id="contractor-1")

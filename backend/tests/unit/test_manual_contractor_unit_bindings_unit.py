from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services import users as users_module
from app.services.users import ManualContractorCreateInput, ManualContractorService


@pytest.mark.asyncio
async def test_create_manual_contractor_reuses_duplicate_and_binds_to_creator_root_unit(monkeypatch):
    notify_mock = AsyncMock()
    monkeypatch.setattr(users_module, "notify_new_user_registration", notify_mock)

    users_repo = AsyncMock()
    users_repo.find_matching_contractor_user_ids = AsyncMock(return_value=["contractor-existing"])
    users_repo.get_role_by_id = AsyncMock(return_value=SimpleNamespace(role="Контрагент"))
    users_repo.list_active_units = AsyncMock(return_value=[(101, None)])
    users_repo.list_active_unit_memberships = AsyncMock(return_value=[("economist-1", 101)])

    units_repo = AsyncMock()
    units_repo.list_user_root_unit_ids = AsyncMock(return_value=[101])
    units_repo.list_units = AsyncMock(
        return_value=[SimpleNamespace(id=101, id_parent=None, is_active=True, name="Финансы")],
    )
    units_repo.get_member = AsyncMock(return_value=None)
    units_repo.add_member = AsyncMock()

    service = ManualContractorService(
        users=users_repo,
        profiles=AsyncMock(),
        company_contacts=AsyncMock(),
        user_auth_accounts=AsyncMock(),
        units=units_repo,
    )

    current_user = CurrentUser(
        user_id="economist-1",
        role_id=settings.economist_role_id,
        status="active",
        permissions=frozenset({"contractors.manual.create"}),
    )

    user_id = await service.create_manual_contractor(
        current_user=current_user,
        data=ManualContractorCreateInput(
            company_name="ООО Ромашка",
            inn="7707083893",
            company_phone="+79991234567",
            company_mail="office@example.com",
        ),
    )

    assert user_id == "contractor-existing"
    units_repo.add_member.assert_awaited_once()
    added_membership = units_repo.add_member.await_args.args[0]
    assert added_membership.id_unit == 101
    assert added_membership.id_user == "contractor-existing"
    notify_mock.assert_not_awaited()
    users_repo.add.assert_not_awaited()

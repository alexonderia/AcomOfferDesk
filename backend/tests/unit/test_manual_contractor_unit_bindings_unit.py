from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services import users as users_module
from app.services.contractor_units import ContractorUnitService
from app.services.users import ManualContractorCreateInput, ManualContractorService


@pytest.mark.asyncio
async def test_create_manual_contractor_reuses_duplicate_and_binds_to_creator_root_unit(monkeypatch):
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
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="economist",
        role_id=settings.economist_role_id,
        status="active",
        permissions=frozenset({"contractors.manual.create"}),
    )

    result = await service.create_manual_contractor(
        current_user=current_user,
        data=ManualContractorCreateInput(
            company_name="ООО Ромашка",
            inn="7707083893",
            company_phone="+79991234567",
            company_mail="office@example.com",
        ),
    )

    assert result.user_id == "contractor-existing"
    assert result.created is False
    units_repo.add_member.assert_awaited_once()
    added_membership = units_repo.add_member.await_args.args[0]
    assert added_membership.id_unit == 101
    assert added_membership.id_user == "contractor-existing"
    users_repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_contractor_access_uses_effective_root_unit_memberships():
    users_repo = AsyncMock()
    users_repo.list_active_units = AsyncMock(return_value=[(101, None)])
    users_repo.list_active_unit_memberships = AsyncMock(
        return_value=[("lead-1", 101), ("contractor-1", 101)]
    )
    service = ContractorUnitService(users=users_repo, units=AsyncMock())
    current_user = CurrentUser(
        user_id="lead-1",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="lead_economist",
        role_id=settings.lead_economist_role_id,
        status="active",
        permissions=frozenset({"contractors.read"}),
    )

    assert await service.can_access_contractor(
        current_user=current_user,
        contractor_user_id="contractor-1",
    ) is True


@pytest.mark.asyncio
async def test_security_officer_can_access_contractors_without_unit_membership():
    users_repo = AsyncMock()
    service = ContractorUnitService(users=users_repo, units=AsyncMock())
    current_user = CurrentUser(
        user_id="security-1",
        iam_account_id="00000000-0000-4000-8000-000000000001",
        iam_session_id="00000000-0000-4000-8000-000000000002",
        system_role="security_officer",
        role_id=settings.security_officer_role_id,
        status="active",
        permissions=frozenset({"contractors.read"}),
    )

    assert await service.can_access_contractor(
        current_user=current_user,
        contractor_user_id="contractor-1",
    ) is True

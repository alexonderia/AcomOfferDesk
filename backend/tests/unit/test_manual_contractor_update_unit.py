from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services import users as users_module
from app.services.users import ManualContractorService, ManualContractorUpdateInput, PLACEHOLDER_TEXT


@pytest.mark.asyncio
async def test_update_manual_contractor_creates_missing_company_contacts(monkeypatch):
    monkeypatch.setattr(users_module, "_bind_keycloak_account", AsyncMock())
    monkeypatch.setattr(users_module, "_sync_keycloak_role_after_bind", AsyncMock())

    keycloak_admin = AsyncMock()
    keycloak_admin.ensure_user = AsyncMock(return_value=SimpleNamespace(id="kc-subject-1"))

    user = SimpleNamespace(
        id="contractor-no-company",
        id_role=settings.contractor_role_id,
    )
    profile = SimpleNamespace(
        id="contractor-no-company",
        full_name="Иван Петров",
        phone="+79990000000",
        mail="ivan@example.com",
    )
    created_company = {}

    async def add_company(contact) -> None:
        created_company["value"] = contact

    users_repo = AsyncMock()
    users_repo.get_by_id = AsyncMock(return_value=user)
    users_repo.has_legacy_messenger_account = AsyncMock(return_value=False)

    profiles_repo = AsyncMock()
    profiles_repo.get_by_id = AsyncMock(return_value=profile)

    company_contacts_repo = AsyncMock()
    company_contacts_repo.get_by_id = AsyncMock(return_value=None)
    company_contacts_repo.add = AsyncMock(side_effect=add_company)

    service = ManualContractorService(
        users=users_repo,
        profiles=profiles_repo,
        company_contacts=company_contacts_repo,
        user_auth_accounts=AsyncMock(),
        keycloak_admin=keycloak_admin,
    )

    current_user = CurrentUser(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        status="active",
        permissions=frozenset({"contractors.manual.manage"}),
    )

    result = await service.update_manual_contractor(
        current_user=current_user,
        user_id="contractor-no-company",
        data=ManualContractorUpdateInput(company_mail="office@example.com"),
    )

    assert result == "contractor-no-company"
    company_contacts_repo.add.assert_awaited_once()
    contact = created_company["value"]
    assert contact.id == "contractor-no-company"
    assert contact.mail == "office@example.com"
    assert contact.company_name == PLACEHOLDER_TEXT
    assert contact.inn == PLACEHOLDER_TEXT

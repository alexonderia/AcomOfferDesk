"""Unit tests: Keycloak app.* role sync after user creation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services import users as users_module
from app.services.users import ManualContractorCreateInput, ManualContractorService


@pytest.mark.asyncio
async def test_create_manual_contractor_syncs_keycloak_app_contractor_role(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_enabled", True)

    sync_mock = AsyncMock()
    monkeypatch.setattr(users_module, "sync_keycloak_app_role_for_user", sync_mock)

    keycloak_admin = AsyncMock()
    keycloak_admin.ensure_user = AsyncMock(
        return_value=SimpleNamespace(id="kc-subject-1"),
    )

    service = ManualContractorService(
        users=AsyncMock(),
        profiles=AsyncMock(),
        company_contacts=AsyncMock(),
        user_auth_accounts=AsyncMock(),
        keycloak_admin=keycloak_admin,
    )
    service._users.exists = AsyncMock(return_value=False)
    service._users.add = AsyncMock()
    service._profiles.add = AsyncMock()
    service._company_contacts.add = AsyncMock()

    bind_mock = AsyncMock()
    monkeypatch.setattr(users_module, "_bind_keycloak_account", bind_mock)

    login = await service._create_manual_contractor(
        data=ManualContractorCreateInput(
            company_name='ООО "Тест"',
            inn="7707083893",
            company_phone="+79991234567",
        )
    )

    assert login
    bind_mock.assert_awaited_once()
    sync_mock.assert_awaited_once()
    assert sync_mock.await_args.kwargs["local_role_id"] == settings.contractor_role_id
    assert sync_mock.await_args.kwargs["keycloak_user_id"] == "kc-subject-1"


@pytest.mark.asyncio
async def test_create_manual_contractor_notify_does_not_use_missing_full_name(monkeypatch):
    notify_mock = AsyncMock()
    monkeypatch.setattr(users_module, "notify_new_user_registration", notify_mock)
    monkeypatch.setattr(users_module, "_bind_keycloak_account", AsyncMock())
    monkeypatch.setattr(users_module, "_sync_keycloak_role_after_bind", AsyncMock())

    keycloak_admin = AsyncMock()
    keycloak_admin.ensure_user = AsyncMock(return_value=SimpleNamespace(id="kc-subject-2"))

    users_repo = AsyncMock()
    users_repo.exists = AsyncMock(return_value=False)
    users_repo.get_role_by_id = AsyncMock(return_value=SimpleNamespace(role="Контрагент"))

    service = ManualContractorService(
        users=users_repo,
        profiles=AsyncMock(),
        company_contacts=AsyncMock(),
        user_auth_accounts=AsyncMock(),
        keycloak_admin=keycloak_admin,
    )

    company = 'ООО "Кубик"'
    await service.create_manual_contractor(
        current_user=CurrentUser(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            status="active",
            permissions=frozenset({"contractors.manual.create"}),
        ),
        data=ManualContractorCreateInput(
            company_name=company,
            inn="2365485695",
            company_phone="+79999999999",
            company_mail="kkybikkik@gmail.com",
        ),
    )

    notify_mock.assert_awaited_once()
    ctx = notify_mock.await_args.args[0]
    assert ctx.source == "manual_contractor"
    assert ctx.full_name is None
    assert ctx.company_name == company

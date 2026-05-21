"""Unit tests: Keycloak app.* role sync after user creation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
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

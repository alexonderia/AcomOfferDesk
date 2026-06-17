from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.permissions import PermissionCodes
from app.services import users as users_module
from app.services.users import UserStatusService


@pytest.mark.asyncio
async def test_review_contractor_activation_syncs_keycloak_app_role_and_logs_out_sessions(monkeypatch):
    monkeypatch.setattr(settings, "telegram_legacy_enabled", False)

    sync_mock = AsyncMock()
    monkeypatch.setattr(users_module, "sync_keycloak_app_role_for_user", sync_mock)
    monkeypatch.setattr(users_module, "notify_contractor_status_changed_email", AsyncMock(return_value=False))

    user = SimpleNamespace(
        id="contractor-1",
        id_role=settings.contractor_role_id,
        status="review",
        tg_user_id=None,
    )
    users_repo = AsyncMock()
    users_repo.get_by_id = AsyncMock(return_value=user)

    async def _update_status(target_user, next_status: str) -> None:
        target_user.status = next_status

    users_repo.update_status = AsyncMock(side_effect=_update_status)

    profiles_repo = AsyncMock()
    profiles_repo.get_by_id = AsyncMock(return_value=SimpleNamespace(mail="contractor@example.com"))

    user_auth_accounts = AsyncMock()
    user_auth_accounts.get_by_user_provider = AsyncMock(
        return_value=SimpleNamespace(external_subject_id="kc-subject-1")
    )

    keycloak_admin = AsyncMock()
    keycloak_admin.logout_user_sessions = AsyncMock()

    service = UserStatusService(
        users=users_repo,
        tg_users=AsyncMock(),
        profiles=profiles_repo,
        user_auth_accounts=user_auth_accounts,
        keycloak_admin=keycloak_admin,
    )

    result = await service.update_statuses(
        current_user=CurrentUser(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            status="active",
            permissions=frozenset({PermissionCodes.USERS_STATUS_UPDATE}),
        ),
        user_id="contractor-1",
        user_status="active",
        tg_status=None,
    )

    assert result.user_status == "active"
    sync_mock.assert_awaited_once()
    assert sync_mock.await_args.kwargs["keycloak_user_id"] == "kc-subject-1"
    assert sync_mock.await_args.kwargs["local_role_id"] == settings.contractor_role_id
    keycloak_admin.logout_user_sessions.assert_awaited_once_with(user_id="kc-subject-1")


@pytest.mark.asyncio
async def test_review_contractor_activation_without_keycloak_link_skips_role_sync(monkeypatch):
    monkeypatch.setattr(settings, "telegram_legacy_enabled", False)

    sync_mock = AsyncMock()
    monkeypatch.setattr(users_module, "sync_keycloak_app_role_for_user", sync_mock)
    monkeypatch.setattr(users_module, "notify_contractor_status_changed_email", AsyncMock(return_value=False))

    user = SimpleNamespace(
        id="contractor-2",
        id_role=settings.contractor_role_id,
        status="review",
        tg_user_id=None,
    )
    users_repo = AsyncMock()
    users_repo.get_by_id = AsyncMock(return_value=user)

    async def _update_status(target_user, next_status: str) -> None:
        target_user.status = next_status

    users_repo.update_status = AsyncMock(side_effect=_update_status)

    service = UserStatusService(
        users=users_repo,
        tg_users=AsyncMock(),
        profiles=AsyncMock(get_by_id=AsyncMock(return_value=SimpleNamespace(mail="contractor2@example.com"))),
        user_auth_accounts=AsyncMock(get_by_user_provider=AsyncMock(return_value=None)),
        keycloak_admin=AsyncMock(),
    )

    result = await service.update_statuses(
        current_user=CurrentUser(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            status="active",
            permissions=frozenset({PermissionCodes.USERS_STATUS_UPDATE}),
        ),
        user_id="contractor-2",
        user_status="active",
        tg_status=None,
    )

    assert result.user_status == "active"
    sync_mock.assert_not_awaited()


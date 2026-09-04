from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services.users import UserSelfService


@pytest.mark.asyncio
async def test_profile_update_is_local_only() -> None:
    profile = SimpleNamespace(
        id="contractor-1",
        full_name="Старое имя",
        phone="+79991234567",
        mail="old@example.com",
    )
    profiles = AsyncMock()
    profiles.get_by_id = AsyncMock(return_value=profile)
    auth_accounts = AsyncMock()
    service = UserSelfService(
        users=AsyncMock(),
        profiles=profiles,
        company_contacts=AsyncMock(),
        user_status_periods=AsyncMock(),
        user_auth_accounts=auth_accounts,
    )

    await service.update_my_profile_for_review_onboarding(
        CurrentUser(
            user_id=profile.id,
            iam_account_id="00000000-0000-4000-8000-000000000001",
            iam_session_id="00000000-0000-4000-8000-000000000002",
            system_role="contractor",
            role_id=settings.contractor_role_id,
            status="review",
            permissions=frozenset(),
        ),
        full_name="Новое имя",
        phone="+79990001122",
        mail="new@example.com",
    )

    assert profile.full_name == "Новое имя"
    assert profile.mail == "new@example.com"
    auth_accounts.get_by_user_provider.assert_not_awaited()

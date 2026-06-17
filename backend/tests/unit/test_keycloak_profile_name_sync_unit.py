from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.services.identity_sync import IdentitySyncService
from app.services.keycloak_oidc import KeycloakAccessTokenClaims
from app.services.users import UserSelfService, _split_full_name_for_keycloak


class _ProfilesRepo:
    def __init__(self, profile=None) -> None:
        self.profile = profile

    async def get_by_id(self, user_id: str):
        _ = user_id
        return self.profile

    async def add(self, profile) -> None:
        self.profile = profile


class _UserAuthAccountsRepo:
    def __init__(self, account=None) -> None:
        self.account = account

    async def get_by_user_provider(self, *, user_id: str, provider: str, include_inactive: bool = False):
        _ = (user_id, provider, include_inactive)
        return self.account


def test_split_full_name_for_keycloak_preserves_hyphenated_surname_and_multiword_first_name():
    parts = _split_full_name_for_keycloak("Сидоров-Петров Жан Клод Иванович")

    assert parts.last_name == "Сидоров-Петров"
    assert parts.first_name == "Жан Клод"
    assert parts.middle_name == "Иванович"
    assert parts.should_sync is True


@pytest.mark.asyncio
async def test_review_onboarding_profile_update_syncs_linked_keycloak_name_parts():
    profile = SimpleNamespace(
        id="contractor-review-1",
        full_name="Иванов-Сидоров Анна Мария Петровна",
        phone="+79991234567",
        mail="before@example.com",
    )
    profiles = _ProfilesRepo(profile)
    user_auth_accounts = _UserAuthAccountsRepo(
        SimpleNamespace(external_username="contractor-review-1", external_subject_id="kc-1")
    )
    keycloak_admin = AsyncMock()
    keycloak_admin.ensure_user = AsyncMock(return_value=SimpleNamespace(id="kc-1"))

    service = UserSelfService(
        users=AsyncMock(),
        profiles=profiles,
        company_contacts=AsyncMock(),
        user_status_periods=AsyncMock(),
        user_auth_accounts=user_auth_accounts,
        keycloak_admin=keycloak_admin,
    )

    await service.update_my_profile_for_review_onboarding(
        CurrentUser(
            user_id="contractor-review-1",
            role_id=settings.contractor_role_id,
            status="review",
            permissions=frozenset(),
        ),
        full_name="Иванов-Сидоров Анна Мария Петровна",
        phone="+79990001122",
        mail="after@example.com",
    )

    keycloak_admin.ensure_user.assert_awaited_once()
    kwargs = keycloak_admin.ensure_user.await_args.kwargs
    assert kwargs["username"] == "contractor-review-1"
    assert kwargs["previous_username"] == "contractor-review-1"
    assert kwargs["email"] == "after@example.com"
    assert kwargs["last_name"] == "Иванов-Сидоров"
    assert kwargs["first_name"] == "Анна Мария"
    assert kwargs["middle_name"] == "Петровна"
    assert kwargs["sync_names"] is True


@pytest.mark.asyncio
async def test_identity_sync_overwrites_local_profile_with_latest_keycloak_name():
    profile = SimpleNamespace(
        id="user-1",
        full_name="Старое Имя",
        phone="+79991234567",
        mail="old@example.com",
    )
    profiles = _ProfilesRepo(profile)
    service = IdentitySyncService(
        users=AsyncMock(),
        user_auth_accounts=AsyncMock(),
        user_contact_channels=AsyncMock(),
        profiles=profiles,
    )

    await service._sync_profile_basics(
        user=SimpleNamespace(id="user-1"),
        claims=KeycloakAccessTokenClaims(
            subject="kc-1",
            issuer="issuer",
            issued_at=1,
            expires_at=2,
            preferred_username="user-1",
            full_name=None,
            given_name="Анна Мария",
            family_name="Иванова",
            middle_name="Петровна",
            email="new@example.com",
            email_verified=True,
            realm_roles=frozenset(),
            api_roles=frozenset(),
        ),
    )

    assert profile.full_name == "Иванова Анна Мария Петровна"
    assert profile.mail == "new@example.com"

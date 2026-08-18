from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api.v1.auth import _session_response
from app.core.config import settings
from app.core.registration_invite import RegistrationInviteTokenCodec
from app.domain.authorization import has_permission
from app.domain.exceptions import Conflict, Forbidden, Unauthorized
from app.domain.iam_status import iam_auth_status_for_user_status
from app.domain.permissions import PermissionCodes
from app.services.registration_submit import RegistrationSubmitService
from app.services.users import UserStatusService


class _Users:
    def __init__(self, user) -> None:
        self.user = user

    async def get_by_id(self, user_id: str):
        return self.user if self.user.id == user_id else None

    async def update_status(self, user, status: str) -> None:
        user.status = status


class _Profiles:
    async def get_by_id(self, user_id: str):
        _ = user_id
        return SimpleNamespace(mail="user@example.com")


class _Channels:
    def __init__(self, *, verified: bool) -> None:
        self.verified = verified

    async def get_primary_by_type(self, *, user_id: str, channel_type: str, include_inactive: bool = False):
        _ = (user_id, channel_type, include_inactive)
        return SimpleNamespace(is_verified=self.verified, channel_value="user@example.com")


@pytest.mark.parametrize(
    ("main_status", "expected_iam"),
    [
        ("active", "active"),
        ("review", "pending"),
        ("inactive", "blocked"),
        ("blacklist", "blocked"),
    ],
)
def test_iam_status_mapping_does_not_activate_review(main_status: str, expected_iam: str) -> None:
    assert iam_auth_status_for_user_status(main_status) == expected_iam


@pytest.mark.asyncio
async def test_approval_requires_verified_email_and_permission(make_current_user, monkeypatch) -> None:
    user = SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, status="review")
    service = UserStatusService(
        _Users(user),
        _Profiles(),
        user_contact_channels=_Channels(verified=False),
    )
    admin = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={PermissionCodes.USERS_STATUS_UPDATE, PermissionCodes.USERS_REGISTRATION_APPROVE},
    )
    with pytest.raises(Conflict):
        await service.update_statuses(current_user=admin, user_id="contractor-1", user_status="active")


@pytest.mark.asyncio
async def test_approval_rejects_without_registration_permission(make_current_user) -> None:
    user = SimpleNamespace(id="contractor-1", id_role=settings.contractor_role_id, status="review")
    service = UserStatusService(
        _Users(user),
        _Profiles(),
        user_contact_channels=_Channels(verified=True),
    )
    economist = make_current_user(
        user_id="eco-1",
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.USERS_STATUS_UPDATE},
    )
    with pytest.raises(Forbidden):
        await service.update_statuses(current_user=economist, user_id="contractor-1", user_status="active")


def test_session_business_access_requires_active_without_complete_profile(make_current_user) -> None:
    active = make_current_user(status="active")
    first_login = make_current_user(status="active", onboarding_state="first_login")
    review = make_current_user(
        role_id=settings.contractor_role_id,
        status="review",
        permissions={PermissionCodes.PROFILE_MANAGE_OWN},
    )
    assert _session_response(active).data.business_access is True
    assert _session_response(active).data.onboarding_state is None
    assert _session_response(first_login).data.business_access is False
    assert _session_response(first_login).data.onboarding_state == "first_login"
    assert _session_response(review).data.business_access is False
    assert _session_response(review).data.onboarding_state == "review"
    assert first_login.onboarding_state == "first_login"
    assert has_permission(first_login, PermissionCodes.PROFILE_MANAGE_OWN) is False
    first_login_with_profile = make_current_user(
        status="active",
        onboarding_state="first_login",
        permissions={PermissionCodes.PROFILE_MANAGE_OWN, PermissionCodes.REQUESTS_READ},
    )
    assert has_permission(first_login_with_profile, PermissionCodes.PROFILE_MANAGE_OWN) is True
    assert has_permission(first_login_with_profile, PermissionCodes.REQUESTS_READ) is False


class _SubmitUow:
    def __init__(self) -> None:
        self.added_users: list = []
        self.added_profiles: list = []
        self.added_companies: list = []
        self.added_bindings: list = []
        self.channels: list = []
        self.existing_logins: set[str] = set()
        self.existing_emails: set[str] = set()
        self.users = SimpleNamespace(exists=self.exists, add=self.add, get_by_id=self._get_user)
        self.profiles = SimpleNamespace(
            exists_by_mail=self.exists_by_mail,
            get_id_by_mail=self.get_id_by_mail,
            get_by_id=self._get_profile,
            add=self.add,
        )
        self.company_contacts = SimpleNamespace(add=self.add, get_by_id=self._get_company)
        self.user_contact_channels = SimpleNamespace(
            exists_primary_email=self.exists_primary_email,
            list_user_ids_by_primary_email=self.list_user_ids_by_primary_email,
            upsert_channel=self.upsert_channel,
            get_primary_by_type=self.get_primary_by_type,
        )
        self.user_auth_accounts = SimpleNamespace(
            add=self.add,
            get_by_external_email=self.get_by_external_email,
            get_by_user_provider=self.get_by_user_provider,
        )

    async def exists(self, login: str) -> bool:
        return login in self.existing_logins

    async def exists_by_mail(self, *, email: str, exclude_user_id: str | None = None) -> bool:
        for profile in self.added_profiles:
            if profile.mail == email and profile.id != exclude_user_id:
                return True
        if exclude_user_id is None:
            return email in self.existing_emails
        return False

    async def exists_primary_email(self, *, email: str, exclude_user_id: str | None = None) -> bool:
        for channel in self.channels:
            if channel.get("channel_value") == email and channel.get("user_id") != exclude_user_id:
                return True
        if exclude_user_id is None:
            return email in self.existing_emails
        return False

    async def get_id_by_mail(self, *, email: str) -> str | None:
        normalized = email.strip().lower()
        for profile in self.added_profiles:
            if (profile.mail or "").strip().lower() == normalized:
                return profile.id
        return None

    async def list_user_ids_by_primary_email(self, *, email: str) -> list[str]:
        normalized = email.strip().lower()
        return [
            channel["user_id"]
            for channel in self.channels
            if channel.get("channel_value") == normalized
        ]

    async def get_by_external_email(self, *, provider: str, email: str):
        _ = provider
        normalized = email.strip().lower()
        for binding in self.added_bindings:
            if (getattr(binding, "external_email", "") or "").strip().lower() == normalized:
                return binding
        return None

    async def get_by_user_provider(self, *, user_id: str, provider: str):
        _ = provider
        for binding in self.added_bindings:
            if binding.id_user == user_id:
                return binding
        return None

    async def add(self, item) -> None:
        if item.__class__.__name__ == "User":
            self.added_users.append(item)
            self.existing_logins.add(item.id)
        elif item.__class__.__name__ == "Profile":
            self.added_profiles.append(item)
            if item.mail:
                self.existing_emails.add(item.mail)
        elif item.__class__.__name__ == "CompanyContact":
            self.added_companies.append(item)
        else:
            self.added_bindings.append(item)

    async def upsert_channel(self, **kwargs):
        self.channels.append(kwargs)
        return SimpleNamespace(is_verified=kwargs.get("is_verified", False))

    async def _get_user(self, user_id: str):
        return next((item for item in self.added_users if item.id == user_id), None)

    async def _get_profile(self, user_id: str):
        return next((item for item in self.added_profiles if item.id == user_id), SimpleNamespace(id=user_id, mail="invitee@example.com"))

    async def _get_company(self, user_id: str):
        return next((item for item in self.added_companies if item.id == user_id), None)

    async def get_primary_by_type(self, **kwargs):
        user_id = kwargs.get("user_id")
        for channel in reversed(self.channels):
            if channel.get("user_id") == user_id:
                return SimpleNamespace(
                    is_verified=channel.get("is_verified", False),
                    channel_value=channel.get("channel_value"),
                )
        return None

    def add_after_commit_hook(self, hook) -> None:
        _ = hook


class _IamClient:
    def __init__(self) -> None:
        self.provisioned = []
        self.actions = []

    async def provision_registration_credentials(self, **kwargs):
        self.provisioned.append(kwargs)
        return SimpleNamespace(
            id="00000000-0000-4000-8000-000000000099",
            login=kwargs["login"],
            role=kwargs["role"],
            auth_status=kwargs["auth_status"],
            password_set=True,
            created=True,
        )

    async def create_action_token(self, *, account_id, purpose, context=None):
        self.actions.append({"account_id": str(account_id), "purpose": purpose, "context": context})
        return SimpleNamespace(token="verify-raw-token")


def _invite_token() -> str:
    return RegistrationInviteTokenCodec(secret=settings.email_verification_secret, ttl_seconds=3600).issue(
        email="invitee@example.com",
        role_id=settings.contractor_role_id,
        inviter_id="admin-1",
        unit_id=8,
    )


@pytest.mark.asyncio
async def test_registration_submit_creates_review_pending_unverified_user(monkeypatch) -> None:
    uow = _SubmitUow()
    iam = _IamClient()

    async def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.services.email_verification.EmailVerificationService._send_verification_email", _noop)
    monkeypatch.setattr(settings, "web_base_url", "https://web.example")
    from app.services.email_verification import EmailVerificationService

    EmailVerificationService._request_locks.clear()
    result = await RegistrationSubmitService(uow, iam_client=iam).submit(
        token=_invite_token(),
        login="new.contractor",
        password="correct horse battery staple",
        password_confirmation="correct horse battery staple",
        email="invitee@example.com",
        full_name="Иван Иванов",
        phone="79991234567",
        company_name="ООО Тест",
        inn="7707083893",
        company_phone="79990001122",
    )
    assert result.status == "review"
    assert uow.added_users[0].status == "review"
    assert not hasattr(uow.added_users[0], "onboarding_state") or getattr(uow.added_users[0], "onboarding_state", None) is None
    assert iam.provisioned[0]["auth_status"] == "pending"
    assert iam.provisioned[0]["password"] == "correct horse battery staple"
    assert uow.channels[0]["is_verified"] is False
    assert iam.actions[0]["purpose"] == "verify_email"
    assert iam.actions[0]["context"] == {"email": "invitee@example.com"}


@pytest.mark.asyncio
async def test_registration_submit_rejects_duplicate_login_and_email() -> None:
    uow = _SubmitUow()
    iam = _IamClient()
    token = _invite_token()
    service = RegistrationSubmitService(uow, iam_client=iam)
    uow.existing_emails.add("invitee@example.com")
    with pytest.raises(Conflict):
        await service.submit(
            token=token,
            login="another.contractor",
            password="correct horse battery staple",
            password_confirmation="correct horse battery staple",
            email="invitee@example.com",
            full_name="Иван Иванов",
            phone="79991234567",
            company_name="ООО Тест",
            inn="7707083893",
            company_phone="79990001122",
        )


@pytest.mark.asyncio
async def test_registration_submit_updates_in_progress_registration(monkeypatch) -> None:
    uow = _SubmitUow()
    iam = _IamClient()

    async def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.services.email_verification.EmailVerificationService._send_verification_email", _noop)
    monkeypatch.setattr(settings, "web_base_url", "https://web.example")
    from app.services.email_verification import EmailVerificationService

    EmailVerificationService._request_locks.clear()
    service = RegistrationSubmitService(uow, iam_client=iam)
    token = _invite_token()
    await service.submit(
        token=token,
        login="new.contractor",
        password="correct horse battery staple",
        password_confirmation="correct horse battery staple",
        email="invitee@example.com",
        full_name="Иван Иванов",
        phone="79991234567",
        company_name="ООО Тест",
        inn="7707083893",
        company_phone="79990001122",
    )
    result = await service.submit(
        token=token,
        login="new.contractor",
        password="replacement password 123",
        password_confirmation="replacement password 123",
        email="fixed@example.com",
        full_name="Пётр Петров",
        phone="79990000000",
        company_name="ООО Новое",
        inn="7707083893",
        company_phone="79990001122",
    )
    assert result.email == "fixed@example.com"
    assert len(uow.added_users) == 1
    assert uow.added_profiles[0].full_name == "Пётр Петров"
    assert uow.added_profiles[0].mail == "fixed@example.com"
    assert uow.added_companies[0].company_name == "ООО Новое"
    assert iam.provisioned[-1]["replace_password"] is True
    assert iam.provisioned[-1]["password"] == "replacement password 123"


@pytest.mark.asyncio
async def test_registration_submit_rejects_invalid_token() -> None:
    with pytest.raises(Unauthorized):
        await RegistrationSubmitService(_SubmitUow(), iam_client=_IamClient()).submit(
            token="not-a-valid-registration-token-value",
            login="new.contractor",
            password="correct horse battery staple",
            password_confirmation="correct horse battery staple",
            email="invitee@example.com",
            full_name="Иван Иванов",
            phone="79991234567",
            company_name="ООО Тест",
            inn="7707083893",
            company_phone="79990001122",
        )

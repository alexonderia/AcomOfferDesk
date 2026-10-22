from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.requests import Request

from app.api.v1 import auth
from app.domain.iam_identity import stable_iam_account_id
from app.services.account_recovery import AccountRecoveryService, GENERIC_RECOVERY_DETAIL


def _request(client_ip: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/password-reset/request",
            "headers": [],
            "scheme": "https",
            "server": ("app.example", 443),
            "client": (client_ip, 12345),
        }
    )


class _Repository:
    def __init__(self, value) -> None:
        self.value = value

    async def get_by_id(self, _value):
        return self.value

    async def get_by_user_provider(self, **_kwargs):
        return self.value

    async def get_primary_by_type(self, **_kwargs):
        return self.value

    async def list_user_ids_by_primary_email(self, **_kwargs):
        return []

    async def exists_by_mail(self, **_kwargs):
        return False

    async def exists_primary_email(self, **_kwargs):
        return False

    async def upsert_channel(self, **_kwargs):
        return SimpleNamespace(is_verified=False, is_primary=True)


class _Uow:
    def __init__(self, *, user=None, profile=None, binding=None, channel=None) -> None:
        self.users = _Repository(user)
        self.profiles = _Repository(profile)
        self.user_auth_accounts = _Repository(binding)
        self.user_contact_channels = _Repository(channel)
        self.hooks = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def add_after_commit_hook(self, hook):
        self.hooks.append(hook)


@pytest.mark.asyncio
async def test_password_reset_response_does_not_enumerate_unknown_login() -> None:
    response = await auth.request_password_reset(
        auth.PasswordResetRequest(login="unknown-user"),
        _request("127.0.0.11"),
        _Uow(),
    )
    assert GENERIC_RECOVERY_DETAIL in response.detail


@pytest.mark.asyncio
async def test_password_reset_issues_iam_action_and_schedules_email(monkeypatch) -> None:
    observed = {}

    class Client:
        async def get_credential_state(self, *, account_id: str):
            return SimpleNamespace(password_set=True, auth_status="active")

        async def create_action_token(self, *, account_id: str, purpose: str, context=None):
            observed.update(account_id=account_id, purpose=purpose, context=context)
            return SimpleNamespace(token="secret-action-token")

    monkeypatch.setattr(auth, "IamClient", Client)
    monkeypatch.setattr("app.services.account_recovery.IamClient", Client)
    uow = _Uow(
        user=SimpleNamespace(id="known-user"),
        profile=SimpleNamespace(mail="known@example.com"),
        binding=SimpleNamespace(external_subject_id="00000000-0000-4000-8000-000000000001"),
        channel=SimpleNamespace(channel_value="known@example.com", is_verified=True),
    )
    response = await auth.request_password_reset(
        auth.PasswordResetRequest(login="known-user"),
        _request("127.0.0.12"),
        uow,
    )
    assert observed == {
        "account_id": "00000000-0000-4000-8000-000000000001",
        "purpose": "password_reset",
        "context": None,
    }
    assert len(uow.hooks) == 1
    assert "secret-action-token" not in response.detail


@pytest.mark.asyncio
async def test_password_reset_without_password_uses_first_access(monkeypatch) -> None:
    observed = {}
    sent = []

    class Client:
        async def get_credential_state(self, *, account_id: str):
            return SimpleNamespace(password_set=False, auth_status="active")

        async def create_action_token(self, *, account_id: str, purpose: str, context=None):
            observed.update(account_id=account_id, purpose=purpose, context=context)
            return SimpleNamespace(token="first-access-raw-token")

    async def _fake_send(self, *args, **kwargs):
        sent.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr(auth, "IamClient", Client)
    monkeypatch.setattr("app.services.account_recovery.IamClient", Client)
    monkeypatch.setattr("app.services.email_verification.IamClient", Client)
    monkeypatch.setattr("app.services.email_verification.SMTPEmailService.send_email", _fake_send)
    monkeypatch.setattr("app.core.config.settings.web_base_url", "https://web.example")
    from app.services.email_verification import EmailVerificationService

    EmailVerificationService._request_locks.clear()
    uow = _Uow(
        user=SimpleNamespace(id="manual-user"),
        profile=SimpleNamespace(mail="manual@example.com"),
        binding=SimpleNamespace(external_subject_id="00000000-0000-4000-8000-000000000001"),
        channel=SimpleNamespace(channel_value="manual@example.com", is_verified=False),
    )
    response = await auth.request_password_reset(
        auth.PasswordResetRequest(login="manual-user"),
        _request("127.0.0.13"),
        uow,
    )
    assert observed == {
        "account_id": "00000000-0000-4000-8000-000000000001",
        "purpose": "first_access",
        "context": {"email": "manual@example.com"},
    }
    assert sent
    assert uow.hooks == []
    assert "first-access-raw-token" not in response.detail
    assert GENERIC_RECOVERY_DETAIL in response.detail


@pytest.mark.asyncio
async def test_legacy_user_gets_iam_binding_and_first_access_setup(monkeypatch) -> None:
    class BindingRepo:
        def __init__(self) -> None:
            self.binding = None
            self.added = []

        async def get_by_user_provider(self, **_kwargs):
            return self.binding

        async def add(self, binding):
            self.binding = binding
            self.added.append(binding)

    class LegacyUow:
        def __init__(self) -> None:
            self.users = _Repository(
                SimpleNamespace(id="legacy-user", id_role=6, status="active")
            )
            self.profiles = _Repository(SimpleNamespace(mail="legacy@example.com"))
            self.user_auth_accounts = BindingRepo()
            self.user_contact_channels = _Repository(
                SimpleNamespace(channel_value="legacy@example.com", is_verified=True)
            )
            self.hooks = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        def add_after_commit_hook(self, hook):
            self.hooks.append(hook)

    account_calls = []

    class Client:
        async def put_account(self, *, account_id, login: str, role: str, auth_status: str):
            account_calls.append((str(account_id), login, role, auth_status))
            return SimpleNamespace(id=str(account_id))

        async def get_credential_state(self, *, account_id: str):
            return SimpleNamespace(password_set=False, auth_status="active")

        async def create_action_token(self, *, account_id: str, purpose: str, context=None):
            return SimpleNamespace(token="legacy-setup-token")

    setup_calls = []

    async def _fake_issue_setup(self, *, user_id: str, email: str):
        setup_calls.append((user_id, email))
        return None

    monkeypatch.setattr(AccountRecoveryService, "issue_setup_after_verified_access", _fake_issue_setup)
    uow = LegacyUow()
    service = AccountRecoveryService(uow, iam_client=Client())

    result = await service.request_recovery(identifier="legacy-user")

    assert GENERIC_RECOVERY_DETAIL in result.detail
    assert account_calls == [
        (str(stable_iam_account_id("legacy-user")), "legacy-user", "economist", "active")
    ]
    assert uow.user_auth_accounts.added
    assert uow.user_auth_accounts.added[0].provider == "iam"
    assert setup_calls == [("legacy-user", "legacy@example.com")]

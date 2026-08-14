from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.requests import Request

from app.api.v1 import auth


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


class _Uow:
    def __init__(self, *, user=None, profile=None, binding=None) -> None:
        self.users = _Repository(user)
        self.profiles = _Repository(profile)
        self.user_auth_accounts = _Repository(binding)
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
    assert "Если учётная запись существует" in response.detail


@pytest.mark.asyncio
async def test_password_reset_issues_iam_action_and_schedules_email(monkeypatch) -> None:
    observed = {}

    class Client:
        async def create_action_token(self, *, account_id: str, purpose: str):
            observed.update(account_id=account_id, purpose=purpose)
            return SimpleNamespace(token="secret-action-token")

    monkeypatch.setattr(auth, "IamClient", Client)
    uow = _Uow(
        user=SimpleNamespace(id="known-user"),
        profile=SimpleNamespace(mail="known@example.com"),
        binding=SimpleNamespace(external_subject_id="00000000-0000-4000-8000-000000000001"),
    )
    response = await auth.request_password_reset(
        auth.PasswordResetRequest(login="known-user"),
        _request("127.0.0.12"),
        uow,
    )
    assert observed == {
        "account_id": "00000000-0000-4000-8000-000000000001",
        "purpose": "password_reset",
    }
    assert len(uow.hooks) == 1
    assert "secret-action-token" not in response.detail

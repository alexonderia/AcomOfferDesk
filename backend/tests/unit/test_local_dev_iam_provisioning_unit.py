from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.scripts import provision_local_dev_iam_users


@pytest.mark.asyncio
async def test_local_dev_provisioning_creates_then_reuses_binding_without_password_transport(
    monkeypatch,
) -> None:
    state = {"binding": None, "client_calls": []}

    class AuthAccounts:
        async def get_by_user_provider(self, **_kwargs):
            return state["binding"]

        async def get_conflicting_subject(self, **_kwargs):
            return None

        async def add(self, binding):
            state["binding"] = binding

    class FakeUow:
        user_auth_accounts = AuthAccounts()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    class FakeClient:
        async def provision_local_development_account(self, **kwargs):
            state["client_calls"].append(kwargs)
            return SimpleNamespace(
                id=str(kwargs["account_id"]),
                created=len(state["client_calls"]) == 1,
            )

    monkeypatch.setattr(provision_local_dev_iam_users, "UnitOfWork", FakeUow)
    candidate = provision_local_dev_iam_users.LocalDevCandidate(login="superadmin", role_id=1)

    first = await provision_local_dev_iam_users.provision_candidate(candidate, client=FakeClient())
    second = await provision_local_dev_iam_users.provision_candidate(candidate, client=FakeClient())

    assert first.account_created is True and first.binding_created is True
    assert second.account_created is False and second.binding_created is False
    assert state["binding"].is_active is True
    assert all(set(call) == {"account_id", "login", "role"} for call in state["client_calls"])


@pytest.mark.asyncio
async def test_local_dev_run_is_refused_outside_local_development(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(RuntimeError, match="allowed only"):
        await provision_local_dev_iam_users.run(apply=False)

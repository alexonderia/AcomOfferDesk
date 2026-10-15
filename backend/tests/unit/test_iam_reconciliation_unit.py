from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.scripts import reconcile_iam_accounts


@pytest.mark.asyncio
async def test_reconciliation_report_is_read_only_and_strict_mode_detects_drift(
    monkeypatch,
    capsys,
) -> None:
    class AuthAccounts:
        async def list_for_provider(self, *, provider: str):
            assert provider == "iam"
            return [
                SimpleNamespace(
                    external_subject_id="00000000-0000-4000-8000-000000000001",
                    is_active=False,
                )
            ]

    class FakeUow:
        user_auth_accounts = AuthAccounts()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    class FakeClient:
        async def reconcile_account_ids(self, account_ids: list[str]):
            assert account_ids == ["00000000-0000-4000-8000-000000000001"]
            return (
                ["00000000-0000-4000-8000-000000000002"],
                ["00000000-0000-4000-8000-000000000003"],
            )

    monkeypatch.setattr(reconcile_iam_accounts, "UnitOfWork", FakeUow)
    monkeypatch.setattr(reconcile_iam_accounts, "IamClient", FakeClient)

    assert await reconcile_iam_accounts.run(strict=False) == 0
    assert await reconcile_iam_accounts.run(strict=True) == 2
    output = capsys.readouterr().out
    assert "orphan_iam_account_ids" in output
    assert "missing_iam_account_ids" in output
    assert "inactive_iam_binding_account_ids" in output
    assert "password" not in output.lower()
    assert "token" not in output.lower()

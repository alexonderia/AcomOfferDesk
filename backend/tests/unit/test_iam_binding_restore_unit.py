from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.domain.exceptions import Conflict, NotFound
from app.domain.iam_identity import stable_iam_account_id
from app.infrastructure.iam_client import IamCredentialState
from app.models.auth_models import UserAuthAccount
from app.services.iam_bindings import sync_existing_iam_binding


ACCOUNT = UUID("00000000-0000-4000-8000-000000000001")
LOGIN = "migration-example"


@pytest.fixture
def accounts():
    store = SimpleNamespace(
        get_by_user_provider=AsyncMock(return_value=None),
        get_conflicting_subject=AsyncMock(return_value=None),
        add=AsyncMock(),
    )

    async def save(binding: UserAuthAccount) -> None:
        store.get_by_user_provider.return_value = binding

    store.add.side_effect = save
    return store


def iam_state(*, login=LOGIN, role="contractor", password_set=True, account_id=ACCOUNT):
    return SimpleNamespace(get_credential_state=AsyncMock(return_value=IamCredentialState(
        id=str(account_id), login=login, role=role, auth_status="active", password_set=password_set,
    )))


@pytest.mark.asyncio
async def test_read_only_plan_then_restore_existing_iam_account_and_repeat(accounts):
    client = iam_state()
    options = dict(
        user_auth_accounts=accounts, user_id=LOGIN, role_id=3,
        iam_client=client, iam_account_id=ACCOUNT,
    )

    plan = await sync_existing_iam_binding(**options, apply=False)
    assert plan.action == "create_binding"
    assert plan.binding_active is None
    assert plan.password_set is True
    accounts.add.assert_not_awaited()

    applied = await sync_existing_iam_binding(**options, apply=True)
    saved = accounts.add.await_args.args[0]
    assert applied.action == "create_binding"
    assert (saved.id_user, saved.provider, saved.external_subject_id, saved.external_username, saved.is_active) == (
        LOGIN, "iam", str(ACCOUNT), LOGIN, True,
    )

    assert (await sync_existing_iam_binding(**options, apply=True)).action == "unchanged"
    accounts.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_repairs_login_metadata_without_activating_a_disabled_binding(accounts):
    binding = UserAuthAccount(
        id_user=LOGIN, provider="iam", external_subject_id=str(ACCOUNT),
        external_username=None, is_active=False, external_email="existing@example.invalid",
    )
    accounts.get_by_user_provider.return_value = binding
    options = dict(user_auth_accounts=accounts, user_id=LOGIN, role_id=3, iam_client=iam_state(password_set=False))

    assert (await sync_existing_iam_binding(**options, apply=False)).action == "update_binding_login"
    assert binding.external_username is None
    result = await sync_existing_iam_binding(**options, apply=True)

    assert result.binding_active is False
    assert result.password_set is False
    assert binding.external_username == LOGIN
    assert binding.external_email == "existing@example.invalid"
    assert binding.is_active is False
    accounts.add.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("mismatch", ["subject", "login", "role"])
async def test_never_binds_a_mismatched_iam_identity(accounts, mismatch):
    client = iam_state(
        account_id=UUID(int=2) if mismatch == "subject" else ACCOUNT,
        login="other-login" if mismatch == "login" else LOGIN,
        role="economist" if mismatch == "role" else "contractor",
    )
    with pytest.raises(Conflict):
        await sync_existing_iam_binding(
            user_auth_accounts=accounts, user_id=LOGIN, role_id=3,
            iam_client=client, iam_account_id=ACCOUNT, apply=True,
        )
    accounts.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_subject_cannot_be_reassigned_or_shared(accounts):
    client = iam_state()
    accounts.get_conflicting_subject.return_value = object()
    with pytest.raises(Conflict):
        await sync_existing_iam_binding(
            user_auth_accounts=accounts, user_id=LOGIN, role_id=3,
            iam_client=client, iam_account_id=ACCOUNT, apply=True,
        )
    accounts.get_conflicting_subject.return_value = None
    accounts.get_by_user_provider.return_value = SimpleNamespace(external_subject_id=str(UUID(int=2)))
    with pytest.raises(Conflict):
        await sync_existing_iam_binding(
            user_auth_accounts=accounts, user_id=LOGIN, role_id=3,
            iam_client=client, iam_account_id=ACCOUNT, apply=True,
        )
    client.get_credential_state.assert_not_awaited()
    accounts.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_absent_iam_account_is_reported_without_creating_anything(accounts):
    client = SimpleNamespace(get_credential_state=AsyncMock(side_effect=NotFound("IAM account not found")))
    with pytest.raises(NotFound):
        await sync_existing_iam_binding(
            user_auth_accounts=accounts, user_id=LOGIN, role_id=3, iam_client=client, apply=True,
        )
    client.get_credential_state.assert_awaited_once_with(account_id=str(stable_iam_account_id(LOGIN)))
    accounts.add.assert_not_awaited()

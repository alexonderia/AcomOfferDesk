from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.domain.exceptions import AuthenticationUnavailable, Conflict
from app.domain.iam_identity import stable_iam_account_id
from app.services.iam_bindings import ensure_user_iam_account


@pytest.fixture
def context():
    repo = AsyncMock()
    repo.get_by_user_provider.return_value = None
    repo.get_conflicting_subject.return_value = None
    client = AsyncMock()
    client.put_account.side_effect = lambda **kw: SimpleNamespace(
        id=kw['account_id'], login=kw['login'], role=kw['role'], auth_status=kw['auth_status'],
    )
    client.provision_direct_credentials.side_effect = lambda **kw: SimpleNamespace(
        id=kw['account_id'], login=kw['login'], role=kw['role'], auth_status='active',
    )
    return SimpleNamespace(repo=repo, client=client)


async def synchronize(ctx, **kwargs):
    return await ensure_user_iam_account(
        user_auth_accounts=ctx.repo, user_id='contractor-1', role_id=settings.contractor_role_id,
        user_status=kwargs.pop('user_status', 'active'), iam_client=ctx.client, **kwargs,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize('status,expected', [('active', 'active'), ('review', 'pending'), ('blacklist', 'blocked'), ('inactive', 'blocked')])
async def test_new_identity_and_binding_are_created_without_email_or_password(context, status, expected):
    binding = await synchronize(context, user_status=status)
    context.client.put_account.assert_awaited_once_with(
        account_id=str(stable_iam_account_id('contractor-1')), login='contractor-1', role='contractor', auth_status=expected,
    )
    assert binding.provider == 'iam' and binding.is_active
    assert binding.external_email is None
    context.repo.add.assert_awaited_once_with(binding)
    context.client.provision_direct_credentials.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_inactive_binding_and_account_status_are_preserved(context):
    binding = SimpleNamespace(external_subject_id='existing-subject', is_active=False)
    context.repo.get_by_user_provider.return_value = binding
    context.client.put_account.side_effect = lambda **kw: SimpleNamespace(
        id=kw['account_id'], login=kw['login'], role=kw['role'], auth_status='disabled',
    )
    assert await synchronize(context) is binding
    assert binding.is_active is False
    assert context.client.put_account.await_args.kwargs['auth_status'] == 'blocked'
    context.repo.add.assert_not_awaited()
    context.client.provision_direct_credentials.assert_not_awaited()


@pytest.mark.asyncio
async def test_new_no_mail_creation_can_provision_direct_credentials_once(context):
    await synchronize(context, initial_password='Initial test password 123', is_new_user=True)
    context.client.provision_direct_credentials.assert_awaited_once()
    context.client.put_account.assert_not_awaited()
    context.repo.add.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize('case', ['missing_binding', 'inactive_binding', 'inactive_user', 'no_password'])
async def test_duplicate_creation_cannot_claim_existing_credentials(context, case):
    if case != 'missing_binding':
        context.repo.get_by_user_provider.return_value = SimpleNamespace(external_subject_id='existing', is_active=case != 'inactive_binding')
    context.client.get_credential_state.return_value = SimpleNamespace(login='contractor-1', role='contractor', password_set=False)
    with pytest.raises(Conflict):
        await synchronize(context, initial_password='Initial test password 123', user_status='inactive' if case == 'inactive_user' else 'active')
    context.client.provision_direct_credentials.assert_not_awaited()
    context.repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_foreign_subject_binding_is_rejected_before_iam_write(context):
    context.repo.get_conflicting_subject.return_value = SimpleNamespace(id_user='other')
    with pytest.raises(Conflict):
        await synchronize(context)
    context.client.put_account.assert_not_awaited()
    context.repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_iam_failure_never_creates_local_auth_binding(context):
    context.client.put_account.side_effect = AuthenticationUnavailable()
    with pytest.raises(AuthenticationUnavailable):
        await synchronize(context)
    context.repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_mismatched_iam_response_does_not_bind_another_identity(context):
    context.client.put_account.side_effect = None
    context.client.put_account.return_value = SimpleNamespace(id='wrong', login='another', role='contractor')
    with pytest.raises(Conflict):
        await synchronize(context)
    context.repo.add.assert_not_awaited()

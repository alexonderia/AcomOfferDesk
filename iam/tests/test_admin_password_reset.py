import uuid
from datetime import timedelta

import pytest

from iam_app.core.security import pkce_s256, utc_now, verify_password
from iam_app.errors import Forbidden, InvalidCredentials, Unauthorized
from iam_app.models import AuthSession
from iam_app.repositories import AuditRepository, CredentialRepository
from iam_app.services import IamService


OLD = 'Initial password 123'
NEW = 'Replacement password 456'
REDIRECT = 'http://testserver/api/v1/auth/callback'
VERIFIER = 'v' * 64


async def account(service, session, login, role):
    result = await service.provision_direct_credentials(
        account_id=uuid.uuid4(), login=login, role_name=role, initial_password=OLD,
    )
    auth_session = AuthSession(
        id=uuid.uuid4(), account_id=result.account.id, refresh_token_hash=f'hash-{login}',
        expires_at=utc_now() + timedelta(hours=1),
    )
    session.add(auth_session)
    await session.flush()
    return result.account, auth_session


async def prepare(session, actor_role='superadmin'):
    service = IamService(session)
    await service.seed_rbac({'superadmin': ['users.create'], 'economist': ['requests.view'], 'admin': ['users.create']})
    actor, actor_session = await account(service, session, 'reset.actor', actor_role)
    target, target_session = await account(service, session, 'reset.target', 'economist')
    return service, actor, actor_session, target, target_session


@pytest.mark.asyncio
async def test_reset_replaces_password_revokes_target_sessions_tokens_codes_and_browser_cookie(session):
    service, actor, actor_session, target, target_session = await prepare(session)
    authorization = await service.authenticate_and_create_code(
        login=target.login, password=OLD, state='state', pkce_challenge=pkce_s256(VERIFIER), redirect_uri=REDIRECT,
    )
    bundle = await service.exchange_code(raw_code=authorization.code, code_verifier=VERIFIER, redirect_uri=REDIRECT, ip_address=None, user_agent=None)
    pending = await service.authenticate_and_create_code(
        login=target.login, password=OLD, state='state', pkce_challenge=pkce_s256(VERIFIER), redirect_uri=REDIRECT,
    )
    reset_token, _ = await service.create_action_token(account_id=target.id, purpose='password_reset')
    setup_token, _ = await service.create_action_token(account_id=target.id, purpose='password_setup')
    credential = await CredentialRepository(session).get(target.id)
    credential.failed_login_count = 2
    target.required_actions = ['password_setup', 'complete_profile']
    await service.reset_user_password(account_id=target.id, new_password=NEW, actor_account_id=actor.id, actor_session_id=actor_session.id)
    assert await verify_password(NEW, credential.password_hash)
    assert not await verify_password(OLD, credential.password_hash)
    assert target.required_actions == ['complete_profile']
    assert target.auth_status == 'active'
    assert credential.failed_login_count == 0 and credential.locked_until is None
    assert target_session.revoked_at is not None and actor_session.revoked_at is None
    with pytest.raises(InvalidCredentials):
        await service.authenticate_and_create_code(login=target.login, password=OLD, state='s', pkce_challenge=pkce_s256(VERIFIER), redirect_uri=REDIRECT)
    await service.authenticate_and_create_code(login=target.login, password=NEW, state='s', pkce_challenge=pkce_s256(VERIFIER), redirect_uri=REDIRECT)
    with pytest.raises(Unauthorized):
        await service.refresh(raw_refresh_token=bundle.refresh_token)
    with pytest.raises(Unauthorized):
        await service.exchange_code(raw_code=pending.code, code_verifier=VERIFIER, redirect_uri=REDIRECT, ip_address=None, user_agent=None)
    with pytest.raises(Unauthorized):
        await service.create_code_for_browser_session(account_id=target.id, password_version=authorization.password_version, state='s', pkce_challenge=pkce_s256(VERIFIER), redirect_uri=REDIRECT)
    for token, purpose in [(reset_token, 'password_reset'), (setup_token, 'password_setup')]:
        with pytest.raises(Unauthorized):
            await service.consume_action_token(raw_token=token, purpose=purpose, new_password=OLD)
    events = await AuditRepository(session).list_events()
    event = next(e for e in events if e.event_type == 'password.administratively_reset')
    assert event.account_id == actor.id and event.session_id == actor_session.id
    assert event.details['target_account_id'] == str(target.id)
    assert all(NEW not in str(e.details) and OLD not in str(e.details) for e in events)


@pytest.mark.asyncio
@pytest.mark.parametrize('case', ['admin', 'self', 'other_superadmin', 'revoked', 'expired', 'foreign_session', 'blocked_actor'])
async def test_iam_enforces_superadmin_actor_session_and_protected_targets(session, case):
    service, actor, actor_session, target, target_session = await prepare(session, 'admin' if case == 'admin' else 'superadmin')
    if case == 'self': target = actor
    if case == 'other_superadmin': target, _ = await account(service, session, 'other.root', 'superadmin')
    if case == 'revoked': actor_session.revoked_at = utc_now()
    if case == 'expired': actor_session.expires_at = utc_now() - timedelta(seconds=1)
    if case == 'foreign_session': actor_session = target_session
    if case == 'blocked_actor': actor.auth_status = 'blocked'
    credential = await CredentialRepository(session).get(target.id)
    original_hash = credential.password_hash
    with pytest.raises(Forbidden):
        await service.reset_user_password(account_id=target.id, new_password=NEW, actor_account_id=actor.id, actor_session_id=actor_session.id)
    assert credential.password_hash == original_hash and target_session.revoked_at is None


@pytest.mark.asyncio
@pytest.mark.parametrize('status', ['blocked', 'disabled', 'pending'])
async def test_reset_preserves_nonactive_target_status(session, status):
    service, actor, actor_session, target, _ = await prepare(session)
    target.auth_status = status
    await service.reset_user_password(account_id=target.id, new_password=NEW, actor_account_id=actor.id, actor_session_id=actor_session.id)
    assert target.auth_status == status
    assert await verify_password(NEW, (await CredentialRepository(session).get(target.id)).password_hash)


@pytest.mark.asyncio
async def test_internal_api_requires_service_token_and_redacts_invalid_password(session):
    import httpx
    from iam_app.core.config import settings
    from iam_app.db import get_session
    from iam_app.main import app

    _, actor, actor_session, target, _ = await prepare(session)
    async def db_override():
        yield session
    app.dependency_overrides[get_session] = db_override
    payload = {'new_password': NEW, 'actor_account_id': str(actor.id), 'actor_session_id': str(actor_session.id)}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://testserver') as client:
            path = f'/internal/accounts/{target.id}/password/reset'
            assert (await client.post(path, json=payload)).status_code == 403
            headers = {'X-Acom-Service-Token': settings.internal_service_token}
            response = await client.post(path, headers=headers, json={**payload, 'new_password': 'private'})
            assert response.status_code == 422 and 'private' not in response.text
            response = await client.post(f'/internal/accounts/{actor.id}/password/reset', headers=headers, json=payload)
            assert response.status_code == 403
            response = await client.post(path, headers=headers, json=payload)
            assert response.status_code == 204 and response.content == b''
            assert await verify_password(NEW, (await CredentialRepository(session).get(target.id)).password_hash)
    finally:
        app.dependency_overrides.pop(get_session, None)

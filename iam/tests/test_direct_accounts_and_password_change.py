from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from iam_app.core.security import utc_now, verify_password, pkce_s256
from iam_app.errors import Conflict, CurrentPasswordMismatch, Unauthorized
from iam_app.models import AuthSession
from iam_app.repositories import AuditRepository, CredentialRepository
from iam_app.services import IamService, _safe_details

PASSWORD = 'Initial password 123'
NEW_PASSWORD = 'Replacement password 456'


async def ready_account(session):
    service = IamService(session)
    await service.seed_rbac({'economist': ['requests.view']})
    account_id = uuid.uuid4()
    result = await service.provision_direct_credentials(
        account_id=account_id, login='new.economist', role_name='economist', initial_password=PASSWORD,
    )
    return service, result


async def active_session(session, account_id):
    item = AuthSession(
        id=uuid.uuid4(), account_id=account_id, refresh_token_hash='hashed-secret',
        expires_at=utc_now() + timedelta(hours=1),
    )
    session.add(item)
    await session.flush()
    return item


@pytest.mark.asyncio
async def test_direct_account_is_ready_and_retry_cannot_reset_or_unblock(session):
    service, result = await ready_account(session)
    assert result.account.auth_status == 'active'
    assert result.account.required_actions == []
    credential = await CredentialRepository(session).get(result.account.id)
    original_hash = credential.password_hash
    repeated = await service.provision_direct_credentials(
        account_id=result.account.id, login='new.economist', role_name='economist', initial_password=PASSWORD,
    )
    assert repeated.created is False
    assert credential.password_hash == original_hash
    with pytest.raises(Conflict):
        await service.provision_direct_credentials(
            account_id=result.account.id, login='new.economist', role_name='economist', initial_password=NEW_PASSWORD,
        )
    result.account.auth_status = 'blocked'
    with pytest.raises(Conflict):
        await service.provision_direct_credentials(
            account_id=result.account.id, login='new.economist', role_name='economist', initial_password=PASSWORD,
        )
    assert result.account.auth_status == 'blocked'
    assert credential.password_hash == original_hash


@pytest.mark.asyncio
async def test_direct_creation_cannot_adopt_pending_registration(session):
    service = IamService(session)
    await service.seed_rbac({'economist': ['requests.view']})
    account_id = uuid.uuid4()
    await service.provision_registration_credentials(
        account_id=account_id, login='existing.registration', role_name='economist', initial_password=PASSWORD,
    )
    with pytest.raises(Conflict):
        await service.provision_direct_credentials(
            account_id=account_id, login='existing.registration', role_name='economist', initial_password=PASSWORD,
        )


@pytest.mark.asyncio
async def test_password_change_requires_current_password_and_revokes_sessions_and_reset_tokens(session):
    service, result = await ready_account(session)
    current = await active_session(session, result.account.id)
    other = await active_session(session, result.account.id)
    token, _ = await service.create_action_token(account_id=result.account.id, purpose='password_reset')
    credential = await CredentialRepository(session).get(result.account.id)
    original_hash = credential.password_hash
    with pytest.raises(CurrentPasswordMismatch):
        await service.change_own_password(
            account_id=result.account.id, session_id=current.id,
            current_password='wrong current', new_password=NEW_PASSWORD,
        )
    assert credential.password_hash == original_hash
    assert current.revoked_at is None
    await service.change_own_password(
        account_id=result.account.id, session_id=current.id,
        current_password=PASSWORD, new_password=NEW_PASSWORD,
    )
    assert await verify_password(NEW_PASSWORD, credential.password_hash)
    assert not await verify_password(PASSWORD, credential.password_hash)
    assert current.revoked_at is not None and other.revoked_at is not None
    with pytest.raises(Unauthorized):
        await service.consume_action_token(raw_token=token, purpose='password_reset', new_password=PASSWORD)
    events = await AuditRepository(session).list_events()
    assert any(e.event_type == 'password.changed' for e in events)
    assert all(PASSWORD not in str(e.details) and NEW_PASSWORD not in str(e.details) for e in events)


@pytest.mark.asyncio
async def test_password_change_rejects_foreign_or_revoked_session(session):
    service, result = await ready_account(session)
    current = await active_session(session, result.account.id)
    current.revoked_at = utc_now()
    for session_id in (current.id, uuid.uuid4()):
        with pytest.raises(Unauthorized):
            await service.change_own_password(
                account_id=result.account.id, session_id=session_id,
                current_password=PASSWORD, new_password=NEW_PASSWORD,
            )


def test_password_fields_are_removed_from_audit_details():
    assert _safe_details({'current_password': PASSWORD, 'new_password': NEW_PASSWORD, 'password_confirmation': NEW_PASSWORD, 'reason': 'test'}) == {'reason': 'test'}


@pytest.mark.asyncio
async def test_same_second_password_change_invalidates_old_browser_session(session, monkeypatch):
    now = utc_now().replace(microsecond=100000)
    monkeypatch.setattr('iam_app.services.utc_now', lambda: now)
    service, result = await ready_account(session)
    current = await active_session(session, result.account.id)
    authorization = await service.authenticate_and_create_code(
        login='new.economist', password=PASSWORD, state='state',
        pkce_challenge=pkce_s256('v' * 64), redirect_uri='http://testserver/api/v1/auth/callback',
    )
    now = now.replace(microsecond=900000)
    await service.change_own_password(account_id=result.account.id, session_id=current.id, current_password=PASSWORD, new_password=NEW_PASSWORD)
    with pytest.raises(Unauthorized):
        await service.create_code_for_browser_session(
            account_id=result.account.id, password_version=authorization.password_version,
            state='state', pkce_challenge=pkce_s256('v' * 64), redirect_uri='http://testserver/api/v1/auth/callback',
        )


def test_invalid_credential_payload_does_not_echo_secret():
    from fastapi.testclient import TestClient
    from iam_app.main import app
    from iam_app.core.config import settings

    secret = 'x-private'
    response = TestClient(app).put(f'/internal/accounts/{uuid.uuid4()}/direct-credentials',
        headers={'X-Acom-Service-Token': settings.internal_service_token},
        json={'login': 'new-account', 'role': 'economist', 'password': secret})
    assert response.status_code == 422
    assert secret not in response.text
    assert all('input' not in item for item in response.json()['detail'])

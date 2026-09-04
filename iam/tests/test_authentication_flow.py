from __future__ import annotations

import uuid

import pytest
from jose import jwt

from iam_app.core.config import settings
from iam_app.core.security import pkce_s256
from iam_app.errors import InvalidCredentials, Unauthorized
from iam_app.repositories import AccountRepository, AuditRepository, AuthSessionRepository
from iam_app.services import IamService


ROLE = "economist"
PERMISSIONS = ["offers.view", "requests.view"]
REDIRECT_URI = "http://testserver/api/v1/auth/callback"
VERIFIER = "v" * 64


async def _active_account(service: IamService) -> uuid.UUID:
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: PERMISSIONS})
    await service.create_account(
        account_id=account_id,
        login="economist.one",
        role_name=ROLE,
        auth_status="pending",
    )
    setup_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )
    await service.consume_action_token(
        raw_token=setup_token,
        purpose="password_setup",
        new_password="correct horse battery staple",
    )
    await service.update_status(
        account_id=account_id,
        auth_status="active",
        actor_account_id=None,
        actor_session_id=None,
    )
    return account_id


@pytest.mark.asyncio
async def test_authorization_code_pkce_and_rs256_claims(session) -> None:
    service = IamService(session)
    account_id = await _active_account(service)
    authorization = await service.authenticate_and_create_code(
        login="economist.one",
        password="correct horse battery staple",
        state="expected-state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )

    with pytest.raises(Unauthorized):
        await service.exchange_code(
            raw_code=authorization.code,
            code_verifier="x" * 64,
            redirect_uri=REDIRECT_URI,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    bundle = await service.exchange_code(
        raw_code=authorization.code,
        code_verifier=VERIFIER,
        redirect_uri=REDIRECT_URI,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    claims = jwt.decode(
        bundle.access_token,
        settings.signing_public_key,
        algorithms=["RS256"],
        issuer=settings.issuer,
        audience=settings.audience,
    )
    assert claims["sub"] == str(account_id)
    assert uuid.UUID(claims["sid"])
    assert claims["role"] == ROLE
    assert claims["permissions"] == sorted(PERMISSIONS)
    assert jwt.get_unverified_header(bundle.access_token)["kid"] == settings.signing_kid

    with pytest.raises(Unauthorized):
        await service.exchange_code(
            raw_code=authorization.code,
            code_verifier=VERIFIER,
            redirect_uri=REDIRECT_URI,
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_refresh_rotation_detects_replay_and_revokes_session(session) -> None:
    service = IamService(session)
    await _active_account(service)
    authorization = await service.authenticate_and_create_code(
        login="economist.one",
        password="correct horse battery staple",
        state="state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )
    initial = await service.exchange_code(
        raw_code=authorization.code,
        code_verifier=VERIFIER,
        redirect_uri=REDIRECT_URI,
        ip_address=None,
        user_agent=None,
    )
    rotated = await service.refresh(raw_refresh_token=initial.refresh_token)
    assert rotated.refresh_token != initial.refresh_token

    with pytest.raises(Unauthorized):
        await service.refresh(raw_refresh_token=initial.refresh_token)

    session_id = uuid.UUID(initial.refresh_token.partition(".")[0])
    stored_session = await AuthSessionRepository(session).get(session_id)
    assert stored_session is not None
    assert stored_session.revoked_at is not None
    assert stored_session.revoke_reason == "refresh_reuse"

    with pytest.raises(Unauthorized):
        await service.refresh(raw_refresh_token=rotated.refresh_token)


@pytest.mark.asyncio
async def test_logout_rejects_tampered_refresh_secret_and_revokes_session(session) -> None:
    service = IamService(session)
    await _active_account(service)
    authorization = await service.authenticate_and_create_code(
        login="economist.one",
        password="correct horse battery staple",
        state="state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )
    bundle = await service.exchange_code(
        raw_code=authorization.code,
        code_verifier=VERIFIER,
        redirect_uri=REDIRECT_URI,
        ip_address=None,
        user_agent=None,
    )
    session_id = uuid.UUID(bundle.refresh_token.partition(".")[0])

    with pytest.raises(Unauthorized):
        await service.logout(raw_refresh_token=f"{session_id}.tampered-secret")

    stored_session = await AuthSessionRepository(session).get(session_id)
    assert stored_session is not None
    assert stored_session.revoked_at is not None
    assert stored_session.revoke_reason == "logout_token_mismatch"


@pytest.mark.asyncio
async def test_account_reconciliation_reports_orphan_and_missing_ids(session) -> None:
    service = IamService(session)
    known_account_id = await _active_account(service)
    orphan_account_id = uuid.uuid4()
    missing_account_id = uuid.uuid4()
    await service.create_account(
        account_id=orphan_account_id,
        login="orphan.account",
        role_name=ROLE,
        auth_status="pending",
    )

    orphan_ids, missing_ids = await service.reconcile_account_ids(
        {known_account_id, missing_account_id}
    )

    assert orphan_ids == [orphan_account_id]
    assert missing_ids == [missing_account_id]


@pytest.mark.asyncio
async def test_local_development_provisioning_sets_login_password_idempotently(
    session,
    monkeypatch,
) -> None:
    from iam_app.core.config import settings
    from iam_app.core.security import verify_password
    from iam_app.errors import Forbidden
    from iam_app.repositories import AccountRepository, CredentialRepository

    monkeypatch.setattr(settings, "app_env", "development")
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: PERMISSIONS})

    first = await service.provision_local_development_account(
        account_id=account_id,
        login="superadmin",
        role_name=ROLE,
    )
    credential = await CredentialRepository(session).get(account_id)
    assert first.created is True
    assert first.account.auth_status == "active"
    assert credential is not None
    assert credential.password_algo == "argon2id"
    assert credential.password_hash is not None
    assert await verify_password("superadmin", credential.password_hash)
    original_hash = credential.password_hash

    second = await service.provision_local_development_account(
        account_id=account_id,
        login="superadmin",
        role_name=ROLE,
    )
    stored = await AccountRepository(session).get(account_id)
    credential = await CredentialRepository(session).get(account_id)
    assert second.created is False
    assert stored is not None and stored.auth_status == "active"
    assert credential is not None and credential.password_hash == original_hash

    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(Forbidden):
        await service.provision_local_development_account(
            account_id=account_id,
            login="superadmin",
            role_name=ROLE,
        )


@pytest.mark.asyncio
async def test_password_setup_token_is_single_use_and_password_is_argon2id(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: PERMISSIONS})
    await service.create_account(
        account_id=account_id,
        login="pending.user",
        role_name=ROLE,
        auth_status="pending",
    )
    raw_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )
    await service.consume_action_token(
        raw_token=raw_token,
        purpose="password_setup",
        new_password="a sufficiently long password",
    )

    from iam_app.repositories import AccountRepository, CredentialRepository

    account = await AccountRepository(session).get(account_id)
    credential = await CredentialRepository(session).get(account_id)
    assert account is not None and account.auth_status == "pending"
    assert credential is not None
    assert credential.password_algo == "argon2id"
    assert credential.password_hash is not None and credential.password_hash.startswith("$argon2")
    assert (await service.get_credential_state(account_id=account_id)).required_actions == ()
    setup_events = [
        event
        for event in await AuditRepository(session).list_events()
        if event.event_type == "password.setup_completed"
    ]
    assert len(setup_events) == 1
    assert setup_events[0].session_id is None
    assert setup_events[0].details == {"auth_status": "pending"}

    with pytest.raises(Unauthorized):
        await service.consume_action_token(
            raw_token=raw_token,
            purpose="password_setup",
            new_password="another sufficiently long password",
        )


@pytest.mark.asyncio
async def test_new_action_token_invalidates_previous_unconsumed_token(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: PERMISSIONS})
    await service.create_account(
        account_id=account_id,
        login="retry.user",
        role_name=ROLE,
        auth_status="pending",
    )
    previous, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )
    current, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )

    with pytest.raises(Unauthorized):
        await service.consume_action_token(
            raw_token=previous,
            purpose="password_setup",
            new_password="a sufficiently long password",
        )
    await service.consume_action_token(
        raw_token=current,
        purpose="password_setup",
        new_password="a sufficiently long password",
    )


@pytest.mark.asyncio
async def test_password_reset_changes_password_and_revokes_existing_sessions(session) -> None:
    service = IamService(session)
    account_id = await _active_account(service)
    authorization = await service.authenticate_and_create_code(
        login="economist.one",
        password="correct horse battery staple",
        state="state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )
    bundle = await service.exchange_code(
        raw_code=authorization.code,
        code_verifier=VERIFIER,
        redirect_uri=REDIRECT_URI,
        ip_address=None,
        user_agent=None,
    )
    reset_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_reset",
    )
    await service.consume_action_token(
        raw_token=reset_token,
        purpose="password_reset",
        new_password="a completely different password",
    )

    account = await AccountRepository(session).get(account_id)
    assert account is not None and account.auth_status == "active"
    assert (await service.get_credential_state(account_id=account_id)).required_actions == ()
    reset_events = [
        event
        for event in await AuditRepository(session).list_events()
        if event.event_type == "password.reset_completed"
    ]
    assert len(reset_events) == 1
    assert reset_events[0].session_id is None
    assert reset_events[0].details == {"auth_status": "active"}
    with pytest.raises(Unauthorized):
        await service.refresh(raw_refresh_token=bundle.refresh_token)
    with pytest.raises(InvalidCredentials):
        await service.authenticate_and_create_code(
            login="economist.one",
            password="correct horse battery staple",
            state="state",
            pkce_challenge=pkce_s256(VERIFIER),
            redirect_uri=REDIRECT_URI,
        )
    await service.authenticate_and_create_code(
        login="economist.one",
        password="a completely different password",
        state="state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )


@pytest.mark.asyncio
async def test_role_change_is_reflected_on_refresh_and_block_revokes_session(session) -> None:
    service = IamService(session)
    account_id = await _active_account(service)
    await service.seed_rbac(
        {
            ROLE: PERMISSIONS,
            "admin": ["users.read", "users.status.update"],
        }
    )
    authorization = await service.authenticate_and_create_code(
        login="economist.one",
        password="correct horse battery staple",
        state="state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )
    bundle = await service.exchange_code(
        raw_code=authorization.code,
        code_verifier=VERIFIER,
        redirect_uri=REDIRECT_URI,
        ip_address=None,
        user_agent=None,
    )
    await service.update_role(
        account_id=account_id,
        role_name="admin",
        actor_account_id=None,
        actor_session_id=None,
    )
    refreshed = await service.refresh(raw_refresh_token=bundle.refresh_token)
    claims = jwt.decode(
        refreshed.access_token,
        settings.signing_public_key,
        algorithms=["RS256"],
        issuer=settings.issuer,
        audience=settings.audience,
    )
    assert claims["role"] == "admin"
    assert claims["permissions"] == ["users.read", "users.status.update"]

    await service.update_status(
        account_id=account_id,
        auth_status="blocked",
        actor_account_id=None,
        actor_session_id=None,
    )
    with pytest.raises(Unauthorized):
        await service.refresh(raw_refresh_token=refreshed.refresh_token)


@pytest.mark.asyncio
async def test_repeated_invalid_password_locks_account_without_revealing_login(session) -> None:
    service = IamService(session)
    await _active_account(service)

    for _ in range(settings.login_max_failures):
        with pytest.raises(InvalidCredentials):
            await service.authenticate_and_create_code(
                login="economist.one",
                password="wrong password",
                state="state",
                pkce_challenge=pkce_s256(VERIFIER),
                redirect_uri=REDIRECT_URI,
            )

    with pytest.raises(InvalidCredentials) as existing_error:
        await service.authenticate_and_create_code(
            login="economist.one",
            password="correct horse battery staple",
            state="state",
            pkce_challenge=pkce_s256(VERIFIER),
            redirect_uri=REDIRECT_URI,
        )
    with pytest.raises(InvalidCredentials) as missing_error:
        await service.authenticate_and_create_code(
            login="missing.user",
            password="correct horse battery staple",
            state="state",
            pkce_challenge=pkce_s256(VERIFIER),
            redirect_uri=REDIRECT_URI,
        )
    assert existing_error.value.public_detail == missing_error.value.public_detail

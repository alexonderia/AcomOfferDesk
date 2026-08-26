from __future__ import annotations

import logging
import uuid
from datetime import timedelta

import pytest

from iam_app.core.security import hash_secret, pkce_s256, utc_now, verify_password
from iam_app.errors import Conflict, InvalidCredentials, Unauthorized
from iam_app.repositories import (
    AccountRepository,
    ActionTokenRepository,
    AuditRepository,
    CredentialRepository,
)
from iam_app.services import IamService


ROLE = "economist"
PASSWORD = "registration password 123"
REDIRECT_URI = "http://testserver/api/v1/auth/callback"
VERIFIER = "v" * 64


@pytest.mark.asyncio
async def test_registration_credentials_are_strictly_idempotent_and_audited(
    session,
    caplog,
) -> None:
    caplog.set_level(logging.WARNING, logger="iam_app.services")
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac(
        {
            ROLE: ["requests.view"],
            "admin": ["users.view"],
        }
    )

    first = await service.provision_registration_credentials(
        account_id=account_id,
        login="pending.registration",
        role_name=ROLE,
        initial_password=PASSWORD,
    )
    credential = await CredentialRepository(session).get(account_id)
    assert first.created is True
    assert first.password_set is True
    assert first.account.auth_status == "pending"
    assert credential is not None
    assert credential.password_hash is not None
    assert credential.password_hash.startswith("$argon2")
    assert credential.password_hash != PASSWORD
    assert await verify_password(PASSWORD, credential.password_hash)
    original_hash = credential.password_hash

    credential.failed_login_count = 3
    credential.locked_until = utc_now() + timedelta(minutes=5)
    await session.flush()
    repeated = await service.provision_registration_credentials(
        account_id=account_id,
        login="pending.registration",
        role_name=ROLE,
        initial_password=PASSWORD,
        auth_status="pending",
    )
    assert repeated.created is False
    assert credential.password_hash == original_hash
    assert credential.failed_login_count == 0
    assert credential.locked_until is None

    state = await service.get_credential_state(account_id=account_id)
    assert state.account.id == account_id
    assert state.account.auth_status == "pending"
    assert state.role_name == ROLE
    assert state.password_set is True

    with pytest.raises(InvalidCredentials) as unavailable_error:
        await service.authenticate_and_create_code(
            login="pending.registration",
            password=PASSWORD,
            state="state",
            pkce_challenge=pkce_s256(VERIFIER),
            redirect_uri=REDIRECT_URI,
        )
    assert "Доступ ограничен" in unavailable_error.value.public_detail

    for changed in (
        {"initial_password": "different registration password"},
        {"login": "different.login"},
        {"role_name": "admin"},
    ):
        arguments = {
            "account_id": account_id,
            "login": "pending.registration",
            "role_name": ROLE,
            "initial_password": PASSWORD,
        }
        arguments.update(changed)
        with pytest.raises(Conflict):
            await service.provision_registration_credentials(**arguments)

    await service.update_status(
        account_id=account_id,
        auth_status="active",
        actor_account_id=None,
        actor_session_id=None,
    )
    with pytest.raises(Conflict):
        await service.provision_registration_credentials(
            account_id=account_id,
            login="pending.registration",
            role_name=ROLE,
            initial_password=PASSWORD,
        )

    audit_events = [
        event
        for event in await AuditRepository(session).list_events()
        if event.event_type == "password.initial_provisioned"
    ]
    assert len(audit_events) == 1
    assert audit_events[0].account_id == account_id
    assert audit_events[0].session_id is None
    assert audit_events[0].details == {
        "auth_status": "pending",
        "created_account": True,
        "repaired_credential": False,
    }
    assert PASSWORD not in caplog.text
    assert original_hash not in caplog.text


@pytest.mark.asyncio
async def test_pending_registration_password_can_be_replaced(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.provision_registration_credentials(
        account_id=account_id,
        login="pending.replace",
        role_name=ROLE,
        initial_password=PASSWORD,
    )
    replaced = await service.provision_registration_credentials(
        account_id=account_id,
        login="pending.replace",
        role_name=ROLE,
        initial_password="replacement password 123",
        replace_password=True,
    )
    credential = await CredentialRepository(session).get(account_id)
    assert replaced.created is False
    assert credential is not None
    assert await verify_password("replacement password 123", credential.password_hash)


@pytest.mark.asyncio
async def test_registration_credentials_repair_missing_credential_row(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.create_account(
        account_id=account_id,
        login="repair.registration",
        role_name=ROLE,
        auth_status="pending",
    )
    credential = await CredentialRepository(session).get(account_id)
    assert credential is not None
    await session.delete(credential)
    await session.flush()

    result = await service.provision_registration_credentials(
        account_id=account_id,
        login="repair.registration",
        role_name=ROLE,
        initial_password=PASSWORD,
    )

    repaired = await CredentialRepository(session).get(account_id)
    assert result.created is False
    assert repaired is not None and repaired.password_hash is not None
    assert await verify_password(PASSWORD, repaired.password_hash)
    event = [
        item
        for item in await AuditRepository(session).list_events()
        if item.event_type == "password.initial_provisioned"
    ][0]
    assert event.details["repaired_credential"] is True


@pytest.mark.asyncio
async def test_active_passwordless_setup_preserves_status_and_writes_audit(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.create_account(
        account_id=account_id,
        login="manual.first.access",
        role_name=ROLE,
        auth_status="active",
    )

    state = await service.get_credential_state(account_id=account_id)
    assert state.password_set is False
    with pytest.raises(InvalidCredentials):
        await service.authenticate_and_create_code(
            login="manual.first.access",
            password=PASSWORD,
            state="state",
            pkce_challenge=pkce_s256(VERIFIER),
            redirect_uri=REDIRECT_URI,
        )

    credential = await CredentialRepository(session).get(account_id)
    assert credential is not None
    credential.failed_login_count = 2
    credential.locked_until = utc_now() + timedelta(minutes=5)
    token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )
    await service.consume_action_token(
        raw_token=token,
        purpose="password_setup",
        new_password=PASSWORD,
    )

    account = await AccountRepository(session).get(account_id)
    assert account is not None and account.auth_status == "active"
    assert credential.failed_login_count == 0
    assert credential.locked_until is None
    assert (await service.get_credential_state(account_id=account_id)).password_set is True
    assert (await service.get_credential_state(account_id=account_id)).required_actions == (
        "complete_profile",
    )
    await service.authenticate_and_create_code(
        login="manual.first.access",
        password=PASSWORD,
        state="state",
        pkce_challenge=pkce_s256(VERIFIER),
        redirect_uri=REDIRECT_URI,
    )
    event = [
        item
        for item in await AuditRepository(session).list_events()
        if item.event_type == "password.setup_completed"
    ][0]
    assert event.account_id == account_id
    assert event.session_id is None
    assert event.details == {"auth_status": "active"}


@pytest.mark.asyncio
@pytest.mark.parametrize("auth_status", ["blocked", "disabled"])
async def test_password_actions_reject_unavailable_accounts_without_consuming_token(
    session,
    auth_status: str,
) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.create_account(
        account_id=account_id,
        login=f"{auth_status}.account",
        role_name=ROLE,
        auth_status=auth_status,
    )
    raw_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )

    with pytest.raises(Unauthorized):
        await service.consume_action_token(
            raw_token=raw_token,
            purpose="password_setup",
            new_password=PASSWORD,
        )

    token = await ActionTokenRepository(session).get_by_hash(hash_secret(raw_token))
    account = await AccountRepository(session).get(account_id)
    assert token is not None and token.consumed_at is None
    assert account is not None and account.auth_status == auth_status


@pytest.mark.asyncio
async def test_verify_email_action_is_one_time_and_does_not_change_status(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.provision_registration_credentials(
        account_id=account_id,
        login="verify.pending",
        role_name=ROLE,
        auth_status="pending",
        initial_password=PASSWORD,
    )
    raw_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="verify_email",
        context={"email": "verify.pending@example.com"},
    )

    result = await service.consume_action_token(raw_token=raw_token, purpose="verify_email")
    account = await AccountRepository(session).get(account_id)

    assert result.context == {"email": "verify.pending@example.com"}
    assert result.auth_status == "pending"
    assert account is not None and account.auth_status == "pending"
    with pytest.raises(Unauthorized):
        await service.consume_action_token(raw_token=raw_token, purpose="verify_email")


@pytest.mark.asyncio
async def test_complete_profile_required_action_can_be_completed_without_raw_token(
    session,
) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.create_account(
        account_id=account_id,
        login="complete.profile.user",
        role_name=ROLE,
        auth_status="active",
    )
    setup_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )
    await service.consume_action_token(
        raw_token=setup_token,
        purpose="password_setup",
        new_password=PASSWORD,
    )
    account = await AccountRepository(session).get(account_id)
    assert account is not None
    assert account.auth_status == "active"
    assert account.required_actions == ["complete_profile"]
    assert (await service.get_credential_state(account_id=account_id)).required_actions == (
        "complete_profile",
    )
    leftover_tokens = await ActionTokenRepository(session).list_active_purposes(
        account_id=account_id,
        now=utc_now() + timedelta(days=400),
    )
    assert "complete_profile" not in leftover_tokens

    await service.complete_required_action(account_id=account_id, purpose="complete_profile")
    assert (await service.get_credential_state(account_id=account_id)).required_actions == ()
    await service.complete_required_action(account_id=account_id, purpose="complete_profile")
    assert (await service.get_credential_state(account_id=account_id)).required_actions == ()


@pytest.mark.asyncio
async def test_complete_profile_survives_action_token_ttl_window(session, monkeypatch) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.create_account(
        account_id=account_id,
        login="durable.profile.user",
        role_name=ROLE,
        auth_status="active",
    )
    setup_token, _ = await service.create_action_token(
        account_id=account_id,
        purpose="password_setup",
    )
    await service.consume_action_token(
        raw_token=setup_token,
        purpose="password_setup",
        new_password=PASSWORD,
    )

    later = utc_now() + timedelta(days=40)

    def _later():
        return later

    monkeypatch.setattr("iam_app.services.utc_now", _later)
    assert (await service.get_credential_state(account_id=account_id)).required_actions == (
        "complete_profile",
    )
    account = await AccountRepository(session).get(account_id)
    assert account is not None and account.required_actions == ["complete_profile"]


@pytest.mark.asyncio
async def test_complete_profile_cannot_be_issued_as_action_token(session) -> None:
    service = IamService(session)
    account_id = uuid.uuid4()
    await service.seed_rbac({ROLE: ["requests.view"]})
    await service.create_account(
        account_id=account_id,
        login="no.token.profile",
        role_name=ROLE,
        auth_status="active",
    )
    with pytest.raises(Conflict):
        await service.create_action_token(account_id=account_id, purpose="complete_profile")



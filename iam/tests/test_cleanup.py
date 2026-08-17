from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from iam_app.maintenance.cleanup import CleanupCounts, cleanup_transient_data
from iam_app.models import (
    Account,
    AuthActionToken,
    AuthAuditLog,
    AuthSession,
    AuthorizationCode,
    Role,
)


NOW = datetime(2026, 8, 17, 8, 0, tzinfo=UTC)


async def _seed_account(session) -> uuid.UUID:
    account_id = uuid.uuid4()
    session.add(Role(id=1, name="economist", is_active=True))
    session.add(
        Account(
            id=account_id,
            login=f"user-{account_id}",
            role_id=1,
            auth_status="active",
        )
    )
    await session.flush()
    return account_id


def _auth_session(
    account_id: uuid.UUID,
    *,
    expires_at: datetime,
    revoked_at: datetime | None = None,
) -> AuthSession:
    return AuthSession(
        id=uuid.uuid4(),
        account_id=account_id,
        refresh_token_hash=uuid.uuid4().hex,
        created_at=NOW - timedelta(days=3),
        last_used_at=NOW - timedelta(days=2),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


async def _table_count(session, model) -> int:
    return int((await session.execute(select(func.count()).select_from(model))).scalar_one())


@pytest.mark.asyncio
async def test_cleanup_dry_run_counts_without_deleting(session) -> None:
    account_id = await _seed_account(session)
    expired_session = _auth_session(
        account_id,
        expires_at=NOW - timedelta(minutes=1),
    )
    session.add_all(
        [
            AuthorizationCode(
                id=uuid.uuid4(),
                account_id=account_id,
                code_hash="expired-code",
                pkce_challenge="challenge",
                pkce_method="S256",
                redirect_uri="http://testserver/callback",
                expires_at=NOW - timedelta(minutes=1),
            ),
            AuthActionToken(
                id=uuid.uuid4(),
                account_id=account_id,
                purpose="password_reset",
                token_hash="expired-action",
                expires_at=NOW - timedelta(minutes=1),
            ),
            expired_session,
        ]
    )
    await session.commit()

    counts = await cleanup_transient_data(
        session,
        now=NOW,
        retention=timedelta(hours=24),
        dry_run=True,
    )

    assert counts == CleanupCounts(1, 1, 1)
    assert await _table_count(session, AuthorizationCode) == 1
    assert await _table_count(session, AuthActionToken) == 1
    assert await _table_count(session, AuthSession) == 1


@pytest.mark.asyncio
async def test_cleanup_is_batched_idempotent_and_preserves_active_rows(session) -> None:
    account_id = await _seed_account(session)
    active_session = _auth_session(
        account_id,
        expires_at=NOW + timedelta(hours=1),
    )
    expired_session = _auth_session(
        account_id,
        expires_at=NOW - timedelta(minutes=1),
    )
    revoked_session = _auth_session(
        account_id,
        expires_at=NOW + timedelta(days=1),
        revoked_at=NOW - timedelta(days=2),
    )
    session.add_all(
        [
            AuthorizationCode(
                id=uuid.uuid4(),
                account_id=account_id,
                code_hash="expired-code",
                pkce_challenge="challenge",
                pkce_method="S256",
                redirect_uri="http://testserver/callback",
                expires_at=NOW - timedelta(minutes=1),
            ),
            AuthorizationCode(
                id=uuid.uuid4(),
                account_id=account_id,
                code_hash="active-code",
                pkce_challenge="challenge",
                pkce_method="S256",
                redirect_uri="http://testserver/callback",
                expires_at=NOW + timedelta(minutes=5),
            ),
            AuthActionToken(
                id=uuid.uuid4(),
                account_id=account_id,
                purpose="password_reset",
                token_hash="old-consumed-action",
                expires_at=NOW + timedelta(days=1),
                consumed_at=NOW - timedelta(days=2),
            ),
            AuthActionToken(
                id=uuid.uuid4(),
                account_id=account_id,
                purpose="password_reset",
                token_hash="active-action",
                expires_at=NOW + timedelta(hours=1),
            ),
            active_session,
            expired_session,
            revoked_session,
        ]
    )
    await session.commit()

    totals = CleanupCounts()
    while True:
        batch = await cleanup_transient_data(
            session,
            now=NOW,
            retention=timedelta(hours=24),
            batch_size=1,
        )
        await session.commit()
        totals += batch
        if batch.total == 0:
            break

    assert totals == CleanupCounts(1, 1, 2)
    assert await _table_count(session, AuthorizationCode) == 1
    assert await _table_count(session, AuthActionToken) == 1
    assert await _table_count(session, AuthSession) == 1
    assert await session.get(AuthSession, active_session.id) is not None

    repeated = await cleanup_transient_data(session, now=NOW)
    assert repeated == CleanupCounts()


@pytest.mark.asyncio
async def test_cleanup_does_not_delete_session_referenced_by_audit(session) -> None:
    account_id = await _seed_account(session)
    audited_session = _auth_session(
        account_id,
        expires_at=NOW - timedelta(days=2),
    )
    session.add(audited_session)
    await session.flush()
    session.add(
        AuthAuditLog(
            id=uuid.uuid4(),
            account_id=account_id,
            session_id=audited_session.id,
            event_type="login.success",
            success=True,
            details={},
        )
    )
    await session.commit()

    counts = await cleanup_transient_data(session, now=NOW)
    await session.commit()

    assert counts.auth_sessions == 0
    assert await session.get(AuthSession, audited_session.id) is not None
    assert await _table_count(session, AuthAuditLog) == 1

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam_app.db import SessionLocal
from iam_app.models import AuthActionToken, AuthSession, AuthorizationCode


@dataclass(frozen=True, slots=True)
class CleanupCounts:
    authorization_codes: int = 0
    auth_action_tokens: int = 0
    auth_sessions: int = 0

    def __add__(self, other: "CleanupCounts") -> "CleanupCounts":
        return CleanupCounts(
            authorization_codes=self.authorization_codes + other.authorization_codes,
            auth_action_tokens=self.auth_action_tokens + other.auth_action_tokens,
            auth_sessions=self.auth_sessions + other.auth_sessions,
        )

    @property
    def total(self) -> int:
        return self.authorization_codes + self.auth_action_tokens + self.auth_sessions


async def _count(session: AsyncSession, model, condition) -> int:
    stmt = select(func.count()).select_from(model).where(condition)
    return int((await session.execute(stmt)).scalar_one())


async def _delete_batch(
    session: AsyncSession,
    model,
    condition,
    *,
    batch_size: int,
) -> int:
    ids = list(
        (
            await session.execute(
                select(model.id).where(condition).order_by(model.id).limit(batch_size)
            )
        )
        .scalars()
        .all()
    )
    if not ids:
        return 0
    deleted_ids = list(
        (
            await session.execute(
                delete(model).where(model.id.in_(ids)).returning(model.id)
            )
        )
        .scalars()
        .all()
    )
    return len(deleted_ids)


async def cleanup_transient_data(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    retention: timedelta = timedelta(hours=24),
    batch_size: int = 500,
    dry_run: bool = False,
) -> CleanupCounts:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    if retention < timedelta(0):
        raise ValueError("retention must not be negative")

    effective_now = now or datetime.now(UTC)
    retention_cutoff = effective_now - retention
    code_condition = or_(
        AuthorizationCode.expires_at <= effective_now,
        AuthorizationCode.consumed_at <= retention_cutoff,
    )
    action_condition = or_(
        AuthActionToken.expires_at <= effective_now,
        AuthActionToken.consumed_at <= retention_cutoff,
    )
    session_condition = or_(
        AuthSession.expires_at <= effective_now,
        AuthSession.revoked_at <= retention_cutoff,
    )

    if dry_run:
        return CleanupCounts(
            authorization_codes=await _count(session, AuthorizationCode, code_condition),
            auth_action_tokens=await _count(session, AuthActionToken, action_condition),
            auth_sessions=await _count(session, AuthSession, session_condition),
        )

    return CleanupCounts(
        authorization_codes=await _delete_batch(
            session,
            AuthorizationCode,
            code_condition,
            batch_size=batch_size,
        ),
        auth_action_tokens=await _delete_batch(
            session,
            AuthActionToken,
            action_condition,
            batch_size=batch_size,
        ),
        auth_sessions=await _delete_batch(
            session,
            AuthSession,
            session_condition,
            batch_size=batch_size,
        ),
    )


async def run_cleanup(
    *,
    retention: timedelta,
    batch_size: int,
    dry_run: bool,
) -> CleanupCounts:
    totals = CleanupCounts()
    async with SessionLocal() as session:
        if dry_run:
            return await cleanup_transient_data(
                session,
                retention=retention,
                batch_size=batch_size,
                dry_run=True,
            )
        while True:
            batch = await cleanup_transient_data(
                session,
                retention=retention,
                batch_size=batch_size,
            )
            await session.commit()
            totals += batch
            if batch.total == 0:
                return totals


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Delete expired IAM transient data")
    parser.add_argument("--retention-hours", type=float, default=24.0)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.retention_hours < 0:
        raise SystemExit("--retention-hours must not be negative")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be greater than zero")
    counts = asyncio.run(
        run_cleanup(
            retention=timedelta(hours=args.retention_hours),
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    )
    print(
        json.dumps(
            {
                **asdict(counts),
                "dry_run": args.dry_run,
                "total": counts.total,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

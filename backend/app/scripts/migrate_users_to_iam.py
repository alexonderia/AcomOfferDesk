from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass

from app.core.uow import UnitOfWork
from app.domain.contractor_validation import validate_optional_email
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount
from app.scripts.seed_iam_rbac import build_rbac_matrix
from app.services.iam_password_actions import send_iam_password_action_email


@dataclass(frozen=True, slots=True)
class MigrationCandidate:
    user_id: str
    role_id: int
    status: str
    email: str | None


def _delivery_email(value: str | None) -> str | None:
    try:
        return validate_optional_email((value or "").strip(), allow_placeholder=False)
    except ValueError:
        return None


async def find_candidates() -> list[MigrationCandidate]:
    async with UnitOfWork() as uow:
        rows = await uow.users.list_all_with_profiles()
        bindings = await uow.user_auth_accounts.list_for_provider(provider="iam")
        bound_user_ids = {binding.id_user for binding in bindings if binding.is_active}
        return [
            MigrationCandidate(
                user_id=user.id,
                role_id=user.id_role,
                status=user.status,
                email=_delivery_email(profile.mail if profile else None),
            )
            for user, profile in rows
            if user.id not in bound_user_ids
        ]


async def migrate_candidate(candidate: MigrationCandidate, *, client: IamClient) -> bool:
    role_name = technical_role_name(candidate.role_id)
    if role_name is None or candidate.email is None:
        return False
    account_id = stable_iam_account_id(candidate.user_id)
    async with UnitOfWork() as uow:
        existing = await uow.user_auth_accounts.get_by_user_provider(
            user_id=candidate.user_id,
            provider="iam",
            include_inactive=True,
        )
        if existing is not None and existing.is_active:
            return True
        account_id = existing.external_subject_id if existing is not None else account_id
        account = await client.put_account(
            account_id=account_id,
            login=candidate.user_id,
            role=role_name,
            auth_status="pending",
        )
        if existing is None:
            await uow.user_auth_accounts.add(
                UserAuthAccount(
                    id_user=candidate.user_id,
                    provider="iam",
                    external_subject_id=account.id,
                    external_username=candidate.user_id,
                    external_email=candidate.email,
                    is_active=True,
                )
            )
        else:
            existing.is_active = True
            existing.external_username = candidate.user_id
            existing.external_email = candidate.email
        if account.auth_status == "pending":
            action = await client.create_action_token(
                account_id=account.id,
                purpose="password_setup",
            )
            await send_iam_password_action_email(
                to_email=candidate.email,
                raw_token=action.token,
                purpose="password_setup",
            )
    return True


async def run(*, apply: bool) -> int:
    candidates = await find_candidates()
    print(f"IAM migration candidates: {len(candidates)}")
    for index, candidate in enumerate(candidates, start=1):
        role_name = technical_role_name(candidate.role_id) or "unsupported"
        delivery = "email" if candidate.email else "blocked-missing-valid-email"
        print(f"- candidate={index} role={role_name} setup={delivery}")
    if not apply:
        print("Dry run complete; no data changed.")
        return 0

    client = IamClient()
    await client.seed_rbac(build_rbac_matrix())
    migrated = 0
    skipped = 0
    for candidate in candidates:
        if await migrate_candidate(candidate, client=client):
            migrated += 1
        else:
            skipped += 1
    print(f"Applied: migrated={migrated} skipped={skipped}")
    return 0 if skipped == 0 else 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate Acom users to IAM password-setup accounts")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(apply=args.apply)))


if __name__ == "__main__":
    main()

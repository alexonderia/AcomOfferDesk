"""Synchronize one explicitly named Acom user and IAM account without changing credentials."""
from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.uow import UnitOfWork
from app.domain.exceptions import Conflict, DomainError, NotFound
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.services.iam_bindings import ensure_user_iam_account, sync_existing_iam_binding


async def run(
    *, user_id: str, apply: bool, from_iam: bool = False, iam_account_id: UUID | None = None,
) -> dict:
    client = IamClient()
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(user_id, for_update=from_iam and apply)
        if user is None:
            raise NotFound("Пользователь не найден")
        if from_iam:
            result = await sync_existing_iam_binding(
                user_auth_accounts=uow.user_auth_accounts, user_id=user.id, role_id=user.id_role,
                iam_client=client, apply=apply, iam_account_id=iam_account_id,
            )
            return {
                "user_id": user.id, "business_status": user.status, "applied": apply,
                **asdict(result),
            }

        binding = await uow.user_auth_accounts.get_by_user_provider(
            user_id=user.id, provider="iam", include_inactive=True,
        )
        subject = str(binding.external_subject_id if binding else stable_iam_account_id(user.id))
        try:
            before = await client.get_credential_state(account_id=subject)
        except NotFound:
            before = None
        if before and (before.login != user.id or before.role != technical_role_name(user.id_role)):
            raise Conflict("Учётная запись IAM не соответствует пользователю")
        report = {"user_id": user.id, "business_status": user.status,
            "iam_account_existed": before is not None, "binding_existed": binding is not None, "applied": apply}
        if apply:
            await ensure_user_iam_account(
                user_auth_accounts=uow.user_auth_accounts, user_id=user.id,
                role_id=user.id_role, user_status=user.status, iam_client=client,
            )
            after = await client.get_credential_state(account_id=subject)
            if before is not None and (after.auth_status != before.auth_status
                or after.password_set != before.password_set or after.required_actions != before.required_actions):
                raise Conflict("Синхронизация неожиданно изменила состояние учётной записи")
            report.update(iam_status=after.auth_status, password_set=after.password_set)
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", required=True, help="Exact Acom user login")
    parser.add_argument("--from-iam", action="store_true", help="Restore only the local binding using an existing IAM account")
    parser.add_argument("--iam-account-id", type=UUID, help="Exact existing IAM UUID, for use with --from-iam")
    parser.add_argument("--apply", action="store_true", help="Apply the planned change; default is read-only")
    args = parser.parse_args()
    if args.iam_account_id is not None and not args.from_iam:
        parser.error("--iam-account-id requires --from-iam")
    try:
        result = asyncio.run(run(
            user_id=args.user, apply=args.apply, from_iam=args.from_iam, iam_account_id=args.iam_account_id,
        ))
    except DomainError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2) from None
    except IntegrityError:
        print(json.dumps({"error": "База не сохранила привязку. Проверьте её текущее состояние перед повтором."}, ensure_ascii=False))
        raise SystemExit(2) from None
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

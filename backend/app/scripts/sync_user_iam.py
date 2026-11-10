"""Synchronize one explicitly named Acom user to IAM without changing credentials."""
from __future__ import annotations

import argparse
import asyncio
import json

from app.core.uow import UnitOfWork
from app.domain.exceptions import Conflict, NotFound
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.services.iam_bindings import ensure_user_iam_account


async def run(*, user_id: str, apply: bool) -> dict:
    client = IamClient()
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(user_id)
        if user is None:
            raise NotFound("Пользователь не найден")
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
    parser.add_argument("--apply", action="store_true", help="Create missing IAM account/binding; default is read-only")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(user_id=args.user, apply=args.apply)), ensure_ascii=False))


if __name__ == "__main__":
    main()

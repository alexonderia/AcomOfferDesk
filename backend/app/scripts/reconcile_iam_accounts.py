from __future__ import annotations

import argparse
import asyncio
import json

from app.core.uow import UnitOfWork
from app.infrastructure.iam_client import IamClient


async def run(*, strict: bool) -> int:
    async with UnitOfWork() as uow:
        bindings = await uow.user_auth_accounts.list_for_provider(provider="iam")
    known_account_ids = [binding.external_subject_id for binding in bindings]
    inactive_binding_ids = sorted(
        binding.external_subject_id for binding in bindings if not binding.is_active
    )
    orphan_ids, missing_ids = await IamClient().reconcile_account_ids(known_account_ids)
    report = {
        "active_or_inactive_iam_bindings": len(bindings),
        "inactive_iam_binding_account_ids": inactive_binding_ids,
        "orphan_iam_account_ids": sorted(orphan_ids),
        "missing_iam_account_ids": sorted(missing_ids),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    has_drift = bool(orphan_ids or missing_ids or inactive_binding_ids)
    return 2 if strict and has_drift else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only reconciliation of Acom IAM bindings and IAM accounts"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 2 when orphan or missing accounts are found",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(strict=args.strict)))


if __name__ == "__main__":
    main()

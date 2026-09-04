from __future__ import annotations

import argparse
import asyncio
import json

from app.domain.iam_roles import ROLE_TECHNICAL_NAME_BY_ID
from app.domain.permissions import get_role_permissions_map
from app.infrastructure.iam_client import IamClient


def build_rbac_matrix() -> dict[str, list[str]]:
    role_permissions = get_role_permissions_map()
    return {
        role_name: sorted(role_permissions[role_id])
        for role_id, role_name in ROLE_TECHNICAL_NAME_BY_ID.items()
    }


async def run(*, report_only: bool) -> dict[str, list[str]]:
    client = IamClient()
    if report_only:
        return await client.rbac_report()
    return await client.seed_rbac(build_rbac_matrix())


def main() -> None:
    parser = argparse.ArgumentParser(description="Idempotently seed the Acom IAM RBAC matrix")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Read the current IAM matrix without changing it",
    )
    args = parser.parse_args()
    matrix = asyncio.run(run(report_only=args.report))
    print(json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

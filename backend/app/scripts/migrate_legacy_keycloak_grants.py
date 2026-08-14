from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import text

from app.core.config import settings
from app.domain.contractor_delegations import CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS
from app.domain.department_delegations import DEPARTMENT_DELEGATION_ROLE_TO_PERMISSION
from app.domain.exceptions import NotFound
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.scripts.seed_iam_rbac import build_rbac_matrix


LEGACY_DELEGATION_ROLE_TO_PERMISSIONS: dict[str, frozenset[str]] = {
    **{
        role_code: frozenset({permission_code})
        for role_code, permission_code in DEPARTMENT_DELEGATION_ROLE_TO_PERMISSION.items()
    },
    "delegation.department.files.read": frozenset({"department.files.read"}),
    "delegation.department.files.upload": frozenset({"department.files.upload"}),
    "delegation.department.files.delete": frozenset({"department.files.delete"}),
    "delegation.department.offers.read": frozenset({"department.requests.read"}),
    **CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS,
}


@dataclass(frozen=True, slots=True)
class LegacyGrantTarget:
    user_id: str
    iam_account_id: str
    role_name: str | None
    legacy_roles: frozenset[str]
    permissions: frozenset[str]


def map_legacy_roles(role_codes: frozenset[str]) -> frozenset[str]:
    unknown = sorted(role_codes - LEGACY_DELEGATION_ROLE_TO_PERMISSIONS.keys())
    if unknown:
        raise ValueError(f"Unsupported legacy delegation role(s): {', '.join(unknown)}")
    return frozenset(
        permission
        for role_code in role_codes
        for permission in LEGACY_DELEGATION_ROLE_TO_PERMISSIONS[role_code]
    )


async def find_targets() -> tuple[list[LegacyGrantTarget], list[str]]:
    from app.core.uow import UnitOfWork

    async with UnitOfWork() as uow:
        rows = (
            await uow.session.execute(
                text(
                    """
                    SELECT urm.user_id AS keycloak_subject, kr.name AS role_code
                    FROM keycloak.user_role_mapping AS urm
                    JOIN keycloak.keycloak_role AS kr ON kr.id = urm.role_id
                    WHERE kr.name LIKE 'delegation.department.%'
                       OR kr.name LIKE 'delegation.contractors.%'
                    ORDER BY urm.user_id, kr.name
                    """
                )
            )
        ).all()
        keycloak_bindings = await uow.user_auth_accounts.list_for_provider(
            provider="keycloak"
        )
        iam_bindings = await uow.user_auth_accounts.list_for_provider(provider="iam")
        users = await uow.users.list_all_with_profiles()

    roles_by_subject: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        roles_by_subject[str(row.keycloak_subject)].add(str(row.role_code))

    user_ids_by_keycloak_subject: dict[str, str] = {}
    for binding in keycloak_bindings:
        user_ids_by_keycloak_subject.setdefault(
            binding.external_subject_id,
            binding.id_user,
        )
        if binding.is_active:
            user_ids_by_keycloak_subject[binding.external_subject_id] = binding.id_user

    iam_account_by_user_id = {
        binding.id_user: binding.external_subject_id
        for binding in iam_bindings
        if binding.is_active
    }
    role_name_by_user_id = {
        user.id: technical_role_name(user.id_role)
        for user, _profile in users
    }
    targets: list[LegacyGrantTarget] = []
    missing_iam_user_ids: set[str] = set()
    for keycloak_subject, role_codes in sorted(roles_by_subject.items()):
        user_id = user_ids_by_keycloak_subject.get(keycloak_subject)
        if user_id is None:
            continue
        iam_account_id = iam_account_by_user_id.get(user_id)
        if iam_account_id is None:
            missing_iam_user_ids.add(user_id)
            continue
        normalized_roles = frozenset(role_codes)
        targets.append(
            LegacyGrantTarget(
                user_id=user_id,
                iam_account_id=iam_account_id,
                role_name=role_name_by_user_id.get(user_id),
                legacy_roles=normalized_roles,
                permissions=map_legacy_roles(normalized_roles),
            )
        )
    return targets, sorted(missing_iam_user_ids)


async def run(*, apply: bool) -> int:
    targets, missing_iam_user_ids = await find_targets()
    client = IamClient()
    if apply:
        await client.seed_rbac(build_rbac_matrix())
    discovered_grants = sum(len(target.permissions) for target in targets)
    grants_to_add = 0
    accounts_to_update = 0
    applied_grants = 0
    missing_iam_account_user_ids: list[str] = []
    accounts_to_provision = 0
    accounts_provisioned = 0
    for target in targets:
        try:
            current = await client.get_account_permissions(
                account_id=target.iam_account_id
            )
        except NotFound:
            accounts_to_provision += 1
            can_provision = (
                apply
                and settings.app_env.strip().lower() in {"development", "dev", "local"}
                and target.role_name is not None
            )
            if not can_provision:
                missing_iam_account_user_ids.append(target.user_id)
                continue
            await client.provision_local_development_account(
                account_id=target.iam_account_id,
                login=target.user_id,
                role=target.role_name,
            )
            accounts_provisioned += 1
            current = await client.get_account_permissions(
                account_id=target.iam_account_id
            )
        missing_permissions = target.permissions - current.individually_granted_permissions
        grants_to_add += len(missing_permissions)
        if not missing_permissions:
            continue
        accounts_to_update += 1
        if apply:
            await client.replace_account_permission_grants(
                account_id=target.iam_account_id,
                permissions=(
                    current.individually_granted_permissions | target.permissions
                ),
            )
            applied_grants += len(missing_permissions)

    report = {
        "mode": "apply" if apply else "dry-run",
        "legacy_accounts_found": len(targets),
        "legacy_grants_discovered": discovered_grants,
        "accounts_to_update": accounts_to_update,
        "accounts_to_provision": accounts_to_provision,
        "accounts_provisioned": accounts_provisioned,
        "grants_to_add": grants_to_add,
        "legacy_grants_migrated": applied_grants,
        "missing_iam_user_ids": missing_iam_user_ids,
        "missing_iam_account_user_ids": sorted(missing_iam_account_user_ids),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if missing_iam_user_ids or missing_iam_account_user_ids else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate retained Keycloak delegation role assignments to IAM account grants"
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(apply=args.apply)))


if __name__ == "__main__":
    main()

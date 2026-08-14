from __future__ import annotations

import argparse
import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.exceptions import DomainError
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount
from app.scripts.seed_iam_rbac import build_rbac_matrix


_LOCAL_DEVELOPMENT_ENVIRONMENTS = {"development", "dev", "local"}


@dataclass(frozen=True, slots=True)
class LocalDevCandidate:
    login: str
    role_id: int


@dataclass(frozen=True, slots=True)
class LocalDevProvisionResult:
    login: str
    role: str | None
    account_created: bool = False
    binding_created: bool = False
    failure_reason: str | None = None


def _require_local_development() -> None:
    if settings.app_env.strip().lower() not in _LOCAL_DEVELOPMENT_ENVIRONMENTS:
        raise RuntimeError("Local IAM credential provisioning is allowed only in development/local")


async def find_candidates() -> list[LocalDevCandidate]:
    async with UnitOfWork() as uow:
        rows = await uow.users.list_all_with_profiles()
    return [LocalDevCandidate(login=user.id, role_id=user.id_role) for user, _profile in rows]


def _binding_account_id(binding: UserAuthAccount | None, *, login: str) -> uuid.UUID:
    if binding is None:
        return stable_iam_account_id(login)
    try:
        return uuid.UUID(binding.external_subject_id)
    except ValueError as exc:
        raise ValueError("existing IAM binding has a non-UUID subject") from exc


async def provision_candidate(
    candidate: LocalDevCandidate,
    *,
    client: IamClient,
) -> LocalDevProvisionResult:
    role = technical_role_name(candidate.role_id)
    if role is None:
        return LocalDevProvisionResult(
            login=candidate.login,
            role=None,
            failure_reason=f"unsupported local role id {candidate.role_id}",
        )

    try:
        async with UnitOfWork() as uow:
            binding = await uow.user_auth_accounts.get_by_user_provider(
                user_id=candidate.login,
                provider="iam",
                include_inactive=True,
            )
            account_id = _binding_account_id(binding, login=candidate.login)
            conflict = await uow.user_auth_accounts.get_conflicting_subject(
                provider="iam",
                subject=str(account_id),
                exclude_user_id=candidate.login,
            )
            if conflict is not None:
                return LocalDevProvisionResult(
                    login=candidate.login,
                    role=role,
                    failure_reason="IAM subject is bound to another Acom user",
                )

            account = await client.provision_local_development_account(
                account_id=account_id,
                login=candidate.login,
                role=role,
            )
            binding_created = binding is None
            if binding is None:
                await uow.user_auth_accounts.add(
                    UserAuthAccount(
                        id_user=candidate.login,
                        provider="iam",
                        external_subject_id=account.id,
                        external_username=candidate.login,
                        external_email=None,
                        is_active=True,
                    )
                )
            else:
                binding.external_username = candidate.login
                binding.is_active = True
            return LocalDevProvisionResult(
                login=candidate.login,
                role=role,
                account_created=account.created,
                binding_created=binding_created,
            )
    except (DomainError, ValueError) as exc:
        return LocalDevProvisionResult(
            login=candidate.login,
            role=role,
            failure_reason=str(exc) or exc.__class__.__name__,
        )
    except SQLAlchemyError:
        return LocalDevProvisionResult(
            login=candidate.login,
            role=role,
            failure_reason="could not save IAM binding in the local database",
        )


def _print_report(*, candidates: list[LocalDevCandidate], results: list[LocalDevProvisionResult]) -> None:
    migrated = [item for item in results if item.failure_reason is None]
    failed = [item for item in results if item.failure_reason is not None]
    print(f"Users found: {len(candidates)}")
    print(f"IAM accounts created: {sum(item.account_created for item in migrated)}")
    print(f"Existing IAM accounts reused: {sum(not item.account_created for item in migrated)}")
    print(f"IAM bindings created: {sum(item.binding_created for item in migrated)}")
    print(f"Users not migrated: {len(failed)}")
    for item in failed:
        print(f"- {item.login}: {item.failure_reason}")

    print("\nLocal test accounts (password = login):")
    print("login | role")
    for item in sorted(migrated, key=lambda value: value.login.casefold()):
        print(f"{item.login} | {item.role}")


async def run(*, apply: bool) -> int:
    _require_local_development()
    candidates = await find_candidates()
    if not apply:
        print(f"Users found: {len(candidates)}")
        print("Dry run complete; no IAM accounts, credentials, or bindings changed.")
        return 0

    client = IamClient()
    await client.seed_rbac(build_rbac_matrix())
    results = [await provision_candidate(candidate, client=client) for candidate in candidates]
    _print_report(candidates=candidates, results=results)
    return 0 if all(item.failure_reason is None for item in results) else 2


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision local-development IAM accounts with password equal to login"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(apply=args.apply)))


if __name__ == "__main__":
    main()

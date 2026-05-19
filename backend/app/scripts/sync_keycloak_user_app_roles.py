from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from sqlalchemy import and_, outerjoin, select

from app.core.config import settings
from app.domain.exceptions import Conflict
from app.infrastructure.db import SessionLocal, engine
from app.models.auth_models import UserAuthAccount
from app.models.orm_models import User
from app.services.keycloak_admin import KeycloakAdminService
from app.services.keycloak_app_roles import role_mapping_by_local_role_id


@dataclass(frozen=True, slots=True)
class LocalUserRoleBinding:
    user_id: str
    role_id: int
    keycloak_subject: str | None


def _env_flag(name: str, *, default: bool) -> bool:
    raw_value = (os.getenv(name) or "").strip().lower()
    if not raw_value:
        return default
    return raw_value in {"1", "true", "yes", "on"}


async def _load_users_for_sync() -> list[LocalUserRoleBinding]:
    async with SessionLocal() as session:
        stmt = (
            select(
                User.id,
                User.id_role,
                UserAuthAccount.external_subject_id,
            )
            .select_from(
                outerjoin(
                    User,
                    UserAuthAccount,
                    and_(
                        UserAuthAccount.id_user == User.id,
                        UserAuthAccount.provider == "keycloak",
                        UserAuthAccount.is_active.is_(True),
                    ),
                )
            )
            .order_by(User.id.asc())
        )
        rows = (await session.execute(stmt)).all()

    users: list[LocalUserRoleBinding] = []
    for user_id, role_id, external_subject_id in rows:
        subject = (external_subject_id or "").strip() or None
        users.append(
            LocalUserRoleBinding(
                user_id=str(user_id),
                role_id=int(role_id),
                keycloak_subject=subject,
            )
        )
    return users


async def sync_existing_users_app_roles() -> int:
    if not settings.keycloak_enabled:
        print("SKIP: KEYCLOAK_ENABLED=false")
        return 0

    if not _env_flag("KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE", default=True):
        print("SKIP: KEYCLOAK_INIT_SYNC_EXISTING_USERS_BY_ROLE=false")
        return 0

    role_mapping = role_mapping_by_local_role_id()
    local_users = await _load_users_for_sync()
    if not local_users:
        print("SYNC_RESULT total_users=0 assigned=0 skipped=0 removed=0")
        return 0

    keycloak_admin = KeycloakAdminService()
    admin_token = await keycloak_admin.get_admin_token()
    api_client_uuid = await keycloak_admin.get_client_uuid_by_client_id(
        client_id=settings.keycloak_api_client_id,
        admin_token=admin_token,
    )

    assigned = 0
    skipped = 0
    removed = 0

    for local_user in local_users:
        target_role = role_mapping.get(local_user.role_id)
        if target_role is None:
            skipped += 1
            print(
                "SYNC_SKIP",
                f"user_id={local_user.user_id}",
                "reason=unsupported_role_id",
                f"role_id={local_user.role_id}",
            )
            continue

        if not local_user.keycloak_subject:
            skipped += 1
            print(
                "SYNC_SKIP",
                f"user_id={local_user.user_id}",
                "reason=missing_keycloak_link",
            )
            continue

        try:
            synced, removed_count = await keycloak_admin.sync_user_app_role_for_local_role(
                keycloak_user_id=local_user.keycloak_subject,
                api_client_uuid=api_client_uuid,
                local_role_id=local_user.role_id,
                role_mapping=role_mapping,
                admin_token=admin_token,
            )
        except Conflict as exc:
            skipped += 1
            print(
                "SYNC_SKIP",
                f"user_id={local_user.user_id}",
                f"keycloak_sub={local_user.keycloak_subject}",
                "reason=sync_failed",
                f"detail={exc}",
            )
            continue

        if not synced:
            skipped += 1
            print(
                "SYNC_SKIP",
                f"user_id={local_user.user_id}",
                f"keycloak_sub={local_user.keycloak_subject}",
                "reason=missing_keycloak_user",
            )
            continue

        assigned += 1
        removed += removed_count

    print(
        "SYNC_RESULT",
        f"total_users={len(local_users)}",
        f"assigned={assigned}",
        f"skipped={skipped}",
        f"removed={removed}",
    )
    return 0


async def _run_main() -> int:
    try:
        return await sync_existing_users_app_roles()
    finally:
        await engine.dispose()


def main() -> int:
    return asyncio.run(_run_main())


if __name__ == "__main__":
    raise SystemExit(main())

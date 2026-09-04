from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iam_app.models import (
    Account,
    AccountCredential,
    AccountPermissionGrant,
    AuthActionToken,
    AuthAuditLog,
    AuthSession,
    AuthorizationCode,
    Permission,
    Role,
    RolePermission,
)


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, account_id: uuid.UUID, *, for_update: bool = False) -> Account | None:
        stmt = select(Account).where(Account.id == account_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_login(self, login: str, *, for_update: bool = False) -> Account | None:
        stmt = select(Account).where(Account.login == login)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, account: Account) -> None:
        self._session.add(account)

    async def list_ids(self) -> list[uuid.UUID]:
        stmt = select(Account.id).order_by(Account.id)
        return list((await self._session.execute(stmt)).scalars().all())

    async def flush(self) -> None:
        await self._session.flush()


class CredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, account_id: uuid.UUID, *, for_update: bool = False) -> AccountCredential | None:
        stmt = select(AccountCredential).where(AccountCredential.account_id == account_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, credential: AccountCredential) -> None:
        self._session.add(credential)


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_name(self, name: str) -> Role | None:
        return (
            await self._session.execute(select(Role).where(Role.name == name))
        ).scalar_one_or_none()

    async def get_by_id(self, role_id: int) -> Role | None:
        return await self._session.get(Role, role_id)

    async def get_permission_by_name(self, name: str) -> Permission | None:
        return (
            await self._session.execute(select(Permission).where(Permission.name == name))
        ).scalar_one_or_none()

    async def list_roles(self) -> list[Role]:
        return list((await self._session.execute(select(Role).order_by(Role.id))).scalars().all())

    async def list_permissions(self) -> list[Permission]:
        return list(
            (await self._session.execute(select(Permission).order_by(Permission.name))).scalars().all()
        )

    async def list_active_permissions_by_names(self, names: set[str]) -> list[Permission]:
        if not names:
            return []
        stmt = select(Permission).where(
            Permission.name.in_(names),
            Permission.is_active.is_(True),
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_permission_names_for_role(self, role_id: int) -> list[str]:
        stmt = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == role_id,
                Permission.is_active.is_(True),
            )
            .order_by(Permission.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def role_permission_map(self) -> dict[str, list[str]]:
        roles = await self.list_roles()
        return {
            role.name: await self.list_permission_names_for_role(role.id)
            for role in roles
        }

    async def upsert_role(self, name: str) -> Role:
        role = await self.get_by_name(name)
        if role is None:
            role = Role(name=name, is_active=True)
            self._session.add(role)
            await self._session.flush()
        else:
            role.is_active = True
        return role

    async def upsert_permission(self, name: str) -> Permission:
        permission = await self.get_permission_by_name(name)
        if permission is None:
            permission = Permission(name=name, is_active=True)
            self._session.add(permission)
            await self._session.flush()
        else:
            permission.is_active = True
        return permission

    async def replace_role_permissions(self, role_id: int, permission_ids: Iterable[int]) -> None:
        await self._session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        for permission_id in sorted(set(permission_ids)):
            self._session.add(RolePermission(role_id=role_id, permission_id=permission_id))


class AccountPermissionGrantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_permissions_for_account(
        self,
        account_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(
                AccountPermissionGrant,
                AccountPermissionGrant.permission_id == Permission.id,
            )
            .where(AccountPermissionGrant.account_id == account_id)
            .order_by(Permission.name)
        )
        if active_only:
            stmt = stmt.where(Permission.is_active.is_(True))
        return list((await self._session.execute(stmt)).scalars().all())

    async def replace(self, account_id: uuid.UUID, permission_ids: Iterable[int]) -> None:
        await self._session.execute(
            delete(AccountPermissionGrant).where(AccountPermissionGrant.account_id == account_id)
        )
        for permission_id in sorted(set(permission_ids)):
            self._session.add(
                AccountPermissionGrant(
                    account_id=account_id,
                    permission_id=permission_id,
                )
            )


class AuthorizationCodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, code: AuthorizationCode) -> None:
        self._session.add(code)

    async def get_by_hash(self, code_hash: str, *, for_update: bool = False) -> AuthorizationCode | None:
        stmt = select(AuthorizationCode).where(AuthorizationCode.code_hash == code_hash)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()


class AuthSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, auth_session: AuthSession) -> None:
        self._session.add(auth_session)

    async def get(self, session_id: uuid.UUID, *, for_update: bool = False) -> AuthSession | None:
        stmt = select(AuthSession).where(AuthSession.id == session_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_active_for_account(self, account_id: uuid.UUID) -> list[AuthSession]:
        stmt = select(AuthSession).where(
            AuthSession.account_id == account_id,
            AuthSession.revoked_at.is_(None),
        )
        return list((await self._session.execute(stmt)).scalars().all())


class ActionTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: AuthActionToken) -> None:
        self._session.add(token)

    async def invalidate_active(
        self,
        *,
        account_id: uuid.UUID,
        purpose: str,
        consumed_at: datetime,
    ) -> None:
        await self._session.execute(
            update(AuthActionToken)
            .where(
                AuthActionToken.account_id == account_id,
                AuthActionToken.purpose == purpose,
                AuthActionToken.consumed_at.is_(None),
            )
            .values(consumed_at=consumed_at)
        )

    async def get_by_hash(self, token_hash: str, *, for_update: bool = False) -> AuthActionToken | None:
        stmt = select(AuthActionToken).where(AuthActionToken.token_hash == token_hash)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_active_for_account(
        self,
        *,
        account_id: uuid.UUID,
        purpose: str,
        for_update: bool = False,
    ) -> AuthActionToken | None:
        stmt = select(AuthActionToken).where(
            AuthActionToken.account_id == account_id,
            AuthActionToken.purpose == purpose,
            AuthActionToken.consumed_at.is_(None),
        )
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_active_purposes(self, *, account_id: uuid.UUID, now: datetime) -> list[str]:
        stmt = select(AuthActionToken.purpose).where(
            AuthActionToken.account_id == account_id,
            AuthActionToken.consumed_at.is_(None),
            AuthActionToken.expires_at > now,
        )
        return list((await self._session.execute(stmt)).scalars().all())


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: AuthAuditLog) -> None:
        self._session.add(event)

    async def list_events(self) -> list[AuthAuditLog]:
        stmt = select(AuthAuditLog).order_by(AuthAuditLog.created_at, AuthAuditLog.id)
        return list((await self._session.execute(stmt)).scalars().all())

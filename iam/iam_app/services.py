from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from iam_app.core.config import settings
from iam_app.core.security import (
    as_utc,
    constant_time_equal,
    encode_access_token,
    hash_password,
    hash_secret,
    perform_dummy_password_check,
    pkce_s256,
    random_token,
    utc_now,
    verify_password,
)
from iam_app.errors import Conflict, Forbidden, InvalidCredentials, NotFound, Unauthorized
from iam_app.models import (
    Account,
    AccountCredential,
    AuthActionToken,
    AuthAuditLog,
    AuthSession,
    AuthorizationCode,
)
from iam_app.repositories import (
    AccountPermissionGrantRepository,
    AccountRepository,
    ActionTokenRepository,
    AuditRepository,
    AuthSessionRepository,
    AuthorizationCodeRepository,
    CredentialRepository,
    RoleRepository,
)


logger = logging.getLogger(__name__)

_TECHNICAL_NAME = re.compile(r"^[a-z][a-z0-9_.-]{1,127}$")
_SECRET_DETAIL_KEYS = {
    "password",
    "password_hash",
    "access_token",
    "refresh_token",
    "authorization_code",
    "code",
    "token",
}


def _safe_details(details: dict | None) -> dict:
    safe: dict = {}
    for key, value in (details or {}).items():
        if key.lower() in _SECRET_DETAIL_KEYS:
            continue
        if isinstance(value, dict):
            safe[key] = _safe_details(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        elif isinstance(value, (list, tuple)):
            safe[key] = [
                item for item in value if isinstance(item, (str, int, float, bool)) or item is None
            ]
    return safe


def _password_version(changed_at) -> int:
    return int(as_utc(changed_at).timestamp()) if changed_at is not None else 0


@dataclass(frozen=True, slots=True)
class AuthorizationResult:
    code: str
    redirect_uri: str
    state: str
    account_id: uuid.UUID
    password_version: int


@dataclass(frozen=True, slots=True)
class TokenBundle:
    access_token: str
    access_token_expires_at: int
    refresh_token: str
    refresh_token_expires_at: int


@dataclass(frozen=True, slots=True)
class AccountResult:
    account: Account
    role_name: str
    created: bool


@dataclass(frozen=True, slots=True)
class AccountPermissions:
    permissions_from_role: list[str]
    individually_granted_permissions: list[str]
    effective_permissions: list[str]


class IamService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._accounts = AccountRepository(session)
        self._permission_grants = AccountPermissionGrantRepository(session)
        self._credentials = CredentialRepository(session)
        self._roles = RoleRepository(session)
        self._codes = AuthorizationCodeRepository(session)
        self._sessions = AuthSessionRepository(session)
        self._actions = ActionTokenRepository(session)
        self._audit = AuditRepository(session)

    def _persist_security_failure(self) -> None:
        self._db.info["commit_on_error"] = True

    def _structured_security_log(
        self,
        *,
        event_type: str,
        success: bool,
        details: dict | None = None,
    ) -> None:
        payload = {
            "event_type": event_type,
            "success": success,
            "details": _safe_details(details),
            "audit_storage": "application_log",
            "reason": "auth_audit_log requires an auditable account identity",
        }
        logger.warning("iam_security_event %s", json.dumps(payload, ensure_ascii=False, sort_keys=True))

    async def _record_audit(
        self,
        *,
        account_id: uuid.UUID,
        session_id: uuid.UUID | None,
        event_type: str,
        success: bool,
        details: dict | None = None,
    ) -> None:
        await self._audit.add(
            AuthAuditLog(
                id=uuid.uuid4(),
                account_id=account_id,
                session_id=session_id,
                event_type=event_type,
                success=success,
                details=_safe_details(details),
            )
        )

    async def _record_admin_audit_or_log(
        self,
        *,
        actor_account_id: uuid.UUID | None,
        actor_session_id: uuid.UUID | None,
        event_type: str,
        details: dict,
    ) -> None:
        if actor_account_id is not None and actor_session_id is not None:
            actor_session = await self._sessions.get(actor_session_id)
            if (
                actor_session is not None
                and actor_session.account_id == actor_account_id
                and actor_session.revoked_at is None
            ):
                await self._record_audit(
                    account_id=actor_account_id,
                    session_id=actor_session_id,
                    event_type=event_type,
                    success=True,
                    details=details,
                )
                return
        self._structured_security_log(event_type=event_type, success=True, details=details)

    async def _role_and_permissions(self, account: Account) -> tuple[str, list[str]]:
        role = await self._roles.get_by_id(account.role_id)
        if role is None or not role.is_active:
            raise Forbidden()
        permissions_from_role = await self._roles.list_permission_names_for_role(role.id)
        individually_granted = await self._permission_grants.list_permissions_for_account(
            account.id
        )
        effective_permissions = sorted(
            set(permissions_from_role) | {permission.name for permission in individually_granted}
        )
        return role.name, effective_permissions

    async def get_account_permissions(
        self,
        *,
        account_id: uuid.UUID,
        for_update: bool = False,
    ) -> AccountPermissions:
        account = await self._accounts.get(account_id, for_update=for_update)
        if account is None:
            raise NotFound()
        role = await self._roles.get_by_id(account.role_id)
        if role is None or not role.is_active:
            raise Forbidden()
        permissions_from_role = await self._roles.list_permission_names_for_role(role.id)
        individually_granted = await self._permission_grants.list_permissions_for_account(
            account.id
        )
        individually_granted_names = [permission.name for permission in individually_granted]
        return AccountPermissions(
            permissions_from_role=permissions_from_role,
            individually_granted_permissions=individually_granted_names,
            effective_permissions=sorted(
                set(permissions_from_role) | set(individually_granted_names)
            ),
        )

    async def replace_account_permission_grants(
        self,
        *,
        account_id: uuid.UUID,
        permission_names: list[str],
    ) -> AccountPermissions:
        await self.get_account_permissions(account_id=account_id, for_update=True)
        requested_names = set(permission_names)
        requested_permissions = await self._roles.list_active_permissions_by_names(
            requested_names
        )
        permissions_by_name = {
            permission.name: permission for permission in requested_permissions
        }
        if set(permissions_by_name) != requested_names:
            raise Conflict("unknown or inactive permission")

        stored_permissions = await self._permission_grants.list_permissions_for_account(
            account_id,
            active_only=False,
        )
        stored_names = {permission.name for permission in stored_permissions}
        added = sorted(requested_names - stored_names)
        removed = sorted(stored_names - requested_names)
        if added or removed:
            await self._permission_grants.replace(
                account_id,
                [permission.id for permission in requested_permissions],
            )
            await self._record_audit(
                account_id=account_id,
                session_id=None,
                event_type="account.permissions.updated",
                success=True,
                details={"added": added, "removed": removed},
            )
            await self._db.flush()
        return await self.get_account_permissions(account_id=account_id)

    async def create_account(
        self,
        *,
        account_id: uuid.UUID,
        login: str,
        role_name: str,
        auth_status: str = "pending",
    ) -> AccountResult:
        normalized_login = login.strip()
        normalized_role = role_name.strip()
        role = await self._roles.get_by_name(normalized_role)
        if role is None or not role.is_active:
            raise Conflict("unknown role")

        existing = await self._accounts.get(account_id, for_update=True)
        if existing is not None:
            existing_role = await self._roles.get_by_id(existing.role_id)
            if (
                existing.login != normalized_login
                or existing_role is None
                or existing_role.name != normalized_role
            ):
                raise Conflict("idempotency conflict")
            return AccountResult(existing, normalized_role, False)

        login_owner = await self._accounts.get_by_login(normalized_login)
        if login_owner is not None:
            raise Conflict("login already exists")

        account = Account(
            id=account_id,
            login=normalized_login,
            role_id=role.id,
            auth_status=auth_status,
        )
        await self._accounts.add(account)
        await self._accounts.flush()
        await self._credentials.add(AccountCredential(account_id=account_id))
        self._structured_security_log(
            event_type="account.created",
            success=True,
            details={"account_id": str(account_id), "role": normalized_role},
        )
        return AccountResult(account, normalized_role, True)

    async def provision_local_development_account(
        self,
        *,
        account_id: uuid.UUID,
        login: str,
        role_name: str,
    ) -> AccountResult:
        """Create or reconcile a local-only account whose password equals its login.

        The password is derived inside IAM from the already stored account login; Acom
        never sends a plaintext password. This path is intentionally unavailable outside
        local development and must not be used for production onboarding.
        """
        if settings.app_env.strip().lower() not in {"development", "dev", "local"}:
            raise Forbidden("local development provisioning is disabled")

        normalized_login = login.strip()
        normalized_role = role_name.strip()
        role = await self._roles.get_by_name(normalized_role)
        if role is None or not role.is_active:
            raise Conflict("unknown role")

        now = utc_now()
        account = await self._accounts.get(account_id, for_update=True)
        created = account is None
        password_changed = False
        if account is None:
            login_owner = await self._accounts.get_by_login(normalized_login)
            if login_owner is not None:
                raise Conflict("login already exists")
            account = Account(
                id=account_id,
                login=normalized_login,
                role_id=role.id,
                auth_status="active",
            )
            await self._accounts.add(account)
            await self._accounts.flush()
        else:
            if account.login != normalized_login:
                login_owner = await self._accounts.get_by_login(normalized_login, for_update=True)
                if login_owner is not None and login_owner.id != account.id:
                    raise Conflict("login already exists")
                account.login = normalized_login
            account.role_id = role.id
            account.auth_status = "active"
            account.updated_at = now

        credential = await self._credentials.get(account.id, for_update=True)
        if credential is None:
            credential = AccountCredential(account_id=account.id)
            await self._credentials.add(credential)
            password_changed = True
        elif not credential.password_hash or not await verify_password(account.login, credential.password_hash):
            password_changed = True

        if password_changed:
            credential.password_hash = await hash_password(account.login)
            credential.password_algo = "argon2id"
            credential.password_changed_at = now
            credential.failed_login_count = 0
            credential.locked_until = None
            credential.updated_at = now
            if not created:
                await self.revoke_all(account_id=account.id, reason="local_development_password_reset")

        self._structured_security_log(
            event_type="local_development.account_provisioned",
            success=True,
            details={
                "account_id": str(account.id),
                "role": normalized_role,
                "created": created,
                "password_changed": password_changed,
            },
        )
        return AccountResult(account, normalized_role, created)

    async def authenticate_and_create_code(
        self,
        *,
        login: str,
        password: str,
        state: str,
        pkce_challenge: str,
        redirect_uri: str,
    ) -> AuthorizationResult:
        account = await self._accounts.get_by_login(login.strip(), for_update=True)
        if account is None:
            await perform_dummy_password_check(password)
            self._structured_security_log(
                event_type="login.failed",
                success=False,
                details={"reason": "invalid_credentials"},
            )
            raise InvalidCredentials()

        credential = await self._credentials.get(account.id, for_update=True)
        now = utc_now()
        if account.auth_status != "active" or credential is None or not credential.password_hash:
            if credential is None or not credential.password_hash:
                await perform_dummy_password_check(password)
            self._structured_security_log(
                event_type="login.failed",
                success=False,
                details={"account_id": str(account.id), "reason": "account_unavailable"},
            )
            raise InvalidCredentials()

        if credential.locked_until is not None and as_utc(credential.locked_until) > now:
            self._structured_security_log(
                event_type="login.failed",
                success=False,
                details={"account_id": str(account.id), "reason": "temporarily_locked"},
            )
            raise InvalidCredentials()

        if not await verify_password(password, credential.password_hash):
            credential.failed_login_count += 1
            if credential.failed_login_count >= settings.login_max_failures:
                credential.locked_until = now + timedelta(seconds=settings.login_lock_seconds)
            credential.updated_at = now
            self._structured_security_log(
                event_type="login.failed",
                success=False,
                details={"account_id": str(account.id), "reason": "invalid_credentials"},
            )
            self._persist_security_failure()
            raise InvalidCredentials()

        credential.failed_login_count = 0
        credential.locked_until = None
        credential.updated_at = now
        return await self._create_authorization_code(
            account_id=account.id,
            password_version=_password_version(credential.password_changed_at),
            state=state,
            pkce_challenge=pkce_challenge,
            redirect_uri=redirect_uri,
        )

    async def create_code_for_browser_session(
        self,
        *,
        account_id: uuid.UUID,
        password_version: int,
        state: str,
        pkce_challenge: str,
        redirect_uri: str,
    ) -> AuthorizationResult:
        account = await self._accounts.get(account_id, for_update=True)
        credential = await self._credentials.get(account_id, for_update=True)
        if (
            account is None
            or account.auth_status != "active"
            or credential is None
            or not credential.password_hash
            or _password_version(credential.password_changed_at) != password_version
        ):
            raise Unauthorized()
        await self._role_and_permissions(account)
        return await self._create_authorization_code(
            account_id=account.id,
            password_version=password_version,
            state=state,
            pkce_challenge=pkce_challenge,
            redirect_uri=redirect_uri,
        )

    async def _create_authorization_code(
        self,
        *,
        account_id: uuid.UUID,
        password_version: int,
        state: str,
        pkce_challenge: str,
        redirect_uri: str,
    ) -> AuthorizationResult:
        now = utc_now()
        raw_code = random_token()
        await self._codes.add(
            AuthorizationCode(
                id=uuid.uuid4(),
                account_id=account_id,
                code_hash=hash_secret(raw_code),
                pkce_challenge=pkce_challenge,
                pkce_method="S256",
                redirect_uri=redirect_uri,
                expires_at=now + timedelta(seconds=settings.authorization_code_ttl_seconds),
            )
        )
        return AuthorizationResult(
            code=raw_code,
            redirect_uri=redirect_uri,
            state=state,
            account_id=account_id,
            password_version=password_version,
        )

    def _new_refresh_token(self, session_id: uuid.UUID) -> tuple[str, str]:
        secret = random_token()
        return f"{session_id}.{secret}", hash_secret(secret)

    def _parse_refresh_token(self, raw_token: str) -> tuple[uuid.UUID, str]:
        session_part, separator, secret = raw_token.partition(".")
        if not separator or not secret:
            raise Unauthorized()
        try:
            return uuid.UUID(session_part), secret
        except ValueError as exc:
            raise Unauthorized() from exc

    async def exchange_code(
        self,
        *,
        raw_code: str,
        code_verifier: str,
        redirect_uri: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenBundle:
        code = await self._codes.get_by_hash(hash_secret(raw_code), for_update=True)
        now = utc_now()
        if (
            code is None
            or code.consumed_at is not None
            or as_utc(code.expires_at) <= now
            or code.redirect_uri != redirect_uri
            or code.pkce_method != "S256"
            or not constant_time_equal(code.pkce_challenge, pkce_s256(code_verifier))
        ):
            self._structured_security_log(
                event_type="authorization_code.failed",
                success=False,
                details={"reason": "invalid_or_consumed_code"},
            )
            raise Unauthorized()

        account = await self._accounts.get(code.account_id, for_update=True)
        if account is None or account.auth_status != "active":
            raise Unauthorized()
        code.consumed_at = now

        session_id = uuid.uuid4()
        refresh_token, refresh_hash = self._new_refresh_token(session_id)
        max_expires_at = now + timedelta(seconds=settings.refresh_max_ttl_seconds)
        await self._sessions.add(
            AuthSession(
                id=session_id,
                account_id=account.id,
                refresh_token_hash=refresh_hash,
                created_at=now,
                last_used_at=now,
                expires_at=max_expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        await self._db.flush()
        role_name, permissions = await self._role_and_permissions(account)
        access_token, access_expires_at = encode_access_token(
            account_id=str(account.id),
            session_id=str(session_id),
            role=role_name,
            permissions=permissions,
        )
        await self._record_audit(
            account_id=account.id,
            session_id=session_id,
            event_type="login.success",
            success=True,
            details={"role": role_name},
        )
        refresh_expires_at = min(
            max_expires_at,
            now + timedelta(seconds=settings.refresh_idle_ttl_seconds),
        )
        return TokenBundle(
            access_token=access_token,
            access_token_expires_at=access_expires_at,
            refresh_token=refresh_token,
            refresh_token_expires_at=int(refresh_expires_at.timestamp()),
        )

    async def refresh(self, *, raw_refresh_token: str) -> TokenBundle:
        try:
            session_id, secret = self._parse_refresh_token(raw_refresh_token)
        except Unauthorized:
            self._structured_security_log(
                event_type="refresh.failed",
                success=False,
                details={"reason": "malformed_refresh_token"},
            )
            raise
        auth_session = await self._sessions.get(session_id, for_update=True)
        now = utc_now()
        if auth_session is None:
            self._structured_security_log(
                event_type="refresh.failed",
                success=False,
                details={"reason": "unknown_session"},
            )
            raise Unauthorized()
        failure_reason: str | None = None
        if auth_session.revoked_at is not None:
            failure_reason = "session_revoked"
        elif as_utc(auth_session.expires_at) <= now:
            failure_reason = "session_expired"
        elif (
            as_utc(auth_session.last_used_at) + timedelta(seconds=settings.refresh_idle_ttl_seconds)
            <= now
        ):
            failure_reason = "session_idle_expired"
        if failure_reason is not None:
            await self._record_audit(
                account_id=auth_session.account_id,
                session_id=auth_session.id,
                event_type="refresh.failed",
                success=False,
                details={"reason": failure_reason},
            )
            self._persist_security_failure()
            raise Unauthorized()

        if not constant_time_equal(auth_session.refresh_token_hash, hash_secret(secret)):
            auth_session.revoked_at = now
            auth_session.revoke_reason = "refresh_reuse"
            await self._record_audit(
                account_id=auth_session.account_id,
                session_id=auth_session.id,
                event_type="refresh.reuse",
                success=False,
                details={"reason": "refresh_secret_mismatch"},
            )
            self._persist_security_failure()
            raise Unauthorized()

        account = await self._accounts.get(auth_session.account_id)
        if account is None or account.auth_status != "active":
            auth_session.revoked_at = now
            auth_session.revoke_reason = "account_unavailable"
            await self._record_audit(
                account_id=auth_session.account_id,
                session_id=auth_session.id,
                event_type="refresh.failed",
                success=False,
                details={"reason": "account_unavailable"},
            )
            self._persist_security_failure()
            raise Unauthorized()

        rotated_token, rotated_hash = self._new_refresh_token(auth_session.id)
        auth_session.refresh_token_hash = rotated_hash
        auth_session.last_used_at = now
        role_name, permissions = await self._role_and_permissions(account)
        access_token, access_expires_at = encode_access_token(
            account_id=str(account.id),
            session_id=str(auth_session.id),
            role=role_name,
            permissions=permissions,
        )
        await self._record_audit(
            account_id=account.id,
            session_id=auth_session.id,
            event_type="refresh.success",
            success=True,
            details={"role": role_name},
        )
        refresh_expires_at = min(
            as_utc(auth_session.expires_at),
            now + timedelta(seconds=settings.refresh_idle_ttl_seconds),
        )
        return TokenBundle(
            access_token=access_token,
            access_token_expires_at=access_expires_at,
            refresh_token=rotated_token,
            refresh_token_expires_at=int(refresh_expires_at.timestamp()),
        )

    async def logout(self, *, raw_refresh_token: str, reason: str = "logout") -> None:
        session_id, secret = self._parse_refresh_token(raw_refresh_token)
        auth_session = await self._sessions.get(session_id, for_update=True)
        if auth_session is None:
            return
        now = utc_now()
        if not constant_time_equal(auth_session.refresh_token_hash, hash_secret(secret)):
            if auth_session.revoked_at is None:
                auth_session.revoked_at = now
                auth_session.revoke_reason = "logout_token_mismatch"
            await self._record_audit(
                account_id=auth_session.account_id,
                session_id=auth_session.id,
                event_type="logout.failed",
                success=False,
                details={"reason": "refresh_secret_mismatch"},
            )
            self._persist_security_failure()
            raise Unauthorized()
        if auth_session.revoked_at is None:
            auth_session.revoked_at = now
            auth_session.revoke_reason = reason
            await self._record_audit(
                account_id=auth_session.account_id,
                session_id=auth_session.id,
                event_type="logout",
                success=True,
                details={"reason": reason},
            )

    async def revoke_all(
        self,
        *,
        account_id: uuid.UUID,
        reason: str,
        actor_account_id: uuid.UUID | None = None,
        actor_session_id: uuid.UUID | None = None,
    ) -> int:
        if await self._accounts.get(account_id) is None:
            raise NotFound()
        now = utc_now()
        active = await self._sessions.list_active_for_account(account_id)
        for item in active:
            item.revoked_at = now
            item.revoke_reason = reason
            await self._record_audit(
                account_id=item.account_id,
                session_id=item.id,
                event_type="session.revoked",
                success=True,
                details={"reason": reason},
            )
        await self._record_admin_audit_or_log(
            actor_account_id=actor_account_id,
            actor_session_id=actor_session_id,
            event_type="account.sessions_revoked",
            details={"target_account_id": str(account_id), "reason": reason, "count": len(active)},
        )
        return len(active)

    async def update_role(
        self,
        *,
        account_id: uuid.UUID,
        role_name: str,
        actor_account_id: uuid.UUID | None,
        actor_session_id: uuid.UUID | None,
    ) -> AccountResult:
        account = await self._accounts.get(account_id, for_update=True)
        role = await self._roles.get_by_name(role_name.strip())
        if account is None:
            raise NotFound()
        if role is None or not role.is_active:
            raise Conflict("unknown role")
        previous_role = await self._roles.get_by_id(account.role_id)
        account.role_id = role.id
        account.updated_at = utc_now()
        await self._record_admin_audit_or_log(
            actor_account_id=actor_account_id,
            actor_session_id=actor_session_id,
            event_type="account.role_changed",
            details={
                "target_account_id": str(account_id),
                "old_role": previous_role.name if previous_role else None,
                "new_role": role.name,
            },
        )
        return AccountResult(account, role.name, False)

    async def update_status(
        self,
        *,
        account_id: uuid.UUID,
        auth_status: str,
        actor_account_id: uuid.UUID | None,
        actor_session_id: uuid.UUID | None,
    ) -> AccountResult:
        account = await self._accounts.get(account_id, for_update=True)
        if account is None:
            raise NotFound()
        old_status = account.auth_status
        account.auth_status = auth_status
        account.updated_at = utc_now()
        if auth_status in {"blocked", "disabled"}:
            await self.revoke_all(
                account_id=account_id,
                reason=f"account_{auth_status}",
                actor_account_id=actor_account_id,
                actor_session_id=actor_session_id,
            )
        await self._record_admin_audit_or_log(
            actor_account_id=actor_account_id,
            actor_session_id=actor_session_id,
            event_type=f"account.{auth_status}",
            details={
                "target_account_id": str(account_id),
                "old_status": old_status,
                "new_status": auth_status,
            },
        )
        role, _ = await self._role_and_permissions(account)
        return AccountResult(account, role, False)

    async def create_action_token(
        self,
        *,
        account_id: uuid.UUID,
        purpose: str,
    ) -> tuple[str, int]:
        if await self._accounts.get(account_id) is None:
            raise NotFound()
        now = utc_now()
        await self._actions.invalidate_active(
            account_id=account_id,
            purpose=purpose,
            consumed_at=now,
        )
        raw_token = random_token()
        expires_at = now + timedelta(seconds=settings.action_token_ttl_seconds)
        await self._actions.add(
            AuthActionToken(
                id=uuid.uuid4(),
                account_id=account_id,
                purpose=purpose,
                token_hash=hash_secret(raw_token),
                expires_at=expires_at,
            )
        )
        self._structured_security_log(
            event_type=f"{purpose}.token_created",
            success=True,
            details={"account_id": str(account_id)},
        )
        return raw_token, int(expires_at.timestamp())

    async def consume_action_token(
        self,
        *,
        raw_token: str,
        purpose: str,
        new_password: str,
    ) -> None:
        if len(new_password) < 12 or len(new_password) > 128:
            raise Conflict("password policy")
        token = await self._actions.get_by_hash(hash_secret(raw_token), for_update=True)
        now = utc_now()
        if (
            token is None
            or token.purpose != purpose
            or token.consumed_at is not None
            or as_utc(token.expires_at) <= now
        ):
            self._structured_security_log(
                event_type=f"{purpose}.failed",
                success=False,
                details={"reason": "invalid_or_consumed_action_token"},
            )
            raise Unauthorized()
        account = await self._accounts.get(token.account_id, for_update=True)
        credential = await self._credentials.get(token.account_id, for_update=True)
        if account is None or credential is None or account.auth_status in {"blocked", "disabled"}:
            raise Unauthorized()

        credential.password_hash = await hash_password(new_password)
        credential.password_algo = "argon2id"
        credential.password_changed_at = now
        credential.failed_login_count = 0
        credential.locked_until = None
        credential.updated_at = now
        token.consumed_at = now
        if purpose == "password_setup" and account.auth_status == "pending":
            account.auth_status = "active"
            account.updated_at = now
        if purpose == "password_reset":
            await self.revoke_all(account_id=account.id, reason="password_reset")
        self._structured_security_log(
            event_type=f"{purpose}.completed",
            success=True,
            details={"account_id": str(account.id)},
        )

    async def seed_rbac(self, matrix: dict[str, list[str]]) -> dict[str, list[str]]:
        if not matrix:
            raise Conflict("empty RBAC matrix")
        if any(name.startswith("delegation.") or not _TECHNICAL_NAME.fullmatch(name) for name in matrix):
            raise Conflict("invalid role name")
        all_permission_names = sorted({permission for values in matrix.values() for permission in values})
        if any(
            permission.startswith("delegation.") or not _TECHNICAL_NAME.fullmatch(permission)
            for permission in all_permission_names
        ):
            raise Conflict("invalid permission name")

        permissions = {
            name: await self._roles.upsert_permission(name)
            for name in all_permission_names
        }
        for role_name, permission_names in sorted(matrix.items()):
            role = await self._roles.upsert_role(role_name)
            await self._roles.replace_role_permissions(
                role.id,
                [permissions[name].id for name in permission_names],
            )
        await self._db.flush()
        self._structured_security_log(
            event_type="rbac.seeded",
            success=True,
            details={"roles": len(matrix), "permissions": len(all_permission_names)},
        )
        return await self._roles.role_permission_map()

    async def rbac_report(self) -> dict[str, list[str]]:
        return await self._roles.role_permission_map()

    async def reconcile_account_ids(
        self,
        known_account_ids: set[uuid.UUID],
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        iam_account_ids = set(await self._accounts.list_ids())
        orphan_iam_ids = sorted(iam_account_ids - known_account_ids, key=str)
        missing_iam_ids = sorted(known_account_ids - iam_account_ids, key=str)
        return orphan_iam_ids, missing_iam_ids

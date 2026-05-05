from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.core.config import settings
from app.domain.exceptions import Conflict, Forbidden
from app.models.auth_models import UserAuthAccount
from app.models.orm_models import Profile, User
from app.repositories.profiles import ProfileRepository
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.user_contact_channels import UserContactChannelRepository
from app.repositories.users import UserRepository
from app.services.keycloak_oidc import KeycloakAccessTokenClaims


_LOCAL_USER_ID_PATTERN = re.compile(r"[^a-z0-9_]+")
_PROFILE_PLACEHOLDER = "Не указано"


@dataclass(frozen=True, slots=True)
class SyncedIdentity:
    user: User
    auth_provider: str
    created_local_user: bool


def _normalize_local_user_id(username: str | None, *, subject: str) -> str:
    candidate = (username or "").strip().lower()
    candidate = _LOCAL_USER_ID_PATTERN.sub("_", candidate).strip("_")
    if not candidate:
        candidate = f"kc_{hashlib.sha256(subject.encode('utf-8')).hexdigest()[:12]}"
    return candidate[:128]


def _normalize_email(email: str | None) -> str | None:
    normalized = (email or "").strip().lower()
    return normalized or None


def _normalize_full_name(claims: KeycloakAccessTokenClaims) -> str | None:
    explicit = (claims.full_name or "").strip()
    if explicit:
        return explicit

    parts = [part.strip() for part in (claims.given_name, claims.family_name) if part and part.strip()]
    if parts:
        return " ".join(parts)

    return None


def _is_blank_profile_value(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return normalized in {"", _PROFILE_PLACEHOLDER.lower(), "none", "null"}


class IdentitySyncService:
    def __init__(
        self,
        *,
        users: UserRepository,
        user_auth_accounts: UserAuthAccountRepository,
        user_contact_channels: UserContactChannelRepository,
        profiles: ProfileRepository | None = None,
    ) -> None:
        self._users = users
        self._user_auth_accounts = user_auth_accounts
        self._user_contact_channels = user_contact_channels
        self._profiles = profiles

    async def sync_keycloak_identity(
        self,
        claims: KeycloakAccessTokenClaims,
        *,
        allow_user_creation: bool = False,
    ) -> SyncedIdentity:
        account = await self._user_auth_accounts.get_by_provider_subject(
            provider="keycloak",
            subject=claims.subject,
        )
        created_local_user = False

        if account is None:
            user = await self._resolve_or_create_local_user(claims, allow_user_creation=allow_user_creation)
            account = UserAuthAccount(
                id_user=user.id,
                provider="keycloak",
                external_subject_id=claims.subject,
                external_username=claims.preferred_username,
                external_email=claims.email,
                is_active=True,
            )
            await self._user_auth_accounts.add(account)
            created_local_user = user.id_role == settings.contractor_role_id and user.status == "review"
        else:
            user = await self._users.get_by_id(account.id_user)
            if user is None:
                raise ValueError(f"Broken auth account link for user {account.id_user}")

        await self._user_auth_accounts.touch_login(
            account=account,
            username=claims.preferred_username,
            email=claims.email,
        )

        if claims.email:
            await self._user_contact_channels.upsert_channel(
                user_id=user.id,
                channel_type="email",
                channel_value=claims.email,
                is_verified=claims.email_verified,
                is_primary=True,
            )

        if self._profiles is not None:
            await self._sync_profile_basics(user=user, claims=claims)

        return SyncedIdentity(
            user=user,
            auth_provider="keycloak",
            created_local_user=created_local_user,
        )

    async def _sync_profile_basics(
        self,
        *,
        user: User,
        claims: KeycloakAccessTokenClaims,
    ) -> None:
        if self._profiles is None:
            return

        normalized_email = _normalize_email(claims.email)
        normalized_full_name = _normalize_full_name(claims)
        profile = await self._profiles.get_by_id(user.id)

        if profile is None:
            await self._profiles.add(
                Profile(
                    id=user.id,
                    full_name=normalized_full_name or _PROFILE_PLACEHOLDER,
                    phone=_PROFILE_PLACEHOLDER,
                    mail=normalized_email or _PROFILE_PLACEHOLDER,
                )
            )
            return

        if normalized_full_name and _is_blank_profile_value(profile.full_name):
            profile.full_name = normalized_full_name

        if normalized_email and _is_blank_profile_value(profile.mail):
            profile.mail = normalized_email

    async def _resolve_or_create_local_user(
        self,
        claims: KeycloakAccessTokenClaims,
        *,
        allow_user_creation: bool,
    ) -> User:
        if (
            settings.keycloak_bootstrap_binding_enabled
            and claims.preferred_username == settings.keycloak_bootstrap_app_username
        ):
            bootstrap_user = await self._users.get_by_id("superadmin")
            if bootstrap_user is not None:
                existing_binding = await self._user_auth_accounts.get_by_user_provider(
                    user_id=bootstrap_user.id,
                    provider="keycloak",
                )
                if existing_binding is None:
                    return bootstrap_user

        if not allow_user_creation:
            auto_linked_user = await self._try_auto_link_existing_user(claims)
            if auto_linked_user is not None:
                return auto_linked_user

        if not allow_user_creation:
            raise Forbidden("Local application account is not linked")

        user_id = _normalize_local_user_id(claims.preferred_username, subject=claims.subject)
        if await self._users.exists(user_id):
            user_id = f"{user_id}_{hashlib.sha256(claims.subject.encode('utf-8')).hexdigest()[:8]}"

        user = User(
            id=user_id,
            id_role=settings.contractor_role_id,
            status="review",
        )
        await self._users.add(user)
        # Ensure parent row exists before we queue dependent auth/contact records.
        await self._users.flush()
        return user

    async def _try_auto_link_existing_user(self, claims: KeycloakAccessTokenClaims) -> User | None:
        if settings.keycloak_dev_auto_link_by_username_enabled:
            linked_user = await self._try_auto_link_by_username(claims)
            if linked_user is not None:
                return linked_user

        if settings.keycloak_prod_auto_link_by_verified_email_enabled:
            linked_user = await self._try_auto_link_by_verified_email(claims)
            if linked_user is not None:
                return linked_user

        return None

    async def _try_auto_link_by_username(self, claims: KeycloakAccessTokenClaims) -> User | None:
        preferred_username = (claims.preferred_username or "").strip()
        if not preferred_username:
            return None

        user = await self._users.get_by_id(preferred_username)
        if user is None:
            return None

        await self._ensure_user_can_bind_keycloak(user=user, claims=claims)
        return user

    async def _try_auto_link_by_verified_email(self, claims: KeycloakAccessTokenClaims) -> User | None:
        normalized_email = _normalize_email(claims.email)
        if not claims.email_verified or normalized_email is None:
            return None

        candidates = await self._users.list_by_email(email=normalized_email)
        if not candidates:
            return None
        if len(candidates) > 1:
            raise Conflict("Verified Keycloak email matches multiple local users")

        user = candidates[0]
        await self._ensure_user_can_bind_keycloak(user=user, claims=claims)
        return user

    async def _ensure_user_can_bind_keycloak(
        self,
        *,
        user: User,
        claims: KeycloakAccessTokenClaims,
    ) -> None:
        conflicting_subject = await self._user_auth_accounts.get_conflicting_subject(
            provider="keycloak",
            subject=claims.subject,
            exclude_user_id=user.id,
        )
        if conflicting_subject is not None:
            raise Conflict("Keycloak account is already linked to another local user")

        existing_binding = await self._user_auth_accounts.get_by_user_provider(
            user_id=user.id,
            provider="keycloak",
        )
        if existing_binding is not None and existing_binding.external_subject_id != claims.subject:
            raise Conflict("Local user is already linked to another Keycloak account")

from __future__ import annotations

from dataclasses import dataclass
from app.core.config import settings
from app.core.registration_invite import RegistrationInviteClaims, RegistrationInviteTokenCodec
from app.core.uow import UnitOfWork
from app.domain.auth_context import CurrentUser
from app.domain.authorization import require_permission
from app.domain.contractor_validation import validate_optional_email
from app.domain.exceptions import Conflict, Forbidden, Unauthorized
from app.domain.permissions import PermissionCodes


@dataclass(frozen=True, slots=True)
class InvitationInspectResult:
    status: str
    email: str | None = None
    role_id: int | None = None
    expires_at: str | None = None
    login: str | None = None
    full_name: str | None = None
    phone: str | None = None
    company_name: str | None = None
    inn: str | None = None
    company_phone: str | None = None


class RegistrationInvitationService:
    def __init__(self, uow: UnitOfWork | None = None, *, codec: RegistrationInviteTokenCodec | None = None) -> None:
        self._uow = uow
        self._codec = codec or RegistrationInviteTokenCodec()

    def create_contractor_invitation(
        self,
        *,
        current_user: CurrentUser,
        email: str,
        unit_id: int | None = None,
    ) -> str:
        require_permission(
            current_user,
            PermissionCodes.USERS_REGISTRATION_INVITE,
            message="Недостаточно прав для приглашения к регистрации",
        )
        if current_user.role_id == settings.contractor_role_id:
            raise Forbidden("Контрагент не может отправлять приглашения")
        return self.issue_contractor_registration_token(
            email=email,
            inviter_id=current_user.user_id,
            unit_id=unit_id,
        )

    def issue_contractor_registration_token(
        self,
        *,
        email: str,
        inviter_id: str,
        unit_id: int | None = None,
    ) -> str:
        try:
            normalized_email = validate_optional_email(email.strip().lower(), allow_placeholder=False)
        except ValueError as exc:
            raise Conflict(str(exc)) from exc
        if not normalized_email:
            raise Conflict("Укажите email для приглашения")
        if not inviter_id.strip():
            raise Conflict("Не указан инициатор приглашения")
        return self._codec.issue(
            email=normalized_email,
            role_id=settings.contractor_role_id,
            inviter_id=inviter_id.strip(),
            unit_id=unit_id,
        )

    @staticmethod
    def registration_portal_url(raw_token: str) -> str:
        if settings.web_base_url:
            return f"{settings.web_base_url.rstrip('/')}/register?token={raw_token}"
        return f"/register?token={raw_token}"

    async def inspect(self, *, raw_token: str) -> InvitationInspectResult:
        try:
            claims = self.parse(raw_token)
        except Unauthorized as exc:
            if "истёк" in str(exc):
                return InvitationInspectResult(status="expired")
            return InvitationInspectResult(status="invalid")
        if self._uow is not None:
            existing = await self._load_existing_registration(claims.email)
            if existing is not None:
                user, profile, company, email_verified = existing
                if user.status == "review" and not email_verified:
                    return InvitationInspectResult(
                        status="in_progress",
                        email=(profile.mail if profile and profile.mail else claims.email),
                        role_id=claims.role_id,
                        expires_at=str(claims.exp),
                        login=user.id,
                        full_name=profile.full_name if profile else None,
                        phone=profile.phone if profile else None,
                        company_name=company.company_name if company else None,
                        inn=company.inn if company else None,
                        company_phone=company.phone if company else None,
                    )
                return InvitationInspectResult(status="already_registered", email=claims.email)
        return InvitationInspectResult(
            status="ok",
            email=claims.email,
            role_id=claims.role_id,
            expires_at=str(claims.exp),
        )

    async def load_in_progress_registration(self, email: str):
        existing = await self._load_existing_registration(email)
        if existing is None:
            return None
        user, profile, company, email_verified = existing
        if user.status != "review" or email_verified:
            return None
        return user, profile, company

    async def _load_existing_registration(self, email: str):
        if self._uow is None:
            return None
        user_id = await self._resolve_user_id(email)
        if user_id is None:
            return None
        user = await self._uow.users.get_by_id(user_id)
        if user is None:
            return None
        profile = await self._uow.profiles.get_by_id(user_id)
        company = await self._uow.company_contacts.get_by_id(user_id)
        channel = await self._uow.user_contact_channels.get_primary_by_type(
            user_id=user_id,
            channel_type="email",
        )
        email_verified = bool(channel is not None and channel.is_verified)
        return user, profile, company, email_verified

    async def _resolve_user_id(self, email: str) -> str | None:
        if self._uow is None:
            return None
        profile_id = await self._uow.profiles.get_id_by_mail(email=email)
        if profile_id:
            return profile_id
        channel_ids = await self._uow.user_contact_channels.list_user_ids_by_primary_email(email=email)
        if channel_ids:
            return channel_ids[0]
        binding = await self._uow.user_auth_accounts.get_by_external_email(provider="iam", email=email)
        if binding is not None:
            return binding.id_user
        return None

    async def resolve_existing_user_id(self, email: str) -> str | None:
        """Return the MAIN identity linked to an email, when it already exists."""
        return await self._resolve_user_id(email.strip().lower())

    def parse(self, raw_token: str) -> RegistrationInviteClaims:
        return self._codec.parse(raw_token)

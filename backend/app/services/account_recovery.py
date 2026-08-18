from __future__ import annotations

from dataclasses import dataclass
import logging

from app.core.request_id import get_request_id
from app.core.uow import UnitOfWork
from app.domain.contractor_validation import validate_optional_email
from app.infrastructure.iam_client import IamClient
from app.services.email_verification import FIRST_ACCESS_PURPOSE, EmailVerificationService
from app.services.iam_password_actions import send_iam_password_action_email_safely

logger = logging.getLogger(__name__)

GENERIC_RECOVERY_DETAIL = "Если учётная запись существует, инструкция отправлена на связанный email."


@dataclass(frozen=True, slots=True)
class PasswordRecoveryResult:
    detail: str


class AccountRecoveryService:
    def __init__(self, uow: UnitOfWork, *, iam_client: IamClient | None = None) -> None:
        self._uow = uow
        self._iam_client = iam_client or IamClient()

    async def request_recovery(self, *, identifier: str) -> PasswordRecoveryResult:
        user = await self._resolve_user(identifier)
        if user is None:
            return PasswordRecoveryResult(detail=GENERIC_RECOVERY_DETAIL)
        binding = await self._uow.user_auth_accounts.get_by_user_provider(
            user_id=user.id,
            provider="iam",
        )
        if binding is None:
            return PasswordRecoveryResult(detail=GENERIC_RECOVERY_DETAIL)
        channel = await self._uow.user_contact_channels.get_primary_by_type(
            user_id=user.id,
            channel_type="email",
        )
        delivery_email = (channel.channel_value if channel is not None else "").strip().lower()
        if not delivery_email:
            return PasswordRecoveryResult(detail=GENERIC_RECOVERY_DETAIL)
        try:
            validate_optional_email(delivery_email, allow_placeholder=False)
        except ValueError:
            return PasswordRecoveryResult(detail=GENERIC_RECOVERY_DETAIL)

        credential_state = await self._iam_client.get_credential_state(account_id=binding.external_subject_id)
        if not credential_state.password_set:
            await EmailVerificationService(
                self._uow.profiles,
                self._uow.user_contact_channels,
                user_auth_accounts=self._uow.user_auth_accounts,
                iam_client=self._iam_client,
            ).request_profile_verification(
                user_id=user.id,
                email=delivery_email,
                purpose=FIRST_ACCESS_PURPOSE,
            )
            return PasswordRecoveryResult(detail=GENERIC_RECOVERY_DETAIL)

        action = await self._iam_client.create_action_token(
            account_id=binding.external_subject_id,
            purpose="password_reset",
        )
        self._uow.add_after_commit_hook(
            lambda: send_iam_password_action_email_safely(
                to_email=delivery_email,
                raw_token=action.token,
                purpose="password_reset",
            )
        )
        return PasswordRecoveryResult(detail=GENERIC_RECOVERY_DETAIL)

    async def issue_setup_after_verified_access(self, *, user_id: str, email: str) -> str | None:
        binding = await self._uow.user_auth_accounts.get_by_user_provider(
            user_id=user_id,
            provider="iam",
        )
        if binding is None:
            return None
        action = await self._iam_client.create_action_token(
            account_id=binding.external_subject_id,
            purpose="password_setup",
        )
        await send_iam_password_action_email_safely(
            to_email=email,
            raw_token=action.token,
            purpose="password_setup",
        )
        from urllib.parse import quote

        from app.core.config import settings

        return (
            f"{settings.resolved_iam_public_base_url}/password/setup?token={quote(action.token, safe='')}"
        )

    async def _resolve_user(self, identifier: str):
        normalized = identifier.strip()
        if not normalized:
            return None
        user = await self._uow.users.get_by_id(normalized)
        if user is not None:
            return user
        try:
            email = validate_optional_email(normalized.lower(), allow_placeholder=False)
        except ValueError:
            return None
        if email is None:
            return None
        user_ids = await self._uow.user_contact_channels.list_user_ids_by_primary_email(email=email)
        unique_ids = list(dict.fromkeys(user_ids))
        if len(unique_ids) == 1:
            return await self._uow.users.get_by_id(unique_ids[0])
        if len(unique_ids) > 1:
            logger.warning(
                "password_recovery_ambiguous_email request_id=%s",
                get_request_id(),
            )
        return None

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.contractor_validation import validate_inn, validate_optional_email, validate_ru_phone
from app.domain.exceptions import Conflict, Unauthorized
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount
from app.models.orm_models import CompanyContact, Profile, User
from app.services.account_recovery import AccountRecoveryService
from app.services.registration_admin_notify import schedule_registration_review_required_notification
from app.services.registration_invitations import RegistrationInvitationService

PLACEHOLDER_TEXT = "Не указано"
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


@dataclass(frozen=True, slots=True)
class RegistrationSubmitResult:
    user_id: str
    status: str
    email: str


class RegistrationSubmitService:
    def __init__(self, uow: UnitOfWork, *, iam_client: IamClient | None = None) -> None:
        self._uow = uow
        self._iam_client = iam_client or IamClient()

    async def submit(
        self,
        *,
        token: str,
        login: str,
        password: str | None = None,
        password_confirmation: str | None = None,
        email: str,
        full_name: str,
        phone: str,
        company_name: str,
        inn: str,
        company_phone: str,
        company_mail: str | None = None,
        address: str | None = None,
        note: str | None = None,
    ) -> RegistrationSubmitResult:
        normalized_login = login.strip()
        if not 3 <= len(normalized_login) <= 128:
            raise Conflict("Логин должен содержать от 3 до 128 символов")
        try:
            normalized_email = validate_optional_email(email.strip().lower(), allow_placeholder=False)
            normalized_full_name = full_name.strip()
            normalized_phone = validate_ru_phone(phone.strip())
            normalized_company = company_name.strip()
            normalized_inn = validate_inn(inn.strip())
            normalized_company_phone = validate_ru_phone(company_phone.strip())
            normalized_company_mail = (
                validate_optional_email(company_mail.strip().lower(), allow_placeholder=False)
                if company_mail and company_mail.strip()
                else None
            )
        except ValueError as exc:
            raise Conflict(str(exc)) from exc
        if not normalized_email:
            raise Conflict("Укажите email")
        if not normalized_full_name:
            raise Conflict("Укажите ФИО")
        if not normalized_company:
            raise Conflict("Укажите наименование компании")

        try:
            claims = RegistrationInvitationService(self._uow).parse(token)
        except Unauthorized:
            inspect = await RegistrationInvitationService(self._uow).inspect(raw_token=token)
            if inspect.status == "expired":
                raise Unauthorized("Срок действия ссылки истёк") from None
            raise Unauthorized("Ссылка регистрации недействительна") from None
        in_progress = await RegistrationInvitationService(self._uow).load_in_progress_registration(claims.email)

        role_id = claims.role_id
        role_name = technical_role_name(role_id)
        if role_name is None:
            raise Conflict("Роль недоступна для регистрации")

        if in_progress is not None:
            return await self._update_in_progress(
                user=in_progress[0],
                profile=in_progress[1],
                company=in_progress[2],
                role_name=role_name,
                login=normalized_login,
                email=normalized_email,
                full_name=normalized_full_name,
                phone=normalized_phone,
                company_name=normalized_company,
                inn=normalized_inn,
                company_phone=normalized_company_phone,
                company_mail=normalized_company_mail,
                address=address,
                note=note,
            )

        if await self._uow.users.exists(normalized_login):
            raise Conflict("Пользователь уже существует")
        if await self._uow.profiles.exists_by_mail(email=normalized_email):
            raise Conflict("Эта электронная почта уже используется")
        if await self._uow.user_contact_channels.exists_primary_email(email=normalized_email):
            raise Conflict("Эта электронная почта уже используется")

        account_id = stable_iam_account_id(normalized_login)
        account = await self._iam_client.put_account(
            account_id=account_id,
            login=normalized_login,
            role=role_name,
            auth_status="pending",
        )

        user = User(
            id=normalized_login,
            id_role=role_id,
            status="review",
        )
        await self._uow.users.add(user)
        await self._uow.profiles.add(
            Profile(
                id=normalized_login,
                full_name=normalized_full_name,
                phone=normalized_phone,
                mail=normalized_email,
            )
        )
        await self._uow.company_contacts.add(
            CompanyContact(
                id=normalized_login,
                company_name=normalized_company,
                inn=normalized_inn,
                phone=normalized_company_phone,
                mail=normalized_company_mail or PLACEHOLDER_TEXT,
                address=(address or "").strip() or PLACEHOLDER_TEXT,
                note=(note or "").strip() or PLACEHOLDER_TEXT,
            )
        )
        await self._uow.user_contact_channels.upsert_channel(
            user_id=normalized_login,
            channel_type="email",
            channel_value=normalized_email,
            is_verified=False,
            is_primary=True,
        )
        await self._uow.user_auth_accounts.add(
            UserAuthAccount(
                id_user=normalized_login,
                provider="iam",
                external_subject_id=account.id,
                external_username=normalized_login,
                external_email=claims.email,
                is_active=True,
            )
        )
        await AccountRecoveryService(self._uow).request_recovery(identifier=normalized_login)
        schedule_registration_review_required_notification(
            after_commit_hook_registrar=getattr(self._uow, "add_after_commit_hook", None),
            user_id=normalized_login,
            actor_user_id=claims.inviter_id,
            role_id=role_id,
            source="invitation_registration",
        )
        return RegistrationSubmitResult(
            user_id=normalized_login,
            status="review",
            email=normalized_email,
        )

    async def _update_in_progress(
        self,
        *,
        user,
        profile,
        company,
        role_name: str,
        login: str,
        email: str,
        full_name: str,
        phone: str,
        company_name: str,
        inn: str,
        company_phone: str,
        company_mail: str | None,
        address: str | None,
        note: str | None,
    ) -> RegistrationSubmitResult:
        if login != user.id:
            raise Conflict("Логин уже задан для этой регистрации")
        if await self._uow.profiles.exists_by_mail(email=email, exclude_user_id=user.id):
            raise Conflict("Эта электронная почта уже используется")
        if await self._uow.user_contact_channels.exists_primary_email(email=email, exclude_user_id=user.id):
            raise Conflict("Эта электронная почта уже используется")

        binding = await self._uow.user_auth_accounts.get_by_user_provider(
            user_id=user.id,
            provider="iam",
        )
        account_id = binding.external_subject_id if binding is not None else str(stable_iam_account_id(user.id))
        await self._iam_client.put_account(
            account_id=account_id,
            login=user.id,
            role=role_name,
            auth_status="pending",
        )
        if profile is None:
            profile = Profile(id=user.id, full_name=full_name, phone=phone, mail=email)
            await self._uow.profiles.add(profile)
        else:
            profile.full_name = full_name
            profile.phone = phone
            profile.mail = email
        if company is None:
            await self._uow.company_contacts.add(
                CompanyContact(
                    id=user.id,
                    company_name=company_name,
                    inn=inn,
                    phone=company_phone,
                    mail=company_mail or PLACEHOLDER_TEXT,
                    address=(address or "").strip() or PLACEHOLDER_TEXT,
                    note=(note or "").strip() or PLACEHOLDER_TEXT,
                )
            )
        else:
            company.company_name = company_name
            company.inn = inn
            company.phone = company_phone
            company.mail = company_mail or company.mail or PLACEHOLDER_TEXT
            if address is not None and address.strip():
                company.address = address.strip()
            if note is not None and note.strip():
                company.note = note.strip()
        await AccountRecoveryService(self._uow).request_recovery(identifier=user.id)
        return RegistrationSubmitResult(
            user_id=user.id,
            status="review",
            email=email,
        )

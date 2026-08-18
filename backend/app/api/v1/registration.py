from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from app.api.dependencies import get_current_user, get_uow
from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.auth_context import CurrentUser
from app.domain.policies import UserPolicy
from app.infrastructure.email.email_templates.contractor_invitation_email import (
    build_contractor_invitation_email_payload,
)
from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.schemas.registration import (
    RegistrationInspectResponse,
    RegistrationInviteRequest,
    RegistrationInviteResponse,
    RegistrationSubmitRequest,
    RegistrationSubmitResponse,
)
from app.services.registration_invitations import RegistrationInvitationService
from app.services.registration_submit import RegistrationSubmitService

router = APIRouter()


def _registration_url(raw_token: str) -> str:
    base = (settings.web_base_url or "").rstrip("/")
    return f"{base}/register?token={raw_token}"


@router.post("/registration/invitations", response_model=RegistrationInviteResponse)
async def create_registration_invitation(
    payload: RegistrationInviteRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> RegistrationInviteResponse:
    UserPolicy.ensure_can_invite_registration(current_user)
    service = RegistrationInvitationService()
    raw_token = service.create_contractor_invitation(
        current_user=current_user,
        email=payload.email,
        unit_id=payload.unit_id,
    )
    email_payload = build_contractor_invitation_email_payload(
        to_email=payload.email,
        portal_url=_registration_url(raw_token),
        contact_name=settings.invitation_contact_name,
        contact_email=settings.invitation_contact_email,
        contact_phone=settings.invitation_contact_phone,
        contact_text=settings.invitation_contact_text,
    )
    await SMTPEmailService(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        username=settings.email_address,
        password=settings.email_app_password,
        from_address=settings.email_address,
        from_name=settings.email_from_name,
    ).send_email(
        to_email=email_payload.to_email,
        subject=email_payload.subject,
        text_content=email_payload.text_content,
        html_content=email_payload.html_content,
    )
    return RegistrationInviteResponse(
        data={
            "email": payload.email,
            "expires_in_seconds": settings.registration_invite_ttl_seconds,
        }
    )


@router.get("/registration/invitations/{token}", response_model=RegistrationInspectResponse)
async def inspect_registration_invitation(
    token: str = Path(..., min_length=20, max_length=4096),
    uow: UnitOfWork = Depends(get_uow),
) -> RegistrationInspectResponse:
    async with uow:
        result = await RegistrationInvitationService(uow).inspect(raw_token=token)
    return RegistrationInspectResponse(
        data={
            "status": result.status,
            "email": result.email,
            "role_id": result.role_id,
            "expires_at": result.expires_at,
            "login": result.login,
            "full_name": result.full_name,
            "phone": result.phone,
            "company_name": result.company_name,
            "inn": result.inn,
            "company_phone": result.company_phone,
        }
    )


@router.post("/registration/submit", response_model=RegistrationSubmitResponse)
async def submit_registration(
    payload: RegistrationSubmitRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> RegistrationSubmitResponse:
    async with uow:
        result = await RegistrationSubmitService(uow).submit(
            token=payload.token,
            login=payload.login,
            password=payload.password,
            password_confirmation=payload.password_confirmation,
            email=payload.email,
            full_name=payload.full_name,
            phone=payload.phone,
            company_name=payload.company_name,
            inn=payload.inn,
            company_phone=payload.company_phone,
            company_mail=payload.company_mail,
            address=payload.address,
            note=payload.note,
        )
    return RegistrationSubmitResponse(
        data={
            "user_id": result.user_id,
            "status": result.status,
            "email": result.email,
        },
        detail="Регистрация принята. Подтвердите email и дождитесь проверки.",
    )

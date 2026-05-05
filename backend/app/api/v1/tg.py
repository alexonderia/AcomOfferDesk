from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_uow
from app.core.config import settings
from app.core.tg_links import decode_token
from app.core.tg_shortcodes import TgShortcodeCodec
from app.core.uow import UnitOfWork
from app.domain.exceptions import Conflict, Forbidden
from app.schemas.contractor_registration import (
    ContractorEmailVerificationRequest,
    ContractorRegistrationRequest,
    ContractorRegistrationResponse,
    ContractorRegistrationData,
)
from app.schemas.links import Link, LinkSet
from app.schemas.tg_links import TgLinkData, TgLinkRequest, TgLinkResponse
from app.schemas.tg_users import (
    TgStartData,
    TgOpenRequestItem,
    TgStartRequest,
    TgStartResponse,
    TgUserStartRequest,
    TgUserStartResponse,
    TgUserStartData,
)
from app.services.tg_notifications import notify_expired_link, notify_registration_completed
from app.services.tg_registration_links import (
    TgRegistrationLinkExpiredError,
    TgRegistrationLinkInvalidError,
    build_keycloak_registration_link,
    create_tg_registration_token,
    resolve_tg_registration_token,
)
from app.services.tg_start import TgStartService
from app.services.tg_users import TgUserRegistrationService
from app.services.users import ContractorRegistrationService
from app.services.email_verification import EmailVerificationService


def require_telegram_legacy_enabled() -> None:
    if not settings.telegram_legacy_enabled:
        raise Forbidden("Telegram legacy endpoints are disabled")


router = APIRouter(
    prefix="/tg",
    deprecated=True,
    dependencies=[Depends(require_telegram_legacy_enabled)],
)


def _build_registration_link_status_url(reason: str) -> str:
    base_url = (settings.web_base_url or settings.public_backend_base_url or "http://localhost:8080").rstrip("/")
    return f"{base_url}/auth/registration-link-status?reason={reason}"


@router.post("/links/register", response_model=TgLinkResponse)
@router.post("/links/register/", response_model=TgLinkResponse, include_in_schema=False)
async def create_register_link(
    payload: TgLinkRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> TgLinkResponse:
    if not settings.tg_link_secret:
        raise Forbidden("TG links are not configured")
    async with uow:
        # No standalone tg_users table in current schema.
        # Keep a logical "get-or-create" over user_auth_accounts/user_contact_channels only.
        await uow.tg_users.get_or_create(payload.tg_id)

    code = create_tg_registration_token(tg_id=payload.tg_id)
    url = build_keycloak_registration_link(token=code)

    return TgLinkResponse(
        data=TgLinkData(url=url),
        _links=LinkSet(self=Link(href="/api/v1/tg/links/register", method="POST")),
    )


@router.post("/users/start", response_model=TgUserStartResponse)
@router.post("/users/start/", response_model=TgUserStartResponse, include_in_schema=False)
async def register_tg_user(
    payload: TgUserStartRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> TgUserStartResponse:
    async with uow:
        service = TgUserRegistrationService(uow.tg_users)
        tg_user = await service.register(payload.tg_id)

    return TgUserStartResponse(
        data=TgUserStartData(tg_id=tg_user.id, status=tg_user.status),
        _links=LinkSet(
            self=Link(href="/api/v1/tg/users/start", method="POST"),
        ),
    )


@router.post("/start", response_model=TgStartResponse)
@router.post("/start/", response_model=TgStartResponse, include_in_schema=False)
async def handle_tg_start(
    payload: TgStartRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> TgStartResponse:
    async with uow:
        service = TgStartService(uow.tg_users, uow.users, uow.requests)
        result = await service.handle_start(payload.tg_id)

    return TgStartResponse(
        data=TgStartData(
            tg_id=result.tg_user.id,
            tg_status=result.tg_user.status,
            action=result.action,
            registration_link=result.registration_link,
            requests=[
                TgOpenRequestItem(
                    request_id=item.request_id,
                    description=item.description,
                    deadline_at=item.deadline_at,
                    link=item.link,
                )
                for item in result.requests
            ],
            user_status=result.user_status,
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/tg/start", method="POST"),
        ),
    )


@router.post("/register/request-email-verification")
@router.post("/register/request-email-verification/", include_in_schema=False)
async def request_tg_registration_email_verification(
    payload: ContractorEmailVerificationRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, str]:
    tg_id = await resolve_tg_registration_token(payload.token)
    async with uow:
        service = EmailVerificationService(uow.profiles)
        await service.request_tg_registration_verification(
            tg_id=tg_id,
            email=payload.mail.strip(),
            tg_token=payload.token,
        )
    return {"detail": "Письмо для подтверждения email отправлено"}

class TgLoginAvailabilityResponse(BaseModel):
    available: bool
    detail: str


@router.get("/register/login-availability", response_model=TgLoginAvailabilityResponse)
@router.get("/register/login-availability/", response_model=TgLoginAvailabilityResponse, include_in_schema=False)
async def check_tg_registration_login_availability(
    token: str = Query(..., min_length=1),
    login: str = Query(..., min_length=3, max_length=128),
    uow: UnitOfWork = Depends(get_uow),
) -> TgLoginAvailabilityResponse:
    await resolve_tg_registration_token(token)
    normalized_login = login.strip()
    if not normalized_login:
        return TgLoginAvailabilityResponse(available=False, detail="Введите логин")

    async with uow:
        exists = await uow.users.exists(normalized_login)

    if exists:
        return TgLoginAvailabilityResponse(available=False, detail="Логин уже занят")
    return TgLoginAvailabilityResponse(available=True, detail="Логин свободен")


@router.post("/register/complete", response_model=ContractorRegistrationResponse)
@router.post("/register/complete/", response_model=ContractorRegistrationResponse, include_in_schema=False)
async def complete_tg_registration(
    payload: ContractorRegistrationRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> ContractorRegistrationResponse:
    tg_id = await resolve_tg_registration_token(payload.token)
    normalized_mail_raw = payload.mail.strip()
    normalized_mail = "" if normalized_mail_raw in {"", "Не указано"} else normalized_mail_raw

    async with uow:
        service = ContractorRegistrationService(
            uow.users,
            uow.profiles,
            uow.company_contacts,
            uow.user_auth_accounts,
            uow.user_contact_channels,
        )
        user = await service.register_contractor(
            tg_user_id=tg_id,
            login=payload.login.strip(),
            password=payload.password.strip(),
            full_name=payload.full_name.strip(),
            phone=payload.phone.strip(),
            company_name=payload.company_name.strip(),
            inn=payload.inn.strip(),
            company_phone=payload.company_phone.strip(),
            company_mail=payload.company_mail.strip() if payload.company_mail.strip() else "Не указано",
            address=payload.address.strip(),
            note=payload.note.strip(),
        )

    if normalized_mail:
        try:
            async with uow:
                verification_service = EmailVerificationService(uow.profiles)
                await verification_service.request_profile_verification(user_id=user.id, email=normalized_mail)
        except Conflict:
            pass

    await notify_registration_completed(tg_id)

    return ContractorRegistrationResponse(
        data=ContractorRegistrationData(
            user_id=user.id,
            status=user.status,
            tg_user_id=tg_id,
        ),
        _links=LinkSet(
            self=Link(href="/api/v1/tg/register/complete", method="POST"),
        ),
    )


@router.get("/register")
@router.get("/register/", include_in_schema=False)
async def redirect_tg_register(
    token: str = Query(...),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    try:
        tg_id = await resolve_tg_registration_token(token)
    except TgRegistrationLinkExpiredError:
        return RedirectResponse(url=_build_registration_link_status_url("expired"), status_code=302)
    except TgRegistrationLinkInvalidError:
        return RedirectResponse(url=_build_registration_link_status_url("invalid"), status_code=302)

    async with uow:
        linked_user = await uow.users.get_by_tg_user_id(tg_id)
    if linked_user is not None:
        return RedirectResponse(url=_build_registration_link_status_url("already_registered"), status_code=302)
    url = build_keycloak_registration_link(token=token)
    return RedirectResponse(url=url, status_code=302)

@router.get("/auth")
@router.get("/auth/", include_in_schema=False)
async def redirect_tg_auth(
    _token: str = Query(..., alias="token"),
) -> RedirectResponse:
    if not settings.web_base_url:
        raise Forbidden("Invalid token")
    url = f"{settings.web_base_url.rstrip('/')}/login?next=/"
    return RedirectResponse(url=url, status_code=302)

async def resolve_tg_id_from_auth_token(token: str) -> int:
    try:
        token_payload = await _validate_tg_token(token, purpose="tg_auth")
        return token_payload.tg_id
    except Forbidden:
        if not settings.tg_link_secret:
            raise

    try:
        shortcode_payload = TgShortcodeCodec.decode(token, secret=settings.tg_link_secret)
        TgShortcodeCodec.ensure_valid(shortcode_payload)
    except ValueError as exc:
        raise Forbidden("Invalid token") from exc

    if shortcode_payload.purpose != "tg_auth":
        raise Forbidden("Invalid token")

    return shortcode_payload.tg_id


async def _validate_tg_token(token: str, *, purpose: str):
    if not settings.tg_link_secret:
        raise Forbidden("Invalid token")
    try:
        payload = decode_token(token, settings.tg_link_secret)
    except ValueError as exc:
        raise Forbidden("Invalid token") from exc
    if payload.purpose != purpose:
        raise Forbidden("Invalid token")
    if payload.exp < int(time.time()):
        await notify_expired_link(payload.tg_id)
        raise Forbidden("Link expired")
    return payload

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_uow
from app.core.config import settings
from app.core.max_links import decode_max_token
from app.core.max_shortcodes import MaxShortcodeCodec
from app.core.uow import UnitOfWork
from app.domain.exceptions import Forbidden
from app.schemas.max_users import (
    MaxLinkData,
    MaxLinkRequest,
    MaxLinkResponse,
    MaxOpenRequestItem,
    MaxStartRequest,
    MaxStartResponse,
)
from app.services.max_registration_links import (
    MaxRegistrationLinkExpiredError,
    MaxRegistrationLinkInvalidError,
    build_keycloak_max_registration_link,
    create_max_registration_token,
    resolve_max_registration_token,
)
from app.services.max_start import MaxStartService


def require_max_bot_enabled() -> None:
    if not settings.max_bot_enabled:
        raise Forbidden("Доступ к MAX-контуру отключён")


router = APIRouter(
    prefix="/max",
    dependencies=[Depends(require_max_bot_enabled)],
)


def _build_registration_link_status_url(reason: str) -> str:
    base_url = (settings.web_base_url or settings.public_backend_base_url or "http://localhost:8080").rstrip("/")
    return f"{base_url}/auth/registration-link-status?reason={reason}"


@router.post("/start", response_model=MaxStartResponse)
@router.post("/start/", response_model=MaxStartResponse, include_in_schema=False)
async def handle_max_start(
    payload: MaxStartRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> MaxStartResponse:
    async with uow:
        service = MaxStartService(uow.max_users, uow.users, uow.requests)
        result = await service.handle_start(payload.max_user_id)

    return MaxStartResponse(
        action=result.action,  # type: ignore[arg-type]
        registration_url=result.registration_url,
        requests=[
            MaxOpenRequestItem(
                id=item.id,
                description=item.description,
                deadline_at=item.deadline_at,
                url=item.url,
            )
            for item in result.requests
        ],
    )


@router.post("/links/register", response_model=MaxLinkResponse)
@router.post("/links/register/", response_model=MaxLinkResponse, include_in_schema=False)
async def create_register_link(
    payload: MaxLinkRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> MaxLinkResponse:
    if not settings.max_link_secret:
        raise Forbidden("Ссылки MAX не настроены")
    async with uow:
        await uow.max_users.get_or_create(payload.max_user_id)

    code = create_max_registration_token(max_user_id=payload.max_user_id)
    url = build_keycloak_max_registration_link(token=code)

    return MaxLinkResponse(data=MaxLinkData(url=url))


@router.get("/register")
@router.get("/register/", include_in_schema=False)
async def redirect_max_register(
    token: str = Query(...),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    try:
        max_user_id = await resolve_max_registration_token(token)
    except MaxRegistrationLinkExpiredError:
        return RedirectResponse(url=_build_registration_link_status_url("expired"), status_code=302)
    except MaxRegistrationLinkInvalidError:
        return RedirectResponse(url=_build_registration_link_status_url("invalid"), status_code=302)

    async with uow:
        linked_user = await uow.users.get_by_max_user_id(max_user_id)
    if linked_user is not None:
        return RedirectResponse(url=_build_registration_link_status_url("already_registered"), status_code=302)
    url = build_keycloak_max_registration_link(token=token)
    return RedirectResponse(url=url, status_code=302)


@router.get("/auth")
@router.get("/auth/", include_in_schema=False)
async def redirect_max_auth(
    _token: str = Query(..., alias="token"),
) -> RedirectResponse:
    if not settings.web_base_url:
        raise Forbidden("Недействительная ссылка")
    url = f"{settings.web_base_url.rstrip('/')}/login?next=/"
    return RedirectResponse(url=url, status_code=302)


async def resolve_max_user_id_from_auth_token(token: str) -> str:
    try:
        token_payload = await _validate_max_token(token, purpose="max_auth")
        return token_payload.max_user_id
    except Forbidden:
        if not settings.max_link_secret:
            raise

    try:
        shortcode_payload = MaxShortcodeCodec.decode(token, secret=settings.max_link_secret)
        MaxShortcodeCodec.ensure_valid(shortcode_payload)
    except ValueError as exc:
        raise Forbidden("Недействительная ссылка") from exc

    if shortcode_payload.purpose != "max_auth":
        raise Forbidden("Недействительная ссылка")

    return shortcode_payload.max_user_id


async def _validate_max_token(token: str, *, purpose: str):
    if not settings.max_link_secret:
        raise Forbidden("Недействительная ссылка")
    try:
        payload = decode_max_token(token, settings.max_link_secret)
    except ValueError as exc:
        raise Forbidden("Недействительная ссылка") from exc
    if payload.purpose != purpose:
        raise Forbidden("Недействительная ссылка")
    if payload.exp < int(time.time()):
        raise Forbidden("Ссылка истекла")
    return payload

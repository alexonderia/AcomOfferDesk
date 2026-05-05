from __future__ import annotations

import time
from urllib.parse import quote
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.action_flags import serialize_permissions
from app.api.dependencies import get_current_user, get_uow
from app.core.auth_cookies import (
    clear_keycloak_refresh_cookie,
    clear_keycloak_state_cookie,
    set_keycloak_refresh_cookie,
    set_keycloak_state_cookie,
)
from app.core.config import settings
from app.core.oidc_state_tokens import (
    build_keycloak_login_url,
    build_oidc_authorization_start,
    decode_oidc_state_token,
)
from app.core.registration_invite_tokens import (
    RegistrationInviteTokenCodec,
    RegistrationInviteTokenExpiredError,
    RegistrationInviteTokenInvalidError,
)
from app.core.uow import UnitOfWork
from app.domain.auth_context import CurrentUser, build_current_user
from app.domain.exceptions import Conflict, Forbidden, Unauthorized
from app.domain.policies import UserPolicy
from app.models.auth_models import UserAuthAccount
from app.repositories.telegram_compat import telegram_subject_value
from app.schemas.auth import (
    LoginResponse,
    RegisterUserRequest,
    RegisterUserResponse,
)
from app.schemas.links import Link, LinkSet
from app.services.email_verification import EmailVerificationService
from app.services.identity_sync import IdentitySyncService
from app.services.keycloak_oidc import (
    decode_keycloak_access_token,
    exchange_code_for_tokens,
    looks_like_keycloak_token,
    logout_refresh_token,
    refresh_tokens,
)
from app.services.keycloak_admin import KeycloakAdminService
from app.services.tg_registration_links import (
    TgRegistrationLinkExpiredError,
    TgRegistrationLinkInvalidError,
    resolve_tg_registration_token,
)
from app.services.users import UserRegistrationService

router = APIRouter()


class RequestEmailVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)


class EmailVerificationActionResponse(BaseModel):
    detail: str


def _build_auth_links(*, self_href: str) -> LinkSet:
    return LinkSet(
        self=Link(href=self_href, method="POST"),
    )


def _normalize_host_with_port(*, host_value: str, fallback_host: str, forwarded_port: str) -> str:
    candidate = (host_value or fallback_host or "").strip()
    if not candidate:
        return ""

    parsed = urlsplit(f"//{candidate}")
    fallback_parsed = urlsplit(f"//{fallback_host}") if fallback_host else None
    hostname = (parsed.hostname or "").strip()
    port = parsed.port or (fallback_parsed.port if fallback_parsed is not None else None)

    forwarded_port_value = (forwarded_port or "").strip()
    if port is None and forwarded_port_value.isdigit():
        port = int(forwarded_port_value)

    if not hostname:
        return candidate

    display_host = f"[{hostname}]" if ":" in hostname and not hostname.startswith("[") else hostname
    if port is not None:
        return f"{display_host}:{port}"
    return display_host


def _resolve_request_base_url(request: Request) -> str:
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    forwarded_port = (request.headers.get("x-forwarded-port") or "").split(",")[0].strip()
    forwarded_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
    raw_host = (request.headers.get("host") or "").strip() or request.url.netloc
    host = _normalize_host_with_port(
        host_value=forwarded_host,
        fallback_host=raw_host,
        forwarded_port=forwarded_port,
    )
    scheme = forwarded_proto or request.url.scheme or "http"
    configured_public_base = (settings.public_backend_base_url or settings.web_base_url or "").strip().rstrip("/")
    if configured_public_base:
        configured_public = urlsplit(configured_public_base)
        configured_host = (configured_public.netloc or "").strip().lower()
        if configured_host and host.strip().lower() == configured_host:
            scheme = configured_public.scheme or scheme
    if host:
        return f"{scheme}://{host}".rstrip("/")
    return (settings.public_backend_base_url or settings.web_base_url or str(request.base_url)).rstrip("/")


def _resolve_oidc_public_base_url(request: Request) -> str:
    configured_public_base = (settings.public_backend_base_url or settings.web_base_url or "").strip().rstrip("/")
    if configured_public_base:
        return configured_public_base
    return _resolve_request_base_url(request)


def _extract_base_url_from_redirect_uri(redirect_uri: str) -> str:
    parsed = urlsplit(redirect_uri)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return (settings.web_base_url or settings.public_backend_base_url or "http://localhost:8080").rstrip("/")


def _build_registration_link_status_url(base_url: str, *, reason: str) -> str:
    return f"{base_url.rstrip('/')}/auth/registration-link-status?reason={quote(reason, safe='')}"


def _build_login_error_url(base_url: str, *, reason: str) -> str:
    return f"{base_url.rstrip('/')}/login?auth_error={quote(reason, safe='')}"


def _build_login_error_redirect(base_url: str, *, reason: str) -> RedirectResponse:
    response = RedirectResponse(
        url=_build_login_error_url(base_url, reason=reason),
        status_code=status.HTTP_302_FOUND,
    )
    clear_keycloak_state_cookie(response)
    clear_keycloak_refresh_cookie(response)
    return response


def _onboarding_state(status_value: str) -> str | None:
    return None if status_value == "active" else status_value


async def _link_telegram_registration_context(
    *,
    uow: UnitOfWork,
    user_id: str,
    tg_id: int,
) -> None:
    subject = telegram_subject_value(tg_id)
    linked_user = await uow.users.get_by_tg_user_id(tg_id)
    if linked_user is not None and linked_user.id != user_id:
        raise Conflict("Telegram account is already linked to another user")

    telegram_account = await uow.user_auth_accounts.get_by_user_provider(
        user_id=user_id,
        provider="telegram",
        include_inactive=True,
    )
    if telegram_account is None:
        await uow.user_auth_accounts.add(
            UserAuthAccount(
                id_user=user_id,
                provider="telegram",
                external_subject_id=subject,
                external_username=None,
                external_email=None,
                is_active=True,
            )
        )
    else:
        telegram_account.external_subject_id = subject
        telegram_account.is_active = True

    await uow.user_contact_channels.upsert_channel(
        user_id=user_id,
        channel_type="telegram",
        channel_value=subject,
        is_verified=False,
        is_primary=True,
    )


def _build_auth_response(
    *,
    access_token: str,
    access_token_expires_at: int,
    user_id: str,
    role_id: int,
    status_value: str,
    auth_provider: str,
    self_href: str,
) -> LoginResponse:
    current_user = build_current_user(
        user_id=user_id,
        role_id=role_id,
        status=status_value,
    )
    return LoginResponse(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "access_token_expires_at": access_token_expires_at,
            "user_id": user_id,
            "login": user_id,
            "role_id": role_id,
            "status": status_value,
            "auth_provider": auth_provider,
            "business_access": status_value == "active",
            "onboarding_state": _onboarding_state(status_value),
            "permissions": serialize_permissions(current_user),
        },
        _links=_build_auth_links(self_href=self_href),
    )


async def _build_keycloak_auth_response(
    *,
    access_token: str,
    self_href: str,
    uow: UnitOfWork,
) -> LoginResponse:
    claims = await decode_keycloak_access_token(access_token)
    sync_service = IdentitySyncService(
        users=uow.users,
        user_auth_accounts=uow.user_auth_accounts,
        user_contact_channels=uow.user_contact_channels,
        profiles=uow.profiles,
    )
    synced = await sync_service.sync_keycloak_identity(claims, allow_user_creation=False)
    return _build_auth_response(
        access_token=access_token,
        access_token_expires_at=claims.expires_at,
        user_id=synced.user.id,
        role_id=synced.user.id_role,
        status_value=synced.user.status,
        auth_provider="keycloak",
        self_href=self_href,
    )


@router.post("/auth/request-email-verification", response_model=EmailVerificationActionResponse)
async def request_email_verification(
    payload: RequestEmailVerificationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> EmailVerificationActionResponse:
    async with uow:
        service = EmailVerificationService(uow.profiles)
        result = await service.request_profile_verification(user_id=current_user.user_id, email=payload.email)

    if result == "same_email":
        return EmailVerificationActionResponse(
            detail="РЈРєР°Р·Р°РЅ С‚РµРєСѓС‰РёР№ РїРѕРґС‚РІРµСЂР¶РґС‘РЅРЅС‹Р№ email"
        )
    if result == "already_sent":
        return EmailVerificationActionResponse(
            detail="РџРёСЃСЊРјРѕ СѓР¶Рµ РѕС‚РїСЂР°РІР»РµРЅРѕ. РџСЂРѕРІРµСЂСЊС‚Рµ РІР°С€Сѓ РїРѕС‡С‚Сѓ"
        )
    return EmailVerificationActionResponse(
        detail="РџРёСЃСЊРјРѕ РґР»СЏ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ email РѕС‚РїСЂР°РІР»РµРЅРѕ"
    )


@router.get("/auth/verify-email", response_model=EmailVerificationActionResponse)
async def verify_email(
    token: str = Query(..., min_length=20),
    uow: UnitOfWork = Depends(get_uow),
) -> EmailVerificationActionResponse:
    async with uow:
        service = EmailVerificationService(uow.profiles)
        updated = await service.confirm_profile_verification(token=token)

    if updated:
        return EmailVerificationActionResponse(detail="Email РїРѕРґС‚РІРµСЂР¶РґС‘РЅ")
    return EmailVerificationActionResponse(detail="Email СѓР¶Рµ РїРѕРґС‚РІРµСЂР¶РґС‘РЅ")


@router.get("/auth/oidc/login", response_class=RedirectResponse)
async def begin_keycloak_login(
    request: Request,
    next_path: str | None = Query(default="/"),
    force_prompt: bool = Query(default=False),
) -> RedirectResponse:
    if not settings.keycloak_enabled:
        raise Forbidden("Keycloak authentication is disabled")

    redirect_uri = f"{_resolve_oidc_public_base_url(request)}/api/v1/auth/callback"
    start = build_oidc_authorization_start(next_path=next_path, flow="login", redirect_uri=redirect_uri)
    response = RedirectResponse(
        url=build_keycloak_login_url(
            state=start.state,
            code_challenge=start.code_challenge,
            redirect_uri=start.redirect_uri,
            prompt="login" if force_prompt else None,
        ),
        status_code=status.HTTP_302_FOUND,
    )
    set_keycloak_state_cookie(
        response,
        start.cookie_token,
        max_age=max(0, start.expires_at - int(time.time())),
    )
    return response


@router.get("/auth/oidc/register", response_class=RedirectResponse)
async def begin_keycloak_registration(
    request: Request,
    next_path: str | None = Query(default="/account"),
    tg_token: str | None = Query(default=None),
    invite_token: str | None = Query(default=None),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    if not settings.keycloak_enabled:
        raise Forbidden("Keycloak authentication is disabled")

    redirect_uri = f"{_resolve_oidc_public_base_url(request)}/api/v1/auth/callback"
    web_base = _extract_base_url_from_redirect_uri(redirect_uri)
    tg_registration_id: int | None = None
    registration_email: str | None = None

    if tg_token and invite_token:
        return RedirectResponse(
            url=_build_registration_link_status_url(web_base, reason="invalid"),
            status_code=status.HTTP_302_FOUND,
        )

    if tg_token:
        if not settings.telegram_legacy_enabled:
            return RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason="invalid"),
                status_code=status.HTTP_302_FOUND,
            )
        try:
            tg_registration_id = await resolve_tg_registration_token(tg_token)
        except TgRegistrationLinkExpiredError:
            return RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason="expired"),
                status_code=status.HTTP_302_FOUND,
            )
        except TgRegistrationLinkInvalidError:
            return RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason="invalid"),
                status_code=status.HTTP_302_FOUND,
            )

        async with uow:
            linked_user = await uow.users.get_by_tg_user_id(tg_registration_id)
        if linked_user is not None:
            return RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason="already_registered"),
                status_code=status.HTTP_302_FOUND,
            )
    elif invite_token:
        invite_codec = RegistrationInviteTokenCodec(
            secret=settings.email_verification_secret,
            ttl_seconds=settings.tg_register_ttl_seconds,
        )
        try:
            invite_claims = invite_codec.parse_token(invite_token)
        except RegistrationInviteTokenExpiredError:
            return RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason="expired"),
                status_code=status.HTTP_302_FOUND,
            )
        except RegistrationInviteTokenInvalidError:
            return RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason="invalid"),
                status_code=status.HTTP_302_FOUND,
            )

        registration_email = invite_claims.email
        async with uow:
            existing_users = await uow.users.list_by_email(email=registration_email)
        if existing_users:
            return RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason="already_registered"),
                status_code=status.HTTP_302_FOUND,
            )
    else:
        return RedirectResponse(
            url=_build_registration_link_status_url(web_base, reason="invalid"),
            status_code=status.HTTP_302_FOUND,
        )

    start = build_oidc_authorization_start(
        next_path=next_path,
        flow="register",
        redirect_uri=redirect_uri,
        tg_registration_id=tg_registration_id,
        registration_email=registration_email,
    )
    response = RedirectResponse(
        url=build_keycloak_login_url(
            state=start.state,
            code_challenge=start.code_challenge,
            redirect_uri=start.redirect_uri,
            prompt="create",
        ),
        status_code=status.HTTP_302_FOUND,
    )
    set_keycloak_state_cookie(
        response,
        start.cookie_token,
        max_age=max(0, start.expires_at - int(time.time())),
    )
    return response


@router.get("/auth/callback", response_class=RedirectResponse, response_model=None)
async def keycloak_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    uow: UnitOfWork = Depends(get_uow),
) -> RedirectResponse:
    if not settings.keycloak_enabled:
        raise Forbidden("Keycloak authentication is disabled")
    request_base = _resolve_oidc_public_base_url(request)
    if error:
        return _build_login_error_redirect(request_base, reason="access_denied")
    if not code or not state:
        return _build_login_error_redirect(request_base, reason="session_expired")

    state_cookie = (request.cookies.get(settings.keycloak_state_cookie_name) or "").strip()
    if not state_cookie:
        return _build_login_error_redirect(request_base, reason="session_expired")

    try:
        claims = decode_oidc_state_token(state_cookie)
    except Unauthorized:
        return _build_login_error_redirect(request_base, reason="session_expired")
    if claims.state != state:
        return _build_login_error_redirect(request_base, reason="session_expired")

    try:
        bundle = await exchange_code_for_tokens(
            code=code,
            code_verifier=claims.code_verifier,
            redirect_uri=claims.redirect_uri,
        )
    except Unauthorized:
        return _build_login_error_redirect(request_base, reason="login_failed")
    web_base = _extract_base_url_from_redirect_uri(claims.redirect_uri)
    try:
        async with uow:
            token_claims = await decode_keycloak_access_token(bundle.access_token)
            if claims.registration_email is not None:
                normalized_invite_email = claims.registration_email.strip().lower()
                normalized_token_email = (token_claims.email or "").strip().lower()
                if not normalized_token_email or normalized_token_email != normalized_invite_email:
                    raise Forbidden("Registration invite email mismatch")

                existing_users = await uow.users.list_by_email(email=normalized_invite_email)
                if existing_users:
                    raise Conflict("Registration already completed")

            sync_service = IdentitySyncService(
                users=uow.users,
                user_auth_accounts=uow.user_auth_accounts,
                user_contact_channels=uow.user_contact_channels,
                profiles=uow.profiles,
            )
            synced = await sync_service.sync_keycloak_identity(
                token_claims,
                allow_user_creation=claims.flow == "register",
            )
            if claims.tg_registration_id is not None:
                if not settings.telegram_legacy_enabled:
                    raise Forbidden("Telegram legacy authentication is disabled")
                await _link_telegram_registration_context(
                    uow=uow,
                    user_id=synced.user.id,
                    tg_id=claims.tg_registration_id,
                )
    except (Forbidden, Conflict) as exc:
        if claims.tg_registration_id is not None or claims.registration_email is not None:
            reason = "already_registered" if isinstance(exc, Conflict) else "invalid"
            response = RedirectResponse(
                url=_build_registration_link_status_url(web_base, reason=reason),
                status_code=status.HTTP_302_FOUND,
            )
        else:
            response = RedirectResponse(url=f"{web_base}/auth/callback?error=not_linked", status_code=status.HTTP_302_FOUND)
        clear_keycloak_state_cookie(response)
        clear_keycloak_refresh_cookie(response)
        return response

    redirect_target = f"{web_base}/auth/callback?next={quote(claims.next_path, safe='/%?=&')}"
    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_302_FOUND)
    clear_keycloak_state_cookie(response)
    set_keycloak_refresh_cookie(response, bundle.refresh_token, max_age=max(0, bundle.refresh_expires_in))
    return response


@router.post("/auth/refresh", response_model=LoginResponse)
async def refresh_session(
    request: Request,
    response: Response,
    uow: UnitOfWork = Depends(get_uow),
) -> LoginResponse:
    if not settings.keycloak_enabled:
        raise Unauthorized("Missing credentials")

    keycloak_refresh_token = (request.cookies.get(settings.keycloak_refresh_cookie_name) or "").strip()
    if not keycloak_refresh_token:
        raise Unauthorized("Missing credentials")
    try:
        bundle = await refresh_tokens(refresh_token=keycloak_refresh_token)
    except Unauthorized:
        clear_keycloak_refresh_cookie(response)
        raise Unauthorized("Missing credentials")

    set_keycloak_refresh_cookie(response, bundle.refresh_token, max_age=max(0, bundle.refresh_expires_in))
    async with uow:
        return await _build_keycloak_auth_response(
            access_token=bundle.access_token,
            self_href="/api/v1/auth/refresh",
            uow=uow,
        )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> Response:
    keycloak_refresh_token = (request.cookies.get(settings.keycloak_refresh_cookie_name) or "").strip()
    keycloak_user_id: str | None = None

    authorization = (request.headers.get("Authorization") or "").strip()
    if authorization.startswith("Bearer "):
        bearer_token = authorization.removeprefix("Bearer ").strip()
        if bearer_token and looks_like_keycloak_token(bearer_token):
            try:
                claims = await decode_keycloak_access_token(bearer_token)
                keycloak_user_id = claims.subject
            except Unauthorized:
                keycloak_user_id = None

    if settings.keycloak_enabled and keycloak_refresh_token:
        try:
            await logout_refresh_token(refresh_token=keycloak_refresh_token)
        except Forbidden:
            # Local logout must succeed even if provider is temporarily unavailable.
            pass

    if settings.keycloak_enabled and keycloak_user_id:
        try:
            await KeycloakAdminService().logout_user_sessions(user_id=keycloak_user_id)
        except Conflict:
            # Local logout must succeed even if admin API is temporarily unavailable.
            pass

    clear_keycloak_state_cookie(response)
    clear_keycloak_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/auth/tg/exchange", deprecated=True)
async def tg_exchange_disabled() -> dict[str, str]:
    raise Forbidden("Telegram legacy authentication is disabled")


@router.post("/users/register", response_model=RegisterUserResponse)
async def register_user(
    payload: RegisterUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RegisterUserResponse:
    UserPolicy.ensure_can_register_user(current_user)
    async with uow:
        service = UserRegistrationService(uow.users, uow.profiles, uow.user_auth_accounts)
        user = await service.register_user(
            current_user,
            user_id=payload.login.strip(),
            password=payload.password.strip() if payload.password else None,
            role_id=payload.role_id,
            id_parent=payload.id_parent.strip() if payload.id_parent else None,
            full_name=payload.full_name.strip() if payload.full_name else None,
            phone=payload.phone.strip() if payload.phone else None,
            mail=payload.mail.strip() if payload.mail else None,
        )
    return RegisterUserResponse(
        data={
            "user_id": user.id,
            "role_id": user.id_role,
            "status": user.status,
        },
        _links=LinkSet(
            self=Link(href=f"/api/v1/users/{user.id}", method="GET"),
        ),
    )



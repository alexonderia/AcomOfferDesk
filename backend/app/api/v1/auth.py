from __future__ import annotations

import hmac
import secrets
import time
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from shared.client_ip import resolve_client_ip
from shared.rate_limiter import SlidingWindowRateLimiter

from app.api.dependencies import get_current_user, get_uow, resolve_iam_current_user
from app.core.auth_cookies import (
    clear_csrf_cookie,
    clear_iam_browser_session_cookie,
    clear_iam_access_cookie,
    clear_iam_flow_cookie,
    clear_iam_flow_recovery_cookie,
    clear_iam_refresh_cookie,
    set_csrf_cookie,
    set_iam_access_cookie,
    set_iam_flow_cookie,
    set_iam_flow_recovery_cookie,
    set_iam_refresh_cookie,
)
from app.core.config import settings
from app.core.email_mode import ensure_email_enabled
from app.core.iam_flow import FLOW_TTL_SECONDS, build_iam_authorize_url, create_iam_flow, decode_iam_flow
from app.core.uow import UnitOfWork
from app.domain.authentication import decode_iam_access_token
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import AuthenticationUnavailable, Conflict, Forbidden, NotFound, Unauthorized
from app.domain.iam_roles import technical_role_name
from app.domain.policies import UserPolicy
from app.infrastructure.iam_client import IamClient
from app.services.iam_bindings import ensure_user_iam_account
from app.schemas.auth import AuthSessionData, AuthSessionResponse, RegisterUserRequest, RegisterUserResponse
from app.schemas.auth import PasswordChangeRequest
from app.services.account_recovery import AccountRecoveryService, GENERIC_RECOVERY_DETAIL
from app.services.email_verification import FIRST_ACCESS_PURPOSE, EmailVerificationService
from app.services.unit_hierarchy import UnitHierarchyService
from app.services.units import UnitService
from app.services.users import UserRegistrationService


router = APIRouter()
# This route intentionally lives below /iam so a browser can accept a deletion
# for the path-scoped IAM UI cookie. It is served by Acom's backend, not IAM.
iam_bff_router = APIRouter()
MAX_PASSWORD_RESET_RATE_LIMIT_BUCKETS = 10_000


class RequestEmailVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)


class EmailVerificationActionResponse(BaseModel):
    detail: str
    next_action: str | None = None
    redirect_url: str | None = None


class CsrfResponse(BaseModel):
    csrf_token: str


class PasswordResetRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=255)


class PasswordResetResponse(BaseModel):
    detail: str


class PasswordResetRateLimiter:
    def __init__(
        self,
        *,
        attempts: int = 5,
        window_seconds: int = 900,
        max_buckets: int = MAX_PASSWORD_RESET_RATE_LIMIT_BUCKETS,
    ) -> None:
        self._ip_limiter = SlidingWindowRateLimiter(
            attempts=attempts,
            window_seconds=window_seconds,
            max_buckets=max_buckets,
        )
        self._login_limiter = SlidingWindowRateLimiter(
            attempts=attempts,
            window_seconds=window_seconds,
            max_buckets=max_buckets,
        )

    @property
    def bucket_count(self) -> int:
        return self._ip_limiter.bucket_count + self._login_limiter.bucket_count

    async def allow(self, *, client_ip: str, login: str) -> bool:
        normalized_login = login.strip().casefold()
        if not await self._ip_limiter.allow(client_ip):
            return False
        return await self._login_limiter.allow(normalized_login)


password_reset_rate_limiter = PasswordResetRateLimiter()
password_change_rate_limiter = PasswordResetRateLimiter()


@router.get("/auth/capabilities")
async def app_capabilities(response: Response) -> dict:
    response.headers["Cache-Control"] = "no-store"
    return {"data": {"email_enabled": settings.email_enabled, "direct_user_creation": not settings.email_enabled, "password_change": True}}


@router.post("/users/me/password", status_code=204)
async def change_my_password(
    payload: PasswordChangeRequest, request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> Response:
    if current_user.status != "active":
        raise Forbidden("Смена пароля доступна только активному пользователю")
    if not await password_change_rate_limiter.allow(client_ip=_client_ip(request), login=current_user.iam_account_id):
        return JSONResponse(status_code=429, content={"detail": "Слишком много попыток. Повторите позже"})
    await IamClient().change_own_password(
        account_id=current_user.iam_account_id, session_id=current_user.iam_session_id,
        current_password=payload.current_password.get_secret_value(),
        new_password=payload.new_password.get_secret_value(),
    )
    response = Response(status_code=204)
    clear_iam_access_cookie(response)
    clear_iam_refresh_cookie(response)
    clear_iam_browser_session_cookie(response)
    clear_csrf_cookie(response)
    return response


def _client_ip(request: Request) -> str:
    return (
        resolve_client_ip(
            peer_host=request.client.host if request.client else None,
            forwarded_for=request.headers.get("x-forwarded-for"),
            real_ip=request.headers.get("x-real-ip"),
            trusted_proxy_cidrs=settings.trusted_proxy_cidrs,
        )
        or "unknown"
    )


def _session_response(current_user: CurrentUser) -> AuthSessionResponse:
    onboarding_state = current_user.onboarding_state
    if onboarding_state != "first_login" and current_user.status == "review":
        onboarding_state = "review"
    if onboarding_state == "completed":
        onboarding_state = None
    return AuthSessionResponse(
        data=AuthSessionData(
            user_id=current_user.user_id,
            login=current_user.user_id,
            role_id=current_user.role_id,
            role=current_user.system_role,
            status=current_user.status,
            auth_provider="iam",
            business_access=current_user.status == "active" and current_user.onboarding_state != "first_login",
            onboarding_state=onboarding_state,
            permissions=sorted(current_user.permissions),
            email_enabled=settings.email_enabled,
        )
    )


def _set_session_cookies(response: Response, bundle) -> None:
    now = int(time.time())
    set_iam_access_cookie(
        response,
        bundle.access_token,
        max_age=max(1, bundle.access_token_expires_at - now),
    )
    set_iam_refresh_cookie(
        response,
        bundle.refresh_token,
        max_age=max(1, bundle.refresh_token_expires_at - now),
    )
    set_csrf_cookie(response, secrets.token_urlsafe(32), max_age=max(1, bundle.refresh_token_expires_at - now))


def _clear_session_cookies(response: Response) -> None:
    clear_iam_access_cookie(response)
    clear_iam_refresh_cookie(response)
    clear_csrf_cookie(response)


def _password_action_name(action: str) -> str:
    if action not in {"setup", "reset"}:
        raise NotFound("Password action not found")
    return action


async def _proxy_password_action_page(
    *,
    action: str,
    token: str | None = None,
    form: dict[str, str] | None = None,
) -> HTMLResponse:
    page = await IamClient().render_password_action_page(
        action=_password_action_name(action),
        token=token,
        form=form,
    )
    body = page.html.replace(
        f'action="/iam/password/{action}"',
        f'action="/api/v1/auth/password/{action}"',
    )
    response = HTMLResponse(content=body, status_code=page.status_code)
    response.headers["Cache-Control"] = "no-store"
    return response


def _restart_iam_login(*, error: str) -> RedirectResponse:
    location = f"{settings.resolved_iam_public_base_url}/login?{urlencode({'error': error})}"
    response = RedirectResponse(location, status_code=303)
    clear_iam_flow_cookie(response)
    clear_iam_flow_recovery_cookie(response)
    return response


def _retry_expired_iam_flow(request: Request) -> RedirectResponse:
    if request.cookies.get(settings.iam_flow_recovery_cookie_name) == "1":
        return _restart_iam_login(error="session_expired")
    response = RedirectResponse("/api/v1/auth/login", status_code=303)
    clear_iam_flow_cookie(response)
    set_iam_flow_recovery_cookie(response)
    return response


@router.get("/auth/login")
async def begin_login(next: str | None = Query(default=None)) -> RedirectResponse:
    flow = create_iam_flow(next)
    response = RedirectResponse(build_iam_authorize_url(flow), status_code=302)
    set_iam_flow_cookie(response, flow.cookie_token, max_age=FLOW_TTL_SECONDS)
    return response


@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str = Query(min_length=20, max_length=512),
    state: str = Query(min_length=16, max_length=512),
) -> RedirectResponse:
    bundle = None
    try:
        flow = decode_iam_flow(request.cookies.get(settings.iam_state_cookie_name, ""))
        if not hmac.compare_digest(flow.state, state):
            raise Unauthorized("Invalid IAM state")
        bundle = await IamClient().exchange_code(
            code=code,
            verifier=flow.verifier,
            redirect_uri=flow.redirect_uri,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        await resolve_iam_current_user(decode_iam_access_token(bundle.access_token))
    except Unauthorized:
        if bundle is not None:
            try:
                await IamClient().logout(bundle.refresh_token, reason="acom_identity_rejected")
            except (AuthenticationUnavailable, Unauthorized):
                pass
        return _retry_expired_iam_flow(request)
    except AuthenticationUnavailable:
        return _restart_iam_login(error="service_unavailable")
    response = RedirectResponse(flow.next_path, status_code=303)
    _set_session_cookies(response, bundle)
    clear_iam_flow_cookie(response)
    clear_iam_flow_recovery_cookie(response)
    return response


@router.get("/auth/session", response_model=AuthSessionResponse)
async def get_session(current_user: CurrentUser = Depends(get_current_user)) -> AuthSessionResponse:
    return _session_response(current_user)


@router.get("/auth/csrf", response_model=CsrfResponse)
async def issue_csrf(response: Response) -> CsrfResponse:
    token = secrets.token_urlsafe(32)
    set_csrf_cookie(response, token, max_age=43200)
    return CsrfResponse(csrf_token=token)


@router.post("/auth/refresh", response_model=AuthSessionResponse)
async def refresh_session(request: Request, response: Response) -> AuthSessionResponse | JSONResponse:
    raw_refresh = request.cookies.get(settings.iam_refresh_cookie_name, "").strip()
    if not raw_refresh:
        raise Unauthorized("Missing credentials")
    try:
        bundle = await IamClient().refresh(raw_refresh)
        current_user = await resolve_iam_current_user(decode_iam_access_token(bundle.access_token))
    except Unauthorized:
        error_response = JSONResponse(status_code=401, content={"detail": "Сессия истекла. Войдите снова."})
        _clear_session_cookies(error_response)
        return error_response
    _set_session_cookies(response, bundle)
    return _session_response(current_user)


@router.post("/auth/logout", status_code=204)
async def logout_session(request: Request) -> Response:
    response = Response(status_code=204)
    raw_refresh = request.cookies.get(settings.iam_refresh_cookie_name, "").strip()
    if raw_refresh:
        try:
            await IamClient().logout(raw_refresh)
        except Unauthorized:
            pass
        except AuthenticationUnavailable:
            response = JSONResponse(
                status_code=503,
                content={
                    "detail": "Сервис авторизации временно недоступен.",
                    "reason_code": "AUTH_SERVICE_UNAVAILABLE",
                },
            )
    _clear_session_cookies(response)
    return response


@iam_bff_router.post("/iam/acom/logout", status_code=204)
async def clear_iam_browser_session() -> Response:
    """Clear the path-scoped IAM UI cookie after BFF logout."""
    response = Response(status_code=204)
    clear_iam_browser_session_cookie(response)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/auth/password/{action}", response_class=HTMLResponse)
async def password_action_page(
    action: str,
    token: str = Query(min_length=20, max_length=512),
) -> HTMLResponse:
    return await _proxy_password_action_page(action=action, token=token)


@router.post("/auth/password/{action}", response_class=HTMLResponse)
async def submit_password_action(request: Request, action: str) -> HTMLResponse:
    submitted = await request.form()
    form = {
        field: str(submitted.get(field) or "")
        for field in ("token", "new_password", "password_confirmation")
    }
    return await _proxy_password_action_page(action=action, form=form)


@router.post(
    "/auth/password-reset/request",
    response_model=PasswordResetResponse,
    status_code=202,
)
async def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
) -> PasswordResetResponse:
    ensure_email_enabled()
    generic_detail = GENERIC_RECOVERY_DETAIL
    normalized_login = payload.login.strip()
    client_ip = _client_ip(request)
    if not await password_reset_rate_limiter.allow(
        client_ip=client_ip,
        login=normalized_login,
    ):
        return PasswordResetResponse(detail=generic_detail)

    async with uow:
        result = await AccountRecoveryService(uow).request_recovery(identifier=normalized_login)
    return PasswordResetResponse(detail=result.detail)


@router.post("/auth/request-email-verification", response_model=EmailVerificationActionResponse)
async def request_email_verification(
    payload: RequestEmailVerificationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> EmailVerificationActionResponse:
    ensure_email_enabled()
    UserPolicy.ensure_can_manage_own_profile(current_user)
    async with uow:
        service = EmailVerificationService(
            uow.profiles,
            uow.user_contact_channels,
            user_auth_accounts=uow.user_auth_accounts,
        )
        result = await service.request_profile_verification(
            user_id=current_user.user_id,
            email=payload.email,
            purpose="profile_change",
        )

    if result == "same_email":
        return EmailVerificationActionResponse(detail="Указан текущий подтверждённый email")
    if result == "already_sent":
        return EmailVerificationActionResponse(detail="Письмо уже отправлено. Проверьте вашу почту")
    return EmailVerificationActionResponse(detail="Письмо для подтверждения email отправлено")


@router.get("/auth/verify-email", response_model=EmailVerificationActionResponse)
async def verify_email(
    token: str = Query(..., min_length=20),
    uow: UnitOfWork = Depends(get_uow),
) -> EmailVerificationActionResponse:
    async with uow:
        service = EmailVerificationService(
            uow.profiles,
            uow.user_contact_channels,
            user_auth_accounts=uow.user_auth_accounts,
        )
        result = await service.confirm_profile_verification(token=token)
        next_action = result.next_action
        redirect_url = result.redirect_url
        if result.purpose == FIRST_ACCESS_PURPOSE:
            from app.services.account_recovery import AccountRecoveryService

            redirect_url = await AccountRecoveryService(uow).issue_setup_after_verified_access(
                user_id=result.user_id,
                email=result.email,
            )
            next_action = "password_setup"
        else:
            user = await uow.users.get_by_id(result.user_id)
            if user is not None and user.status == "review":
                next_action = "waiting_for_review"
            elif result.purpose == "profile_change":
                next_action = "login"
            else:
                next_action = "first_login"
    return EmailVerificationActionResponse(
        detail="Email подтверждён" if result.updated else "Email уже подтверждён",
        next_action=next_action,
        redirect_url=redirect_url,
    )


@router.post("/users/register", response_model=RegisterUserResponse)
async def register_user(
    payload: RegisterUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RegisterUserResponse:
    UserPolicy.ensure_can_register_user(current_user)
    if not settings.email_enabled and payload.password is None:
        raise Conflict("Для создания пользователя без почты задайте пароль и его подтверждение")
    if settings.email_enabled and payload.password is not None:
        raise Conflict("Начальный пароль задаётся при создании в режиме без почты")
    iam_client = IamClient()
    normalized_login = payload.login.strip()
    role_name = technical_role_name(payload.role_id)
    if role_name is None:
        raise Conflict("Invalid role")
    async with uow:
        user = await uow.users.get_by_id(normalized_login)
        binding = await uow.user_auth_accounts.get_by_user_provider(
            user_id=normalized_login,
            provider="iam",
            include_inactive=True,
        )
        if user is not None and user.id_role != payload.role_id:
            raise Conflict("Existing user has a different role")
        is_new_user = user is None
        if user is not None:
            await UserRegistrationService(uow.users, uow.profiles, uow.user_auth_accounts).ensure_registration_role(current_user, payload.role_id)
        if not settings.email_enabled and user is not None:
            if binding is None or user.status != "active":
                raise Conflict("Логин уже занят. Создание не изменяет существующую учётную запись")
            allowed_ids = await UnitHierarchyService(uow.users).get_visible_user_ids(current_user=current_user)
            if allowed_ids is not None and user.id not in allowed_ids:
                raise Forbidden("Пользователь находится вне разрешённой области")
        if user is None:
            service = UserRegistrationService(uow.users, uow.profiles, uow.user_auth_accounts)
            user = await service.register_user(
                current_user,
                user_id=normalized_login,
                role_id=payload.role_id,
                id_parent=payload.id_parent.strip() if payload.id_parent else None,
                full_name=payload.full_name.strip() if payload.full_name else None,
                phone=payload.phone.strip() if payload.phone else None,
                mail=payload.mail.strip() if payload.mail else None,
            )
        delivery_email = (payload.mail or "").strip().lower()
        if delivery_email and is_new_user:
            await uow.user_contact_channels.upsert_channel(
                user_id=user.id,
                channel_type="email",
                channel_value=delivery_email,
                is_verified=False,
                is_primary=True,
            )
        unit_service = UnitService(uow.units, uow.users)
        if not is_new_user and not settings.email_enabled:
            pass
        elif payload.unit_id is not None:
            # A new employee is not visible through memberships yet. The
            # registration operation validates the lead's chosen unit directly.
            is_new_lead_registration = is_new_user and current_user.role_id == settings.lead_economist_role_id
            if UserPolicy.can_manage_unit_members(current_user) and not is_new_lead_registration:
                await unit_service.add_member(current_user=current_user, unit_id=payload.unit_id, user_id=user.id)
            else:
                await unit_service.add_member_on_registration(
                    current_user=current_user, unit_id=payload.unit_id, user_id=user.id
                )
        else:
            hierarchy = UnitHierarchyService(uow.users)
            seed_unit_ids = await hierarchy.get_management_seed_unit_ids(user_id=current_user.user_id)
            for seed_unit_id in sorted(seed_unit_ids):
                await unit_service.add_member_on_registration(
                    current_user=current_user, unit_id=seed_unit_id, user_id=user.id
                )

        await ensure_user_iam_account(
            user_auth_accounts=uow.user_auth_accounts, user_id=user.id,
            role_id=user.id_role, user_status=user.status, email=payload.mail,
            initial_password=payload.password.get_secret_value() if payload.password is not None else None,
            is_new_user=is_new_user, iam_client=iam_client,
        )

        visible_ids = await UnitHierarchyService(uow.users).get_visible_user_ids(current_user=current_user)
        visible_to_creator = visible_ids is None or user.id in visible_ids

    return RegisterUserResponse(
        data={"user_id": user.id, "role_id": user.id_role, "status": user.status,
              "visible_to_creator": visible_to_creator}
    )

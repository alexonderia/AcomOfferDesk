from __future__ import annotations

import asyncio
import hmac
import secrets
import time
from collections import defaultdict, deque
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_uow, resolve_iam_current_user
from app.core.auth_cookies import (
    clear_csrf_cookie,
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
from app.core.iam_flow import FLOW_TTL_SECONDS, build_iam_authorize_url, create_iam_flow, decode_iam_flow
from app.core.uow import UnitOfWork
from app.domain.authentication import decode_iam_access_token, reject_unavailable_authentication
from app.domain.auth_context import CurrentUser
from app.domain.contractor_validation import validate_optional_email
from app.domain.exceptions import AuthenticationUnavailable, Conflict, Unauthorized
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.domain.policies import UserPolicy
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount
from app.schemas.auth import AuthSessionData, AuthSessionResponse, RegisterUserRequest, RegisterUserResponse
from app.services.email_verification import EmailVerificationService
from app.services.iam_password_actions import (
    send_iam_password_action_email,
    send_iam_password_action_email_safely,
)
from app.services.unit_hierarchy import UnitHierarchyService
from app.services.units import UnitService
from app.services.users import UserRegistrationService


router = APIRouter()


class RequestEmailVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)


class EmailVerificationActionResponse(BaseModel):
    detail: str


class CsrfResponse(BaseModel):
    csrf_token: str


class PasswordResetRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=128)


class PasswordResetResponse(BaseModel):
    detail: str


class PasswordResetRateLimiter:
    def __init__(self, *, attempts: int = 5, window_seconds: int = 900) -> None:
        self._limit = attempts
        self._window = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self._window
        async with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= self._limit:
                return False
            attempts.append(now)
            return True


password_reset_rate_limiter = PasswordResetRateLimiter()


def _session_response(current_user: CurrentUser) -> AuthSessionResponse:
    return AuthSessionResponse(
        data=AuthSessionData(
            user_id=current_user.user_id,
            login=current_user.user_id,
            role_id=current_user.role_id,
            role=current_user.system_role,
            status=current_user.status,
            auth_provider="iam",
            business_access=current_user.status == "active",
            onboarding_state="review" if current_user.status == "review" else None,
            permissions=sorted(current_user.permissions),
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
            ip_address=request.client.host if request.client else None,
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
    generic_detail = "Если учётная запись существует, инструкция отправлена на подтверждённый email."
    normalized_login = payload.login.strip()
    client_ip = request.client.host if request.client else "unknown"
    if not await password_reset_rate_limiter.allow(f"{client_ip}:{normalized_login.casefold()}"):
        return PasswordResetResponse(detail=generic_detail)

    async with uow:
        user = await uow.users.get_by_id(normalized_login)
        if user is None:
            return PasswordResetResponse(detail=generic_detail)
        profile = await uow.profiles.get_by_id(user.id)
        try:
            delivery_email = validate_optional_email(
                (profile.mail if profile else "") or "",
                allow_placeholder=False,
            )
        except ValueError:
            return PasswordResetResponse(detail=generic_detail)
        if delivery_email is None:
            return PasswordResetResponse(detail=generic_detail)
        binding = await uow.user_auth_accounts.get_by_user_provider(
            user_id=user.id,
            provider="iam",
        )
        if binding is None:
            return PasswordResetResponse(detail=generic_detail)
        action = await IamClient().create_action_token(
            account_id=binding.external_subject_id,
            purpose="password_reset",
        )
        uow.add_after_commit_hook(
            lambda: send_iam_password_action_email_safely(
                to_email=delivery_email,
                raw_token=action.token,
                purpose="password_reset",
            )
        )
    return PasswordResetResponse(detail=generic_detail)


@router.get("/auth/oidc/login")
@router.get("/auth/oidc/register")
async def unavailable_legacy_authentication_flow() -> None:
    reject_unavailable_authentication()


@router.post("/auth/request-email-verification", response_model=EmailVerificationActionResponse)
async def request_email_verification(
    payload: RequestEmailVerificationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> EmailVerificationActionResponse:
    UserPolicy.ensure_can_manage_own_profile(current_user)
    async with uow:
        service = EmailVerificationService(uow.profiles, uow.user_contact_channels)
        result = await service.request_profile_verification(user_id=current_user.user_id, email=payload.email)

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
        service = EmailVerificationService(uow.profiles, uow.user_contact_channels)
        updated = await service.confirm_profile_verification(token=token)
    return EmailVerificationActionResponse(detail="Email подтверждён" if updated else "Email уже подтверждён")


@router.post("/users/register", response_model=RegisterUserResponse)
async def register_user(
    payload: RegisterUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RegisterUserResponse:
    UserPolicy.ensure_can_register_user(current_user)
    iam_client = IamClient()
    normalized_login = payload.login.strip()
    account_id = stable_iam_account_id(normalized_login)
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
        if binding is not None and binding.is_active:
            account = await iam_client.put_account(
                account_id=binding.external_subject_id,
                login=user.id,
                role=role_name,
                auth_status="pending",
            )
            if account.auth_status == "pending":
                action = await iam_client.create_action_token(
                    account_id=account.id,
                    purpose="password_setup",
                )
                profile = await uow.profiles.get_by_id(user.id)
                delivery_email = (payload.mail or (profile.mail if profile else None) or "").strip()
                if delivery_email:
                    await send_iam_password_action_email(
                        to_email=delivery_email,
                        raw_token=action.token,
                        purpose="password_setup",
                    )
            return RegisterUserResponse(
                data={"user_id": user.id, "role_id": user.id_role, "status": user.status}
            )

        account = await iam_client.put_account(
            account_id=binding.external_subject_id if binding is not None else account_id,
            login=user.id,
            role=role_name,
            auth_status="pending",
        )
        if binding is None:
            binding = UserAuthAccount(
                id_user=user.id,
                provider="iam",
                external_subject_id=account.id,
                external_username=user.id,
                external_email=payload.mail,
                is_active=True,
            )
            await uow.user_auth_accounts.add(binding)
        else:
            binding.is_active = True
        if account.auth_status == "pending":
            action = await iam_client.create_action_token(
                account_id=account.id,
                purpose="password_setup",
            )
            profile = await uow.profiles.get_by_id(user.id)
            delivery_email = (payload.mail or (profile.mail if profile else None) or "").strip()
            if delivery_email:
                await send_iam_password_action_email(
                    to_email=delivery_email,
                    raw_token=action.token,
                    purpose="password_setup",
                )

        unit_service = UnitService(uow.units, uow.users)
        if payload.unit_id is not None:
            if UserPolicy.can_manage_unit_members(current_user):
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
    return RegisterUserResponse(
        data={"user_id": user.id, "role_id": user.id_role, "status": user.status}
    )

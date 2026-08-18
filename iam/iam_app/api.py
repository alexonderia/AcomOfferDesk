from __future__ import annotations

import base64
import json
import logging
import uuid
from datetime import UTC, datetime
from urllib.parse import urlencode

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from fastapi import (
    APIRouter,
    Depends,
    Form,
    Header,
    Query,
    Request,
    Response,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shared.client_ip import resolve_client_ip
from shared.rate_limiter import SlidingWindowRateLimiter

from iam_app.browser_pages import (
    render_login_page,
    render_login_restart_page,
    render_password_page,
    render_password_saved_page,
)
from iam_app.core.config import settings
from iam_app.core.request_id import get_request_id
from iam_app.core.security import (
    constant_time_equal,
    decode_auth_request,
    decode_browser_session,
    encode_auth_request,
    encode_browser_session,
)
from iam_app.db import get_session
from iam_app.errors import Forbidden, IamError, RateLimited
from iam_app.schemas import (
    AccountCredentialStateResponse,
    AccountPermissionGrantsPutRequest,
    AccountPermissionsResponse,
    AccountPutRequest,
    AccountResponse,
    AccountRolePatchRequest,
    AccountStatusPatchRequest,
    ActionTokenConsumeRequest,
    ActionTokenConsumeResponse,
    ActionTokenRequest,
    ActionTokenResponse,
    LogoutRequest,
    RbacReportResponse,
    RbacSeedRequest,
    ReconciliationRequest,
    ReconciliationResponse,
    RefreshRequest,
    RegistrationCredentialsPutRequest,
    RegistrationCredentialsResponse,
    RevokeAllRequest,
    TokenBundleResponse,
    TokenExchangeRequest,
)
from iam_app.services import IamService


router = APIRouter()
logger = logging.getLogger(__name__)
MAX_RATE_LIMIT_BUCKETS = 10_000


class LoginRateLimiter:
    def __init__(
        self,
        *,
        attempts: int | None = None,
        window_seconds: float | None = None,
        max_buckets: int = MAX_RATE_LIMIT_BUCKETS,
    ) -> None:
        effective_attempts = (
            attempts
            if attempts is not None
            else settings.login_rate_limit_attempts
        )
        effective_window = (
            window_seconds
            if window_seconds is not None
            else settings.login_rate_limit_window_seconds
        )
        self._ip_limiter = SlidingWindowRateLimiter(
            attempts=effective_attempts,
            window_seconds=effective_window,
            max_buckets=max_buckets,
        )
        self._login_limiter = SlidingWindowRateLimiter(
            attempts=effective_attempts,
            window_seconds=effective_window,
            max_buckets=max_buckets,
        )

    @property
    def bucket_count(self) -> int:
        return self._ip_limiter.bucket_count + self._login_limiter.bucket_count

    async def check(self, *, client_ip: str, login: str) -> None:
        normalized_login = login.strip().casefold()
        if not await self._ip_limiter.allow(client_ip):
            raise RateLimited()
        if not await self._login_limiter.allow(normalized_login):
            raise RateLimited()


login_rate_limiter = LoginRateLimiter()


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


async def require_internal_service(
    x_acom_service_token: str = Header(default="", alias="X-Acom-Service-Token"),
) -> None:
    if not constant_time_equal(x_acom_service_token, settings.internal_service_token):
        logger.warning(
            "iam_security_event %s",
            json.dumps(
                {
                    "event_type": "internal_service_auth.failed",
                    "request_id": get_request_id(),
                    "success": False,
                    "reason_code": "invalid_service_token",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                sort_keys=True,
            ),
        )
        raise Forbidden()


def render_browser_auth_error(*, request: Request, error: str, status_code: int) -> HTMLResponse:
    if request.cookies.get(settings.auth_request_cookie_name):
        return render_login_page(error=error, status_code=status_code)
    return render_login_restart_page(error=error, status_code=status_code)


def _token_response(bundle) -> TokenBundleResponse:
    return TokenBundleResponse(
        access_token=bundle.access_token,
        access_token_expires_at=bundle.access_token_expires_at,
        refresh_token=bundle.refresh_token,
        refresh_token_expires_at=bundle.refresh_token_expires_at,
    )


@router.get("/iam/authorize", response_class=HTMLResponse)
async def authorize(
    request: Request,
    response_type: str = Query(default="code"),
    state: str = Query(min_length=16, max_length=512),
    code_challenge: str = Query(min_length=43, max_length=128),
    code_challenge_method: str = Query(default="S256"),
    redirect_uri: str = Query(min_length=8, max_length=2048),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    if (
        response_type != "code"
        or code_challenge_method != "S256"
        or redirect_uri not in settings.allowed_redirect_uris
    ):
        raise IamError()
    browser_session_token = request.cookies.get(settings.browser_session_cookie_name, "")
    if browser_session_token:
        try:
            browser_session = decode_browser_session(browser_session_token)
            result = await IamService(session).create_code_for_browser_session(
                account_id=uuid.UUID(str(browser_session["sub"])),
                password_version=int(browser_session["password_version"]),
                state=state,
                pkce_challenge=code_challenge,
                redirect_uri=redirect_uri,
            )
        except (KeyError, TypeError, ValueError, IamError):
            response = render_login_page()
            response.delete_cookie(
                settings.browser_session_cookie_name,
                path="/iam",
                secure=settings.cookie_secure,
                httponly=True,
                samesite="lax",
            )
            return response

        separator = "&" if "?" in result.redirect_uri else "?"
        response = RedirectResponse(
            f"{result.redirect_uri}{separator}{urlencode({'code': result.code, 'state': result.state})}",
            status_code=303,
        )
        response.delete_cookie(
            settings.auth_request_cookie_name,
            path="/iam",
            secure=settings.cookie_secure,
            httponly=True,
            samesite="lax",
        )
        return response

    auth_request = encode_auth_request(
        {
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "redirect_uri": redirect_uri,
        }
    )
    response = render_login_page()
    response.set_cookie(
        key=settings.auth_request_cookie_name,
        value=auth_request,
        max_age=600,
        path="/iam",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/iam/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str | None = Query(default=None, max_length=64)) -> Response:
    if error:
        messages = {
            "session_expired": "Сессия входа истекла. Войдите в систему заново.",
            "service_unavailable": "Сервис авторизации временно недоступен. Попробуйте позже.",
        }
        return render_login_restart_page(error=messages.get(error, "Не удалось продолжить вход."))
    if not request.cookies.get(settings.auth_request_cookie_name):
        return RedirectResponse("/api/v1/auth/login", status_code=303)
    return render_login_page()


@router.post("/iam/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    login: str = Form(min_length=3, max_length=128),
    password: str = Form(min_length=1, max_length=128),
    session: AsyncSession = Depends(get_session),
) -> Response:
    auth_request_token = request.cookies.get(settings.auth_request_cookie_name, "")
    try:
        auth_request = decode_auth_request(auth_request_token)
    except ValueError as exc:
        _ = exc
        return render_login_restart_page(error="Сессия входа истекла. Войдите в систему заново.")
    client_ip = _client_ip(request)
    await login_rate_limiter.check(client_ip=client_ip, login=login)
    try:
        result = await IamService(session).authenticate_and_create_code(
            login=login,
            password=password,
            state=str(auth_request["state"]),
            pkce_challenge=str(auth_request["code_challenge"]),
            redirect_uri=str(auth_request["redirect_uri"]),
        )
    except IamError as exc:
        return render_login_page(error=exc.public_detail, status_code=exc.status_code)

    separator = "&" if "?" in result.redirect_uri else "?"
    location = f"{result.redirect_uri}{separator}{urlencode({'code': result.code, 'state': result.state})}"
    response = RedirectResponse(location, status_code=303)
    response.set_cookie(
        key=settings.browser_session_cookie_name,
        value=encode_browser_session(
            account_id=str(result.account_id),
            password_version=result.password_version,
        ),
        max_age=settings.browser_session_ttl_seconds,
        path="/iam",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        settings.auth_request_cookie_name,
        path="/iam",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/iam/logout", status_code=204)
async def logout_browser_session() -> Response:
    response = Response(status_code=204)
    response.delete_cookie(
        settings.browser_session_cookie_name,
        path="/iam",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/iam/password/setup", response_class=HTMLResponse)
async def password_setup_page(token: str = Query(min_length=20, max_length=512)) -> HTMLResponse:
    return render_password_page(purpose="password_setup", token=token)


@router.get("/iam/password/reset", response_class=HTMLResponse)
async def password_reset_page(token: str = Query(min_length=20, max_length=512)) -> HTMLResponse:
    return render_password_page(purpose="password_reset", token=token)


async def _consume_password_form(
    *,
    purpose: str,
    token: str,
    new_password: str,
    password_confirmation: str,
    session: AsyncSession,
) -> HTMLResponse:
    if new_password != password_confirmation:
        response = render_password_page(
            purpose=purpose,
            token=token,
            error="Пароли не совпадают",
        )
        response.status_code = 400
        return response
    try:
        await IamService(session).consume_action_token(
            raw_token=token,
            purpose=purpose,
            new_password=new_password,
        )
    except IamError as exc:
        response = render_password_page(purpose=purpose, token=token, error=exc.public_detail)
        response.status_code = exc.status_code
        return response
    return render_password_saved_page(purpose=purpose)


@router.post("/iam/password/setup", response_class=HTMLResponse)
async def password_setup_submit(
    token: str = Form(min_length=20, max_length=512),
    new_password: str = Form(min_length=12, max_length=128),
    password_confirmation: str = Form(min_length=12, max_length=128),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    return await _consume_password_form(
        purpose="password_setup",
        token=token,
        new_password=new_password,
        password_confirmation=password_confirmation,
        session=session,
    )


@router.post("/iam/password/reset", response_class=HTMLResponse)
async def password_reset_submit(
    token: str = Form(min_length=20, max_length=512),
    new_password: str = Form(min_length=12, max_length=128),
    password_confirmation: str = Form(min_length=12, max_length=128),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    return await _consume_password_form(
        purpose="password_reset",
        token=token,
        new_password=new_password,
        password_confirmation=password_confirmation,
        session=session,
    )


@router.get("/iam/.well-known/jwks.json")
async def jwks() -> dict:
    def encode_number(value: int) -> str:
        length = (value.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(value.to_bytes(length, "big")).decode("ascii").rstrip("=")

    keys: list[dict[str, str]] = []
    for kid, public_key_pem in settings.verification_public_keys.items():
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(public_key, RSAPublicKey):
            raise RuntimeError("IAM signing public key must be RSA")
        numbers = public_key.public_numbers()
        keys.append(
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": kid,
                "n": encode_number(numbers.n),
                "e": encode_number(numbers.e),
            }
        )
    return {"keys": keys}


@router.post(
    "/internal/token",
    response_model=TokenBundleResponse,
    dependencies=[Depends(require_internal_service)],
)
async def exchange_token(
    payload: TokenExchangeRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenBundleResponse:
    bundle = await IamService(session).exchange_code(
        raw_code=payload.code,
        code_verifier=payload.code_verifier,
        redirect_uri=payload.redirect_uri,
        ip_address=payload.ip_address,
        user_agent=payload.user_agent,
    )
    return _token_response(bundle)


@router.post(
    "/internal/refresh",
    response_model=TokenBundleResponse,
    dependencies=[Depends(require_internal_service)],
)
async def refresh_token(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenBundleResponse:
    return _token_response(await IamService(session).refresh(raw_refresh_token=payload.refresh_token))


@router.post("/internal/logout", status_code=204, dependencies=[Depends(require_internal_service)])
async def logout(
    payload: LogoutRequest,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await IamService(session).logout(raw_refresh_token=payload.refresh_token, reason=payload.reason)
    return Response(status_code=204)


@router.put(
    "/internal/accounts/{account_id}",
    response_model=AccountResponse,
    dependencies=[Depends(require_internal_service)],
)
async def put_account(
    account_id: uuid.UUID,
    payload: AccountPutRequest,
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    result = await IamService(session).create_account(
        account_id=account_id,
        login=payload.login,
        role_name=payload.role,
        auth_status=payload.auth_status,
    )
    return AccountResponse(
        id=result.account.id,
        login=result.account.login,
        role=result.role_name,
        auth_status=result.account.auth_status,
        created=result.created,
    )


@router.put(
    "/internal/accounts/{account_id}/registration-credentials",
    response_model=RegistrationCredentialsResponse,
    dependencies=[Depends(require_internal_service)],
)
async def put_registration_credentials(
    account_id: uuid.UUID,
    payload: RegistrationCredentialsPutRequest,
    session: AsyncSession = Depends(get_session),
) -> RegistrationCredentialsResponse:
    result = await IamService(session).provision_registration_credentials(
        account_id=account_id,
        login=payload.login,
        role_name=payload.role,
        auth_status=payload.auth_status,
        initial_password=payload.password,
        replace_password=payload.replace_password,
    )
    return RegistrationCredentialsResponse(
        id=result.account.id,
        login=result.account.login,
        role=result.role_name,
        auth_status=result.account.auth_status,
        password_set=result.password_set,
        created=result.created,
    )


@router.get(
    "/internal/accounts/{account_id}/credential-state",
    response_model=AccountCredentialStateResponse,
    dependencies=[Depends(require_internal_service)],
)
async def get_account_credential_state(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AccountCredentialStateResponse:
    result = await IamService(session).get_credential_state(account_id=account_id)
    return AccountCredentialStateResponse(
        id=result.account.id,
        login=result.account.login,
        role=result.role_name,
        auth_status=result.account.auth_status,
        password_set=result.password_set,
        required_actions=list(result.required_actions),
    )


@router.post(
    "/internal/local-dev/accounts/{account_id}/provision",
    response_model=AccountResponse,
    dependencies=[Depends(require_internal_service)],
)
async def provision_local_development_account(
    account_id: uuid.UUID,
    payload: AccountPutRequest,
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    result = await IamService(session).provision_local_development_account(
        account_id=account_id,
        login=payload.login,
        role_name=payload.role,
    )
    return AccountResponse(
        id=result.account.id,
        login=result.account.login,
        role=result.role_name,
        auth_status=result.account.auth_status,
        created=result.created,
    )


@router.patch(
    "/internal/accounts/{account_id}/role",
    response_model=AccountResponse,
    dependencies=[Depends(require_internal_service)],
)
async def patch_account_role(
    account_id: uuid.UUID,
    payload: AccountRolePatchRequest,
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    result = await IamService(session).update_role(
        account_id=account_id,
        role_name=payload.role,
        actor_account_id=payload.actor_account_id,
        actor_session_id=payload.actor_session_id,
    )
    return AccountResponse(
        id=result.account.id,
        login=result.account.login,
        role=result.role_name,
        auth_status=result.account.auth_status,
    )


@router.get(
    "/internal/accounts/{account_id}/permissions",
    response_model=AccountPermissionsResponse,
    dependencies=[Depends(require_internal_service)],
)
async def get_account_permissions(
    account_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AccountPermissionsResponse:
    result = await IamService(session).get_account_permissions(account_id=account_id)
    return AccountPermissionsResponse(
        permissions_from_role=result.permissions_from_role,
        individually_granted_permissions=result.individually_granted_permissions,
        effective_permissions=result.effective_permissions,
    )


@router.put(
    "/internal/accounts/{account_id}/permission-grants",
    response_model=AccountPermissionsResponse,
    dependencies=[Depends(require_internal_service)],
)
async def put_account_permission_grants(
    account_id: uuid.UUID,
    payload: AccountPermissionGrantsPutRequest,
    session: AsyncSession = Depends(get_session),
) -> AccountPermissionsResponse:
    result = await IamService(session).replace_account_permission_grants(
        account_id=account_id,
        permission_names=payload.permissions,
    )
    return AccountPermissionsResponse(
        permissions_from_role=result.permissions_from_role,
        individually_granted_permissions=result.individually_granted_permissions,
        effective_permissions=result.effective_permissions,
    )


@router.patch(
    "/internal/accounts/{account_id}/status",
    response_model=AccountResponse,
    dependencies=[Depends(require_internal_service)],
)
async def patch_account_status(
    account_id: uuid.UUID,
    payload: AccountStatusPatchRequest,
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    result = await IamService(session).update_status(
        account_id=account_id,
        auth_status=payload.auth_status,
        actor_account_id=payload.actor_account_id,
        actor_session_id=payload.actor_session_id,
    )
    return AccountResponse(
        id=result.account.id,
        login=result.account.login,
        role=result.role_name,
        auth_status=result.account.auth_status,
    )


@router.post(
    "/internal/accounts/{account_id}/revoke-all",
    dependencies=[Depends(require_internal_service)],
)
async def revoke_all(
    account_id: uuid.UUID,
    payload: RevokeAllRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    count = await IamService(session).revoke_all(
        account_id=account_id,
        reason=payload.reason,
        actor_account_id=payload.actor_account_id,
        actor_session_id=payload.actor_session_id,
    )
    return {"revoked_sessions": count}


@router.post(
    "/internal/accounts/{account_id}/action-tokens",
    response_model=ActionTokenResponse,
    dependencies=[Depends(require_internal_service)],
)
async def create_action_token(
    account_id: uuid.UUID,
    payload: ActionTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> ActionTokenResponse:
    token, expires_at = await IamService(session).create_action_token(
        account_id=account_id,
        purpose=payload.purpose,
        context=payload.context,
    )
    return ActionTokenResponse(token=token, expires_at=expires_at, purpose=payload.purpose)


@router.post(
    "/internal/action-tokens/consume",
    response_model=ActionTokenConsumeResponse,
    dependencies=[Depends(require_internal_service)],
)
async def consume_action_token(
    payload: ActionTokenConsumeRequest,
    session: AsyncSession = Depends(get_session),
) -> ActionTokenConsumeResponse:
    result = await IamService(session).consume_action_token(
        raw_token=payload.token,
        purpose=payload.purpose,
        new_password=payload.new_password,
    )
    return ActionTokenConsumeResponse(
        account_id=result.account_id,
        purpose=result.purpose,
        auth_status=result.auth_status,
        context=result.context,
    )


@router.post(
    "/internal/accounts/{account_id}/required-actions/{purpose}/complete",
    dependencies=[Depends(require_internal_service)],
)
async def complete_required_action(
    account_id: uuid.UUID,
    purpose: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    await IamService(session).complete_required_action(account_id=account_id, purpose=purpose)
    return {"status": "completed", "purpose": purpose}


@router.put(
    "/internal/rbac",
    response_model=RbacReportResponse,
    dependencies=[Depends(require_internal_service)],
)
async def seed_rbac(
    payload: RbacSeedRequest,
    session: AsyncSession = Depends(get_session),
) -> RbacReportResponse:
    matrix = {role.name: sorted(set(role.permissions)) for role in payload.roles}
    return RbacReportResponse(roles=await IamService(session).seed_rbac(matrix))


@router.get(
    "/internal/rbac",
    response_model=RbacReportResponse,
    dependencies=[Depends(require_internal_service)],
)
async def rbac_report(session: AsyncSession = Depends(get_session)) -> RbacReportResponse:
    return RbacReportResponse(roles=await IamService(session).rbac_report())


@router.post(
    "/internal/reconciliation/accounts",
    response_model=ReconciliationResponse,
    dependencies=[Depends(require_internal_service)],
)
async def reconcile_accounts(
    payload: ReconciliationRequest,
    session: AsyncSession = Depends(get_session),
) -> ReconciliationResponse:
    orphan_ids, missing_ids = await IamService(session).reconcile_account_ids(
        set(payload.account_ids)
    )
    return ReconciliationResponse(
        orphan_iam_account_ids=orphan_ids,
        missing_iam_account_ids=missing_ids,
    )

from __future__ import annotations

import asyncio
import base64
import html
import time
import uuid
from collections import defaultdict, deque
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

from iam_app.core.config import settings
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
    AccountPermissionGrantsPutRequest,
    AccountPermissionsResponse,
    AccountPutRequest,
    AccountResponse,
    AccountRolePatchRequest,
    AccountStatusPatchRequest,
    ActionTokenRequest,
    ActionTokenResponse,
    LogoutRequest,
    RbacReportResponse,
    RbacSeedRequest,
    ReconciliationRequest,
    ReconciliationResponse,
    RefreshRequest,
    RevokeAllRequest,
    TokenBundleResponse,
    TokenExchangeRequest,
)
from iam_app.services import IamService


router = APIRouter()


class LoginRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - settings.login_rate_limit_window_seconds
        async with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= settings.login_rate_limit_attempts:
                raise RateLimited()
            attempts.append(now)
            if len(self._attempts) > 10_000:
                empty_keys = [item for item, values in self._attempts.items() if not values]
                for item in empty_keys:
                    self._attempts.pop(item, None)


login_rate_limiter = LoginRateLimiter()


async def require_internal_service(
    x_acom_service_token: str = Header(default="", alias="X-Acom-Service-Token"),
) -> None:
    if not constant_time_equal(x_acom_service_token, settings.internal_service_token):
        raise Forbidden()


def _page(*, title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:system-ui,sans-serif;background:#f5f7fa;margin:0;"
        "min-height:100vh;display:grid;place-items:center;color:#18212f}.card{width:min(420px,"
        "calc(100% - 32px));box-sizing:border-box;background:#fff;border:1px solid #dce2ea;"
        "border-radius:16px;padding:32px;box-shadow:0 12px 36px #17203314}h1{font-size:24px;"
        "margin:0 0 20px}label{display:block;font-weight:600;margin:14px 0 6px}input{width:100%;"
        "box-sizing:border-box;padding:11px 12px;border:1px solid #aeb8c5;border-radius:8px;"
        "font:inherit}button{width:100%;margin-top:22px;padding:12px;border:0;border-radius:8px;"
        "background:#1769e0;color:#fff;font:inherit;font-weight:700;cursor:pointer}.error{color:#a51d2d;"
        "margin-bottom:12px}.hint{color:#586579;font-size:14px}.action{display:block;text-align:center;"
        "margin-top:22px;padding:12px;border-radius:8px;background:#1769e0;color:#fff;text-decoration:none;"
        "font-weight:700}.secondary-action{display:block;text-align:center;margin-top:18px;color:#1769e0;"
        "font-weight:600;text-decoration:none}</style></head>"
        f'<body><main class="card">{body}</main></body></html>',
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )


def _login_page(*, error: str | None = None, status_code: int = 200) -> HTMLResponse:
    error_html = f'<p class="error">{html.escape(error)}</p>' if error else ""
    response = _page(
        title="Вход в AcomOfferDesk",
        body=(
            "<h1>Вход в AcomOfferDesk</h1>"
            f"{error_html}"
            '<form method="post" action="/iam/login" autocomplete="on">'
            '<label for="login">Логин</label><input id="login" name="login" '
            'autocomplete="username" maxlength="128" required>'
            '<label for="password">Пароль</label><input id="password" name="password" '
            'type="password" autocomplete="current-password" maxlength="128" required>'
            '<button type="submit">Войти</button></form>'
            '<a class="secondary-action" href="/login?reset=1">Забыли пароль?</a>'
        ),
    )
    response.status_code = status_code
    return response


def _login_restart_page(*, error: str, status_code: int = 400) -> HTMLResponse:
    response = _page(
        title="Вход в AcomOfferDesk",
        body=(
            "<h1>Вход в AcomOfferDesk</h1>"
            f'<p class="error">{html.escape(error)}</p>'
            '<p class="hint">Начните вход заново, чтобы создать новую защищённую сессию.</p>'
            '<a class="action" href="/api/v1/auth/login">Войти снова</a>'
        ),
    )
    response.status_code = status_code
    return response


def render_browser_auth_error(*, request: Request, error: str, status_code: int) -> HTMLResponse:
    if request.cookies.get(settings.auth_request_cookie_name):
        return _login_page(error=error, status_code=status_code)
    return _login_restart_page(error=error, status_code=status_code)


def _password_page(*, purpose: str, token: str, error: str | None = None) -> HTMLResponse:
    title = "Создание пароля" if purpose == "password_setup" else "Новый пароль"
    path = "setup" if purpose == "password_setup" else "reset"
    error_html = f'<p class="error">{html.escape(error)}</p>' if error else ""
    return _page(
        title=title,
        body=(
            f"<h1>{title}</h1>{error_html}"
            f'<form method="post" action="/iam/password/{path}">'
            f'<input type="hidden" name="token" value="{html.escape(token, quote=True)}">'
            '<label for="new_password">Пароль</label><input id="new_password" name="new_password" '
            'type="password" autocomplete="new-password" minlength="12" maxlength="128" required>'
            '<p class="hint">Используйте не менее 12 символов.</p>'
            f'<button type="submit">{title}</button></form>'
        ),
    )


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
            response = _login_page()
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
    response = _login_page()
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
        return _login_restart_page(error=messages.get(error, "Не удалось продолжить вход."))
    if not request.cookies.get(settings.auth_request_cookie_name):
        return RedirectResponse("/api/v1/auth/login", status_code=303)
    return _login_page()


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
        return _login_restart_page(error="Сессия входа истекла. Войдите в систему заново.")
    client_ip = request.client.host if request.client else "unknown"
    await login_rate_limiter.check(f"{client_ip}:{login.strip()}")
    try:
        result = await IamService(session).authenticate_and_create_code(
            login=login,
            password=password,
            state=str(auth_request["state"]),
            pkce_challenge=str(auth_request["code_challenge"]),
            redirect_uri=str(auth_request["redirect_uri"]),
        )
    except IamError as exc:
        return _login_page(error=exc.public_detail, status_code=exc.status_code)

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
    return _password_page(purpose="password_setup", token=token)


@router.get("/iam/password/reset", response_class=HTMLResponse)
async def password_reset_page(token: str = Query(min_length=20, max_length=512)) -> HTMLResponse:
    return _password_page(purpose="password_reset", token=token)


async def _consume_password_form(
    *,
    purpose: str,
    token: str,
    new_password: str,
    session: AsyncSession,
) -> HTMLResponse:
    try:
        await IamService(session).consume_action_token(
            raw_token=token,
            purpose=purpose,
            new_password=new_password,
        )
    except IamError as exc:
        response = _password_page(purpose=purpose, token=token, error=exc.public_detail)
        response.status_code = exc.status_code
        return response
    return _page(
        title="Пароль сохранён",
        body=(
            "<h1>Пароль сохранён</h1>"
            '<p class="hint">Теперь можно вернуться в AcomOfferDesk и войти с новым паролем.</p>'
        ),
    )


@router.post("/iam/password/setup", response_class=HTMLResponse)
async def password_setup_submit(
    token: str = Form(min_length=20, max_length=512),
    new_password: str = Form(min_length=12, max_length=128),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    return await _consume_password_form(
        purpose="password_setup", token=token, new_password=new_password, session=session
    )


@router.post("/iam/password/reset", response_class=HTMLResponse)
async def password_reset_submit(
    token: str = Form(min_length=20, max_length=512),
    new_password: str = Form(min_length=12, max_length=128),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    return await _consume_password_form(
        purpose="password_reset", token=token, new_password=new_password, session=session
    )


@router.get("/iam/.well-known/jwks.json")
async def jwks() -> dict:
    public_key = serialization.load_pem_public_key(settings.signing_public_key.encode("utf-8"))
    if not isinstance(public_key, RSAPublicKey):
        raise RuntimeError("IAM signing public key must be RSA")
    numbers = public_key.public_numbers()

    def encode_number(value: int) -> str:
        length = (value.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(value.to_bytes(length, "big")).decode("ascii").rstrip("=")

    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": settings.signing_kid,
                "n": encode_number(numbers.n),
                "e": encode_number(numbers.e),
            }
        ]
    }


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
    )
    return ActionTokenResponse(token=token, expires_at=expires_at, purpose=payload.purpose)


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

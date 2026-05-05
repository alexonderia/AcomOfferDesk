from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from jose import JWTError, jwt

from app.core.config import settings
from app.domain.exceptions import Unauthorized


OIDC_STATE_TTL_SECONDS = 600


def _urlsafe_random(bytes_length: int = 32) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(bytes_length)).decode("ascii").rstrip("=")


def _sanitize_next_path(next_path: str | None) -> str:
    if not next_path:
        return "/"
    candidate = next_path.strip()
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"
    return candidate


@dataclass(frozen=True, slots=True)
class OidcAuthorizationStart:
    cookie_token: str
    state: str
    code_verifier: str
    code_challenge: str
    expires_at: int
    next_path: str
    flow: str
    redirect_uri: str
    tg_registration_id: int | None
    registration_email: str | None


@dataclass(frozen=True, slots=True)
class OidcStateClaims:
    state: str
    code_verifier: str
    next_path: str
    flow: str
    redirect_uri: str
    tg_registration_id: int | None
    registration_email: str | None
    issued_at: int
    expires_at: int


def build_oidc_authorization_start(
    *,
    next_path: str | None = None,
    flow: str = "login",
    redirect_uri: str | None = None,
    tg_registration_id: int | None = None,
    registration_email: str | None = None,
) -> OidcAuthorizationStart:
    now = datetime.now(timezone.utc)
    state = _urlsafe_random(24)
    code_verifier = _urlsafe_random(48)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    expires_at = int((now + timedelta(seconds=OIDC_STATE_TTL_SECONDS)).timestamp())
    normalized_next_path = _sanitize_next_path(next_path)
    normalized_redirect_uri = (redirect_uri or settings.keycloak_callback_url).strip() or settings.keycloak_callback_url
    normalized_registration_email = (registration_email or "").strip().lower() or None
    payload = {
        "state": state,
        "code_verifier": code_verifier,
        "next_path": normalized_next_path,
        "flow": flow,
        "redirect_uri": normalized_redirect_uri,
        "tg_registration_id": tg_registration_id,
        "registration_email": normalized_registration_email,
        "iat": int(now.timestamp()),
        "exp": expires_at,
        "type": "oidc_state",
    }
    token = jwt.encode(payload, settings.resolved_refresh_token_secret, algorithm=settings.jwt_algorithm)
    return OidcAuthorizationStart(
        cookie_token=token,
        state=state,
        code_verifier=code_verifier,
        code_challenge=code_challenge,
        expires_at=expires_at,
        next_path=normalized_next_path,
        flow=flow,
        redirect_uri=normalized_redirect_uri,
        tg_registration_id=tg_registration_id,
        registration_email=normalized_registration_email,
    )


def decode_oidc_state_token(token: str) -> OidcStateClaims:
    try:
        payload = jwt.decode(token, settings.resolved_refresh_token_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise Unauthorized("Invalid OIDC state") from exc

    if payload.get("type") != "oidc_state":
        raise Unauthorized("Invalid OIDC state")

    state = str(payload.get("state") or "").strip()
    code_verifier = str(payload.get("code_verifier") or "").strip()
    next_path = _sanitize_next_path(payload.get("next_path"))
    flow = str(payload.get("flow") or "login").strip() or "login"
    redirect_uri = str(payload.get("redirect_uri") or "").strip() or settings.keycloak_callback_url
    raw_tg_registration_id = payload.get("tg_registration_id")
    tg_registration_id: int | None = None
    if raw_tg_registration_id not in {None, ""}:
        try:
            tg_registration_id = int(raw_tg_registration_id)
        except (TypeError, ValueError) as exc:
            raise Unauthorized("Invalid OIDC state") from exc
    registration_email = str(payload.get("registration_email") or "").strip().lower() or None
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if not state or not code_verifier or not isinstance(issued_at, int) or not isinstance(expires_at, int):
        raise Unauthorized("Invalid OIDC state")

    return OidcStateClaims(
        state=state,
        code_verifier=code_verifier,
        next_path=next_path,
        flow=flow,
        redirect_uri=redirect_uri,
        tg_registration_id=tg_registration_id,
        registration_email=registration_email,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def build_keycloak_login_url(
    *,
    state: str,
    code_challenge: str,
    redirect_uri: str | None = None,
    prompt: str | None = None,
) -> str:
    resolved_redirect_uri = (redirect_uri or settings.keycloak_callback_url).strip() or settings.keycloak_callback_url
    parts = [
        f"client_id={quote(settings.keycloak_client_id, safe='')}",
        "response_type=code",
        f"redirect_uri={quote(resolved_redirect_uri, safe='')}",
        "scope=openid%20profile%20email",
        f"state={quote(state, safe='')}",
        f"code_challenge={quote(code_challenge, safe='')}",
        "code_challenge_method=S256",
    ]
    if prompt:
        parts.append(f"prompt={quote(prompt, safe='')}")
    return f"{settings.keycloak_authorization_endpoint}?{'&'.join(parts)}"

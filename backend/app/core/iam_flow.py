from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from jose import JWTError, jwt

from app.core.config import settings
from app.domain.exceptions import Unauthorized


FLOW_TTL_SECONDS = 600


def _random(bytes_length: int) -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(bytes_length)).decode("ascii").rstrip("=")


def sanitize_next_path(next_path: str | None) -> str:
    candidate = (next_path or "/").strip()
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"
    return candidate


@dataclass(frozen=True, slots=True)
class IamFlowStart:
    cookie_token: str
    state: str
    verifier: str
    challenge: str
    next_path: str


@dataclass(frozen=True, slots=True)
class IamFlowClaims:
    state: str
    verifier: str
    redirect_uri: str
    next_path: str


def create_iam_flow(next_path: str | None) -> IamFlowStart:
    now = datetime.now(UTC)
    state = _random(24)
    verifier = _random(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    normalized_next = sanitize_next_path(next_path)
    payload = {
        "type": "iam_flow",
        "state": state,
        "verifier": verifier,
        "redirect_uri": settings.iam_callback_url,
        "next_path": normalized_next,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=FLOW_TTL_SECONDS)).timestamp()),
    }
    cookie_token = jwt.encode(payload, settings.resolved_refresh_token_secret, algorithm="HS256")
    return IamFlowStart(
        cookie_token=cookie_token,
        state=state,
        verifier=verifier,
        challenge=challenge,
        next_path=normalized_next,
    )


def decode_iam_flow(cookie_token: str) -> IamFlowClaims:
    try:
        payload = jwt.decode(
            cookie_token,
            settings.resolved_refresh_token_secret,
            algorithms=["HS256"],
        )
    except JWTError as exc:
        raise Unauthorized("Invalid IAM state") from exc
    if payload.get("type") != "iam_flow":
        raise Unauthorized("Invalid IAM state")
    state = str(payload.get("state") or "").strip()
    verifier = str(payload.get("verifier") or "").strip()
    redirect_uri = str(payload.get("redirect_uri") or "").strip()
    next_path = sanitize_next_path(payload.get("next_path"))
    if not state or not verifier or redirect_uri != settings.iam_callback_url:
        raise Unauthorized("Invalid IAM state")
    return IamFlowClaims(
        state=state,
        verifier=verifier,
        redirect_uri=redirect_uri,
        next_path=next_path,
    )


def build_iam_authorize_url(flow: IamFlowStart) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "state": flow.state,
            "code_challenge": flow.challenge,
            "code_challenge_method": "S256",
            "redirect_uri": settings.iam_callback_url,
        }
    )
    return f"{settings.resolved_iam_public_base_url}/authorize?{query}"

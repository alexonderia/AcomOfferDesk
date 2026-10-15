from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.request_id import get_request_id
from app.domain.exceptions import AuthenticationUnavailable, Unauthorized
from app.domain.iam_roles import local_role_id
from app.domain.permissions import get_known_permissions


AUTH_SERVICE_UNAVAILABLE_CODE = "AUTH_SERVICE_UNAVAILABLE"
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IamAccessClaims:
    account_id: str
    session_id: str
    system_role: str
    role_id: int
    permissions: frozenset[str]
    issued_at: int
    expires_at: int
    required_actions: frozenset[str] = frozenset()


def _log_jwt_header_failure(*, kid: str | None, reason_code: str) -> None:
    logger.warning(
        "security_event %s",
        json.dumps(
            {
                "event_type": (
                    "invalid_jwt_kid"
                    if reason_code == "unknown_kid"
                    else "invalid_jwt"
                ),
                "kid": kid,
                "reason_code": reason_code,
                "request_id": get_request_id(),
                "success": False,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            sort_keys=True,
        ),
    )


def decode_iam_access_token(token: str) -> IamAccessClaims:
    verification_keys = settings.iam_verification_keys
    if not verification_keys:
        raise AuthenticationUnavailable()
    try:
        header = jwt.get_unverified_header(token)
        kid = str(header.get("kid") or "").strip()
        if header.get("alg") != "RS256":
            _log_jwt_header_failure(
                kid=kid or None,
                reason_code="invalid_algorithm",
            )
            raise Unauthorized("Unknown IAM signing key")
        public_key = verification_keys.get(kid)
        if public_key is None:
            _log_jwt_header_failure(
                kid=kid or None,
                reason_code="unknown_kid",
            )
            raise Unauthorized("Unknown IAM signing key")
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=settings.resolved_iam_issuer,
            audience=settings.iam_audience,
            options={
                "require_sub": True,
                "require_iat": True,
                "require_exp": True,
                "require_iss": True,
                "require_aud": True,
            },
        )
    except ExpiredSignatureError as exc:
        raise Unauthorized("Token expired") from exc
    except Unauthorized:
        raise
    except JWTError as exc:
        raise Unauthorized("Invalid token") from exc

    subject = str(payload.get("sub") or "").strip()
    session_id = str(payload.get("sid") or "").strip()
    system_role = str(payload.get("role") or "").strip()
    role_id = local_role_id(system_role)
    raw_permissions = payload.get("permissions")
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    try:
        uuid.UUID(subject)
        uuid.UUID(session_id)
    except (ValueError, AttributeError) as exc:
        raise Unauthorized("Invalid token payload") from exc
    if (
        role_id is None
        or not isinstance(raw_permissions, list)
        or not all(isinstance(item, str) and item.strip() for item in raw_permissions)
        or not isinstance(issued_at, int)
        or not isinstance(expires_at, int)
    ):
        raise Unauthorized("Invalid token payload")
    permissions = frozenset(item.strip() for item in raw_permissions)
    if not permissions.issubset(get_known_permissions()):
        raise Unauthorized("Invalid token payload")
    raw_required_actions = payload.get("required_actions") or []
    if not isinstance(raw_required_actions, list) or not all(
        isinstance(item, str) and item.strip() for item in raw_required_actions
    ):
        raise Unauthorized("Invalid token payload")
    return IamAccessClaims(
        account_id=subject,
        session_id=session_id,
        system_role=system_role,
        role_id=role_id,
        permissions=permissions,
        issued_at=issued_at,
        expires_at=expires_at,
        required_actions=frozenset(item.strip() for item in raw_required_actions),
    )

from __future__ import annotations

import uuid
from dataclasses import dataclass

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.domain.exceptions import AuthenticationUnavailable, Unauthorized
from app.domain.iam_roles import local_role_id
from app.domain.permissions import get_known_permissions


AUTH_SERVICE_UNAVAILABLE_CODE = "AUTH_SERVICE_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class IamAccessClaims:
    account_id: str
    session_id: str
    system_role: str
    role_id: int
    permissions: frozenset[str]
    issued_at: int
    expires_at: int


def decode_iam_access_token(token: str) -> IamAccessClaims:
    public_key = settings.iam_signing_public_key
    if not public_key:
        raise AuthenticationUnavailable()
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256" or header.get("kid") != settings.iam_signing_kid:
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
    return IamAccessClaims(
        account_id=subject,
        session_id=session_id,
        system_role=system_role,
        role_id=role_id,
        permissions=permissions,
        issued_at=issued_at,
        expires_at=expires_at,
    )

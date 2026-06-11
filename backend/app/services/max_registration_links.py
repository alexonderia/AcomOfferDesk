from __future__ import annotations

import time
from urllib.parse import quote

from app.core.config import settings
from app.core.max_links import decode_max_token
from app.core.max_shortcodes import MaxShortcodeCodec
from app.domain.exceptions import Conflict

DEFAULT_MAX_REGISTRATION_NEXT_PATH = "/account"


class MaxRegistrationLinkInvalidError(ValueError):
    pass


class MaxRegistrationLinkExpiredError(ValueError):
    pass


def create_max_registration_token(*, max_user_id: str) -> str:
    if not settings.max_link_secret:
        raise Conflict("MAX links are not configured")
    payload = MaxShortcodeCodec.build(
        max_user_id=max_user_id,
        purpose="max_register",
        ttl_seconds=settings.max_register_ttl_seconds,
    )
    return MaxShortcodeCodec.encode(payload, secret=settings.max_link_secret)


def build_keycloak_max_registration_link(
    *,
    token: str,
    next_path: str = DEFAULT_MAX_REGISTRATION_NEXT_PATH,
) -> str:
    if not settings.public_backend_base_url:
        raise Conflict("Public backend URL is not configured")
    encoded_token = quote(token, safe="")
    encoded_next_path = quote(next_path, safe="/")
    return (
        f"{settings.public_backend_base_url.rstrip('/')}/api/v1/auth/oidc/register"
        f"?max_token={encoded_token}&next_path={encoded_next_path}"
    )


async def resolve_max_registration_token(token: str) -> str:
    if not settings.max_link_secret:
        raise MaxRegistrationLinkInvalidError("Invalid token")

    now = int(time.time())
    try:
        payload = decode_max_token(token, settings.max_link_secret)
    except ValueError:
        payload = None

    if payload is not None:
        if payload.purpose != "max_register":
            raise MaxRegistrationLinkInvalidError("Invalid token")
        if payload.exp < now:
            raise MaxRegistrationLinkExpiredError("Link expired")
        return payload.max_user_id

    try:
        shortcode_payload = MaxShortcodeCodec.decode(token, secret=settings.max_link_secret)
    except ValueError as exc:
        raise MaxRegistrationLinkInvalidError("Invalid token") from exc

    if shortcode_payload.purpose != "max_register":
        raise MaxRegistrationLinkInvalidError("Invalid token")
    if shortcode_payload.exp < now:
        raise MaxRegistrationLinkExpiredError("Link expired")
    return shortcode_payload.max_user_id

from __future__ import annotations

import time
from urllib.parse import quote

from app.core.config import settings
from app.core.tg_links import decode_token
from app.core.tg_shortcodes import TgShortcodeCodec
from app.domain.exceptions import Conflict
from app.services.tg_notifications import notify_expired_link

DEFAULT_TG_REGISTRATION_NEXT_PATH = "/account"


class TgRegistrationLinkInvalidError(ValueError):
    pass


class TgRegistrationLinkExpiredError(ValueError):
    pass


def create_tg_registration_token(*, tg_id: int) -> str:
    if not settings.tg_link_secret:
        raise Conflict("TG links are not configured")
    payload = TgShortcodeCodec.build(
        tg_id=tg_id,
        purpose="tg_register",
        ttl_seconds=settings.tg_register_ttl_seconds,
    )
    return TgShortcodeCodec.encode(payload, secret=settings.tg_link_secret)


def build_keycloak_registration_link(
    *,
    token: str,
    next_path: str = DEFAULT_TG_REGISTRATION_NEXT_PATH,
) -> str:
    if not settings.public_backend_base_url:
        raise Conflict("Public backend URL is not configured")
    encoded_token = quote(token, safe="")
    encoded_next_path = quote(next_path, safe="/")
    return (
        f"{settings.public_backend_base_url.rstrip('/')}/api/v1/auth/oidc/register"
        f"?tg_token={encoded_token}&next_path={encoded_next_path}"
    )


async def resolve_tg_registration_token(token: str) -> int:
    if not settings.tg_link_secret:
        raise TgRegistrationLinkInvalidError("Invalid token")

    now = int(time.time())
    try:
        payload = decode_token(token, settings.tg_link_secret)
    except ValueError:
        payload = None

    if payload is not None:
        if payload.purpose != "tg_register":
            raise TgRegistrationLinkInvalidError("Invalid token")
        if payload.exp < now:
            await notify_expired_link(payload.tg_id)
            raise TgRegistrationLinkExpiredError("Link expired")
        return payload.tg_id

    try:
        shortcode_payload = TgShortcodeCodec.decode(token, secret=settings.tg_link_secret)
    except ValueError as exc:
        raise TgRegistrationLinkInvalidError("Invalid token") from exc

    if shortcode_payload.purpose != "tg_register":
        raise TgRegistrationLinkInvalidError("Invalid token")
    if shortcode_payload.exp < now:
        await notify_expired_link(shortcode_payload.tg_id)
        raise TgRegistrationLinkExpiredError("Link expired")
    return shortcode_payload.tg_id

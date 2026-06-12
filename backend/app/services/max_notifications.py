from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import datetime
from urllib.parse import quote, urlparse

from app.core.config import settings
from app.infrastructure.notification_publisher import publish_notification
from shared.broker import RK_MAX
from shared.notification_copy import (
    ACCESS_CLOSED_BODY,
    ACCESS_OPENED_BODY,
    EXPIRED_REGISTRATION_LINK_BODY,
    MAX_ACCOUNT_LINKED_BODY,
    REGISTRATION_COMPLETED_BODY,
    message_created_body,
    new_request_outbound_body,
    offer_status_changed_body,
    offer_updated_body,
    request_deadline_changed_body,
    request_files_changed_body,
    request_status_changed_body,
)

_INVALID_MAX_BUTTON_HOSTS = {
    "",
    "0.0.0.0",
    "127.0.0.1",
    "::1",
    "localhost",
    "backend",
    "gateway",
    "keycloak",
    "minio",
    "rabbitmq",
    "web",
}


async def notify_expired_link(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=EXPIRED_REGISTRATION_LINK_BODY,
    )


async def notify_registration_completed(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=REGISTRATION_COMPLETED_BODY,
    )


async def notify_access_opened(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=ACCESS_OPENED_BODY,
    )


async def notify_access_closed(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=ACCESS_CLOSED_BODY,
    )


async def notify_new_message(*, max_user_id: str, request_id: str) -> None:
    link = _build_web_service_link()
    await _notify(
        max_user_id=max_user_id,
        text=message_created_body(request_id=request_id),
        button_text="Открыть систему",
        button_url=link,
    )


async def notify_new_request(
    *,
    max_user_ids: Iterable[str],
    request_id: str,
    description: str | None,
    deadline_at: datetime,
) -> None:
    text = new_request_outbound_body(
        request_id=request_id,
        description=description,
        deadline_at=deadline_at,
    )
    tasks = []
    for max_user_id in max_user_ids:
        link = _build_web_service_link()
        tasks.append(
            _notify(
                max_user_id=max_user_id,
                text=text,
                button_text="Открыть заявку",
                button_url=link,
            )
        )

    if tasks:
        await asyncio.gather(*tasks)


async def notify_request_status_changed(
    *,
    max_user_id: str,
    request_id: str,
    previous_status: str | None = None,
    new_status: str | None = None,
) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=request_status_changed_body(
            request_id=request_id,
            previous_status=previous_status,
            new_status=new_status,
        ),
        button_text="Открыть систему",
        button_url=_build_web_service_link(),
    )


async def notify_request_deadline_changed(*, max_user_id: str, request_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=request_deadline_changed_body(request_id=request_id),
        button_text="Открыть заявку",
        button_url=_build_web_service_link(),
    )


async def notify_request_files_changed(*, max_user_id: str, request_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=request_files_changed_body(request_id=request_id),
        button_text="Открыть заявку",
        button_url=_build_web_service_link(),
    )


async def notify_offer_updated(*, max_user_id: str, request_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=offer_updated_body(request_id=request_id),
        button_text="Открыть КП",
        button_url=_build_web_service_link(),
    )


async def notify_offer_status_finalized(*, max_user_id: str, request_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=offer_status_changed_body(request_id=request_id),
        button_text="Открыть систему",
        button_url=_build_web_service_link(),
    )


async def notify_account_linked(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text=MAX_ACCOUNT_LINKED_BODY,
    )


def _build_web_service_link() -> str:
    public_base_url = _resolve_max_public_base_url()
    if public_base_url is None:
        return ""
    next_path = quote("/", safe="/")
    return f"{public_base_url}/login?next={next_path}"


def _resolve_max_public_base_url() -> str | None:
    for candidate in (settings.public_backend_base_url, settings.web_base_url):
        normalized = _normalize_max_button_base_url(candidate)
        if normalized is not None:
            return normalized
    return None


def _normalize_max_button_base_url(value: str | None) -> str | None:
    if value is None:
        return None

    candidate = value.strip().rstrip("/")
    if not candidate:
        return None

    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").strip().lower()
    if parsed.scheme not in {"http", "https"}:
        return None
    if hostname in _INVALID_MAX_BUTTON_HOSTS:
        return None
    if hostname.endswith(".local"):
        return None

    return candidate


async def _notify(
    *,
    max_user_id: str,
    text: str,
    button_text: str | None = None,
    button_url: str | None = None,
) -> None:
    if not settings.max_bot_enabled:
        return

    normalized_user_id = str(max_user_id).strip()
    if not normalized_user_id:
        return

    await publish_notification(
        RK_MAX,
        {
            "user_id": normalized_user_id,
            "text": text,
            "button_text": button_text,
            "button_url": button_url,
        },
    )

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import datetime
from urllib.parse import quote, urlparse

from app.core.config import settings
from app.infrastructure.notification_publisher import publish_notification
from shared.broker import RK_MAX

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
        text="Срок действия ссылки истек. Пожалуйста, запросите новую через /start.",
    )


async def notify_registration_completed(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text="Регистрация пройдена. Данные отправлены на проверку.",
    )


async def notify_access_opened(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text="Доступ открыт. Теперь вы можете получать открытые заявки через MAX.",
    )


async def notify_access_closed(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text="Доступ к системе через MAX ограничен.",
    )


async def notify_new_message(*, max_user_id: str, request_id: str) -> None:
    link = _build_web_service_link()
    await _notify(
        max_user_id=max_user_id,
        text=f"Новое сообщение по заявке №{request_id}",
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
    description_text = description.strip() if description else "без описания"
    deadline_text = deadline_at.strftime("%d.%m.%Y, %H:%M")
    tasks = []
    for max_user_id in max_user_ids:
        link = _build_web_service_link()
        text = (
            f"Новая заявка №{request_id}\n\n"
            f"{description_text}\n"
            f"Срок: {deadline_text}"
        )
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


async def notify_request_status_changed(*, max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text="Статус интересующей вас заявки изменён.",
        button_text="Открыть систему",
        button_url=_build_web_service_link(),
    )


async def notify_offer_status_finalized(*, max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text="Статус вашего оффера обновлён.",
        button_text="Открыть систему",
        button_url=_build_web_service_link(),
    )


async def notify_account_linked(max_user_id: str) -> None:
    await _notify(
        max_user_id=max_user_id,
        text="MAX successfully linked to your AcomOfferDesk account.",
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

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import datetime
from urllib.parse import quote, urlparse

from app.core.config import settings
from app.infrastructure.notification_publisher import publish_notification
from shared.broker import RK_TG

_INVALID_TELEGRAM_BUTTON_HOSTS = {
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

async def notify_expired_link(tg_id: int) -> None:
    await _notify(
        tg_id=tg_id,
        text="Срок действия ссылки истек. Пожалуйста, запросите новую через /start.",
    )


async def notify_registration_completed(tg_id: int) -> None:
    await _notify(
        tg_id=tg_id,
        text="Регистрация пройдена. Данные отправлены на проверку.",
    )


async def notify_access_opened(tg_id: int) -> None:
    await _notify(
        tg_id=tg_id,
        text="Доступ открыт. Теперь вы можете войти в веб-приложение.",
    )

async def notify_access_closed(tg_id: int) -> None:
    await _notify(
        tg_id=tg_id,
        text="⛔ Доступ к Telegram-боту закрыт.",
    )

async def notify_new_message(*, tg_id: int, request_id: int) -> None:
    link = _build_web_service_link(tg_id=tg_id)
    await _notify(
        tg_id=tg_id,
        text=f"💬 Новое сообщение по заявке №{request_id}",
        button_text="Открыть сервис",
        button_url=link,
    )

async def notify_new_request(
    *,
    tg_ids: Iterable[int],
    request_id: int,
    description: str | None,
    deadline_at: datetime,
) -> None:
    description_text = description.strip() if description else "без описания"
    deadline_text = deadline_at.strftime("%d.%m.%Y, %H:%M")
    tasks = []
    for tg_id in tg_ids:
        link = _build_web_service_link(tg_id=tg_id)
        text = (
            f"📄 Новая заявка №{request_id}\n\n"
            f"📝 Описание: {description_text}\n"
            f"⏰ Дедлайн приёма КП: {deadline_text}"
        )
        tasks.append(
            _notify(
                tg_id=tg_id,
                text=text,
                button_text="Перейти в сервис",
                button_url=link,
            )
        )

    if tasks:
        await asyncio.gather(*tasks)

async def notify_request_status_changed(*, tg_id: int) -> None:
    await _notify(
        tg_id=tg_id,
        text="Статус интересующей вас заявки изменён.",
        button_text="Перейти в сервис",
        button_url=_build_web_service_link(tg_id=tg_id),
    )


async def notify_offer_status_finalized(*, tg_id: int) -> None:
    await _notify(
        tg_id=tg_id,
        text="Статус вашего оффера обновлён.",
        button_text="Перейти в сервис",
        button_url=_build_web_service_link(tg_id=tg_id),
    )

def _build_authorization_link(*, tg_id: int) -> str:
    _ = tg_id
    public_base_url = _resolve_telegram_public_base_url()
    if public_base_url is None:
        return ""
    next_path = quote("/", safe="/")
    return f"{public_base_url}/login?next={next_path}"


def _build_web_service_link(*, tg_id: int) -> str:
    return _build_authorization_link(tg_id=tg_id)


def _resolve_telegram_public_base_url() -> str | None:
    for candidate in (settings.public_backend_base_url, settings.web_base_url):
        normalized = _normalize_telegram_button_base_url(candidate)
        if normalized is not None:
            return normalized
    return None


def _normalize_telegram_button_base_url(value: str | None) -> str | None:
    if value is None:
        return None

    candidate = value.strip().rstrip("/")
    if not candidate:
        return None

    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").strip().lower()
    if parsed.scheme not in {"http", "https"}:
        return None
    if hostname in _INVALID_TELEGRAM_BUTTON_HOSTS:
        return None
    if hostname.endswith(".local"):
        return None

    return candidate

async def _notify(
    *,
    tg_id: int,
    text: str,
    button_text: str | None = None,
    button_url: str | None = None,
) -> None:
    # LEGACY: Telegram transport is disabled in production by default.
    # Keep the publisher intact so the flow can be restored via LEGACY_TELEGRAM_ENABLED=true.
    if not settings.telegram_legacy_enabled:
        return

    await publish_notification(
        RK_TG,
        {
            "chat_id": tg_id,
            "text": text,
            "button_text": button_text,
            "button_url": button_url,
        },
    )

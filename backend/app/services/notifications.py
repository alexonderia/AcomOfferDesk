from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Awaitable, Callable

from app.domain.exceptions import NotFound
from app.domain.notifications import (
    NOTIFICATION_SEVERITIES,
    NOTIFICATION_TYPES,
    sanitize_notification_error_message,
)
from app.models.orm_models import UserNotification
from app.realtime.contracts import OutboundEnvelope
from app.repositories.notifications import NotificationRepository
from shared.normalization import as_optional_int as _as_optional_int

logger = logging.getLogger(__name__)
_SYSTEM_TOAST_CHANNEL = "system"


RealtimeNotificationSender = Callable[..., Awaitable[bool]]


class NotificationService:
    def __init__(
        self,
        notifications: NotificationRepository,
        realtime_sender: RealtimeNotificationSender | None = None,
    ):
        self._notifications = notifications
        self._realtime_sender = realtime_sender

    async def create_for_user(
        self,
        *,
        user_id: str,
        notification_type: str,
        severity: str,
        title: str,
        body: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        link_url: str | None = None,
        payload: dict | None = None,
    ) -> UserNotification:
        normalized_user_id = user_id.strip()
        if not normalized_user_id:
            raise ValueError("user_id is required")
        self._ensure_supported_type(notification_type)
        self._ensure_supported_severity(severity)

        notification = UserNotification(
            user_id=normalized_user_id,
            type=notification_type,
            severity=severity,
            title=title.strip() or "Уведомление",
            body=body.strip() or "Есть обновление.",
            entity_type=(entity_type.strip() if entity_type else None),
            entity_id=entity_id,
            link_url=(link_url.strip() if link_url else None),
            payload=payload,
        )
        created = await self._notifications.create(notification)
        await self._send_created_event_best_effort(created)
        return created

    async def create_many_for_users(
        self,
        *,
        user_ids: Sequence[str],
        notification_type: str,
        severity: str,
        title: str,
        body: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        link_url: str | None = None,
        payload: dict | None = None,
    ) -> list[UserNotification]:
        seen: set[str] = set()
        notifications_to_create: list[UserNotification] = []
        self._ensure_supported_type(notification_type)
        self._ensure_supported_severity(severity)
        for user_id in user_ids:
            normalized = user_id.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            notifications_to_create.append(
                UserNotification(
                    user_id=normalized,
                    type=notification_type,
                    severity=severity,
                    title=title.strip() or "Уведомление",
                    body=body.strip() or "Есть обновление.",
                    entity_type=(entity_type.strip() if entity_type else None),
                    entity_id=entity_id,
                    link_url=(link_url.strip() if link_url else None),
                    payload=payload,
                )
            )

        if not notifications_to_create:
            return []

        create_many = getattr(self._notifications, "create_many", None)
        if callable(create_many):
            created = await create_many(notifications_to_create)
        else:
            created = []
            for notification in notifications_to_create:
                created.append(await self._notifications.create(notification))

        await asyncio.gather(
            *(self._send_created_event_best_effort(notification) for notification in created),
            return_exceptions=True,
        )
        return created

    async def list_for_current_user(
        self,
        *,
        user_id: str,
        limit: int,
        offset: int,
    ) -> list[UserNotification]:
        return await self._notifications.list_for_user(user_id=user_id, limit=limit, offset=offset)

    async def count_unread_for_current_user(self, *, user_id: str) -> int:
        return await self._notifications.count_unread(user_id=user_id)

    async def mark_as_read_for_current_user(self, *, user_id: str, notification_id: int) -> UserNotification:
        notification = await self._notifications.mark_as_read(user_id=user_id, notification_id=notification_id)
        if notification is None:
            raise NotFound("Уведомление не найдено.")
        return notification

    async def mark_all_as_read_for_current_user(self, *, user_id: str) -> int:
        return await self._notifications.mark_all_as_read(user_id=user_id)

    async def notify_offer_created(
        self,
        *,
        actor_user_id: str,
        recipient_user_id: str,
        request_id: str,
        offer_id: int,
    ) -> UserNotification | None:
        if actor_user_id == recipient_user_id:
            return None
        return await self.create_for_user(
            user_id=recipient_user_id,
            notification_type="offer.created",
            severity="info",
            title="Новое коммерческое предложение",
            body=f"По заявке №{request_id} создано новое КП.",
            entity_type="offer",
            entity_id=offer_id,
            link_url=f"/requests/{request_id}",
            payload={
                "request_id": request_id,
                "offer_id": offer_id,
                "actor_user_id": actor_user_id,
                "recipient_user_id": recipient_user_id,
            },
        )

    async def notify_message_created(
        self,
        *,
        author_user_id: str,
        recipient_user_ids: Sequence[str],
        request_id: str,
        offer_id: int,
        chat_id: int,
        message_id: int,
    ) -> list[UserNotification]:
        recipients = [user_id for user_id in recipient_user_ids if user_id != author_user_id]
        return await self.create_many_for_users(
            user_ids=recipients,
            notification_type="message.created",
            severity="info",
            title="Новое сообщение",
            body=f"В чате по заявке №{request_id} появилось новое сообщение.",
            entity_type="message",
            entity_id=message_id,
            link_url=f"/offers/{offer_id}/workspace",
            payload={
                "request_id": request_id,
                "offer_id": offer_id,
                "chat_id": chat_id,
                "message_id": message_id,
                "author_user_id": author_user_id,
            },
        )

    async def notify_email_sent(
        self,
        *,
        recipient_user_id: str,
        title: str = "Письмо отправлено",
        body: str = "Письмо успешно отправлено.",
        entity_type: str | None = None,
        entity_id: int | None = None,
        link_url: str | None = None,
        payload: dict | None = None,
    ) -> UserNotification:
        return await self.create_for_user(
            user_id=recipient_user_id,
            notification_type="email.sent",
            severity="success",
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            link_url=link_url,
            payload=payload,
        )

    async def notify_email_failed(
        self,
        *,
        recipient_user_id: str,
        error_message: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        link_url: str | None = None,
        payload: dict | None = None,
    ) -> UserNotification:
        safe_error = sanitize_notification_error_message(error_message)
        return await self.create_for_user(
            user_id=recipient_user_id,
            notification_type="email.failed",
            severity="error",
            title="Письмо не отправлено",
            body=f"Ошибка отправки письма: {safe_error}",
            entity_type=entity_type,
            entity_id=entity_id,
            link_url=link_url,
            payload=payload,
        )

    async def notify_request_status_changed(
        self,
        *,
        actor_user_id: str,
        recipient_user_id: str,
        request_id: str,
        previous_status: str,
        new_status: str,
    ) -> UserNotification | None:
        if actor_user_id == recipient_user_id:
            return None
        return await self.create_for_user(
            user_id=recipient_user_id,
            notification_type="request.status_changed",
            severity="info",
            title="Статус заявки изменен",
            body=f"Заявка №{request_id}: {previous_status} -> {new_status}.",
            entity_type="request",
            entity_id=_as_optional_int(request_id),
            link_url=f"/requests/{request_id}",
            payload={
                "request_id": request_id,
                "previous_status": previous_status,
                "new_status": new_status,
            },
        )

    async def notify_system_warning(
        self,
        *,
        recipient_user_id: str,
        title: str,
        body: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        link_url: str | None = None,
        payload: dict | None = None,
    ) -> UserNotification:
        return await self.create_for_user(
            user_id=recipient_user_id,
            notification_type="system.warning",
            severity="warning",
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            link_url=link_url,
            payload=payload,
        )

    async def emit_created_event(self, notification: UserNotification) -> None:
        await self._send_created_event_best_effort(notification)

    def _ensure_supported_type(self, value: str) -> None:
        if value not in NOTIFICATION_TYPES:
            raise ValueError(f"Unsupported notification type: {value}")

    def _ensure_supported_severity(self, value: str) -> None:
        if value not in NOTIFICATION_SEVERITIES:
            raise ValueError(f"Unsupported notification severity: {value}")

    async def _send_created_event_best_effort(self, notification: UserNotification) -> None:
        try:
            sender = await self._resolve_realtime_sender()
            if sender is None:
                return
            payload = notification.payload if isinstance(notification.payload, dict) else {}
            tracking_only = str(payload.get("tracking_only") or "").strip().lower()
            if tracking_only == "true":
                return
            process_event_id = payload.get("event_id")
            normalized_event_id = str(process_event_id).strip() if process_event_id is not None else ""

            envelope_kwargs = {
                "type": "notification.created",
                "data": {
                    "notification": notification_to_realtime_dict(notification),
                    "has_unread": True,
                },
            }
            if normalized_event_id:
                envelope_kwargs["event_id"] = normalized_event_id
            envelope = OutboundEnvelope(**envelope_kwargs)
            delivered = await sender(user_id=notification.user_id, event=envelope)
            if not delivered:
                logger.debug(
                    "Realtime notification not delivered because user is offline: user_id=%s notification_id=%s",
                    notification.user_id,
                    notification.id,
                )
                return
            if self._resolve_toast_channel(payload) == _SYSTEM_TOAST_CHANNEL:
                await sender(
                    user_id=notification.user_id,
                    event=OutboundEnvelope(
                        type="system.toast",
                        data={
                            "title": notification.title,
                            "message": notification.body,
                            "severity": notification.severity,
                            "link_url": notification.link_url,
                            "notification_id": notification.id,
                        },
                    ),
                )
        except Exception:
            logger.exception(
                "Failed to send realtime notification event: user_id=%s notification_id=%s",
                notification.user_id,
                notification.id,
            )

    async def _resolve_realtime_sender(self) -> RealtimeNotificationSender | None:
        if self._realtime_sender is not None:
            return self._realtime_sender
        try:
            # Local import prevents circular dependency between realtime runtime and notification service.
            from app.realtime.runtime import get_unified_realtime_runtime

            runtime = get_unified_realtime_runtime()
            return runtime.send_to_user
        except Exception:
            logger.exception("Realtime runtime is unavailable for notification delivery")
            return None

    @staticmethod
    def _resolve_toast_channel(payload: dict | None) -> str | None:
        if not isinstance(payload, dict):
            return None
        raw_channel = payload.get("toast_channel")
        if raw_channel is None:
            return None
        normalized_channel = str(raw_channel).strip().lower()
        return normalized_channel or None


def notification_to_dict(notification: UserNotification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "type": notification.type,
        "severity": notification.severity,
        "title": notification.title,
        "body": notification.body,
        "entity_type": notification.entity_type,
        "entity_id": notification.entity_id,
        "link_url": notification.link_url,
        "payload": notification.payload or {},
        "read_at": _as_datetime(notification.read_at, allow_none=True),
        "created_at": _as_datetime(notification.created_at),
    }


def notification_to_realtime_dict(notification: UserNotification) -> dict:
    payload = notification_to_dict(notification)
    payload.pop("user_id", None)
    return payload


def _as_datetime(value, *, allow_none: bool = False) -> datetime | None:
    if allow_none and value is None:
        return None
    if isinstance(value, datetime):
        return value
    raise ValueError("Expected datetime value")

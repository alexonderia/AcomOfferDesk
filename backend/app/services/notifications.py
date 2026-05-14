from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.domain.exceptions import NotFound
from app.domain.notifications import (
    NOTIFICATION_SEVERITIES,
    NOTIFICATION_TYPES,
    sanitize_notification_error_message,
)
from app.models.orm_models import UserNotification
from app.repositories.notifications import NotificationRepository


class NotificationService:
    def __init__(self, notifications: NotificationRepository):
        self._notifications = notifications

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
        return await self._notifications.create(notification)

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
        created: list[UserNotification] = []
        seen: set[str] = set()
        for user_id in user_ids:
            normalized = user_id.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            created.append(
                await self.create_for_user(
                    user_id=normalized,
                    notification_type=notification_type,
                    severity=severity,
                    title=title,
                    body=body,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    link_url=link_url,
                    payload=payload,
                )
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
            raise NotFound("Notification not found")
        return notification

    async def mark_all_as_read_for_current_user(self, *, user_id: str) -> int:
        return await self._notifications.mark_all_as_read(user_id=user_id)

    async def notify_offer_created(
        self,
        *,
        actor_user_id: str,
        recipient_user_id: str,
        request_id: int,
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
        request_id: int,
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
        request_id: int,
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
            entity_id=request_id,
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
        payload: dict | None = None,
    ) -> UserNotification:
        return await self.create_for_user(
            user_id=recipient_user_id,
            notification_type="system.warning",
            severity="warning",
            title=title,
            body=body,
            payload=payload,
        )

    def _ensure_supported_type(self, value: str) -> None:
        if value not in NOTIFICATION_TYPES:
            raise ValueError(f"Unsupported notification type: {value}")

    def _ensure_supported_severity(self, value: str) -> None:
        if value not in NOTIFICATION_SEVERITIES:
            raise ValueError(f"Unsupported notification severity: {value}")


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


def _as_datetime(value, *, allow_none: bool = False) -> datetime | None:
    if allow_none and value is None:
        return None
    if isinstance(value, datetime):
        return value
    raise ValueError("Expected datetime value")

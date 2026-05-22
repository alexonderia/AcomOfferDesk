from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.repositories.notifications import NotificationRepository
from app.services.notifications import NotificationService
from shared.process_notifications import ProcessNotificationEvent

logger = logging.getLogger(__name__)


def _normalize_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_user_ids(values: Sequence[Any]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        user_id = _normalize_optional_str(raw_value)
        if user_id is None or user_id in seen:
            continue
        seen.add(user_id)
        normalized.append(user_id)
    return normalized


def _status_severity(status: str | None) -> str:
    normalized = (status or "").strip().lower()
    if normalized in {"active", "approved"}:
        return "success"
    if normalized in {"inactive", "rejected"}:
        return "warning"
    if normalized in {"blacklist", "blocked"}:
        return "error"
    return "info"


class ProcessNotificationEventHandler:
    async def handle(self, *, payload: dict) -> None:
        try:
            event = ProcessNotificationEvent.parse(payload)
        except ValueError as exc:
            logger.warning("Skip invalid process notification event payload: %s", exc)
            return

        async with UnitOfWork() as uow:
            notifications_repo = uow.notifications
            if notifications_repo is None:
                logger.warning("Notifications repository is unavailable in UnitOfWork")
                return
            service = NotificationService(notifications_repo)
            await self._dispatch(uow=uow, service=service, repo=notifications_repo, event=event)

    async def _dispatch(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        if event.event_type == "offer.created":
            await self._handle_offer_created(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "offer.status_changed":
            await self._handle_offer_status_event(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "message.created":
            await self._handle_message_created(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "request.files_changed":
            await self._handle_request_files_changed(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "offer.updated":
            await self._handle_offer_updated(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "request.created":
            await self._handle_request_created(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "request.responsible_changed":
            await self._handle_request_responsible_changed(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "request.deadline_changed":
            await self._handle_request_deadline_changed(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "request.status_changed":
            await self._handle_request_status_changed(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "user.status_changed":
            await self._handle_user_status_changed(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "user.review_required":
            await self._handle_user_review_required(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "plan.assigned":
            await self._handle_plan_assigned(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "plan.updated":
            await self._handle_plan_updated(uow=uow, service=service, repo=repo, event=event)
            return
        if event.event_type == "system.warning":
            await self._handle_system_warning(uow=uow, service=service, repo=repo, event=event)
            return
        logger.warning("Unsupported process notification event type: %s", event.event_type)

    async def _handle_offer_created(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        recipient_user_id = _normalize_optional_str((event.payload or {}).get("recipient_user_id"))
        if recipient_user_id is None and uow.requests is not None and event.request_id is not None:
            request_row = await uow.requests.get_by_id(request_id=event.request_id)
            recipient_user_id = _normalize_optional_str(getattr(request_row, "id_user", None)) if request_row is not None else None

        if recipient_user_id is None:
            logger.warning("Skip offer.created event without resolved recipient: event_id=%s", event.event_id)
            return
        eligible_recipients = await self._filter_center_recipients(uow=uow, user_ids=[recipient_user_id])
        if not eligible_recipients:
            return
        recipient_user_id = eligible_recipients[0]
        if event.actor_user_id is not None and event.actor_user_id == recipient_user_id:
            return
        if await self._is_duplicate(repo=repo, user_id=recipient_user_id, notification_type=event.event_type, event=event):
            return

        link_url = f"/requests/{event.request_id}" if event.request_id is not None else None
        if link_url is None and event.offer_id is not None:
            link_url = f"/offers/{event.offer_id}/workspace"

        await service.create_for_user(
            user_id=recipient_user_id,
            notification_type="offer.created",
            severity="info",
            title="Новое коммерческое предложение",
            body=f"По заявке №{event.request_id} создано новое КП." if event.request_id is not None else "Создано новое КП.",
            entity_type="offer",
            entity_id=event.offer_id,
            link_url=link_url,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "offer_id": event.offer_id,
                "actor_user_id": event.actor_user_id,
                "recipient_user_id": recipient_user_id,
            },
        )

    async def _handle_message_created(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        if "recipient_user_ids" in payload:
            raw_recipients = payload.get("recipient_user_ids")
            is_sequence = isinstance(raw_recipients, Sequence) and not isinstance(raw_recipients, (str, bytes))
            recipients = _normalize_user_ids(raw_recipients if is_sequence else [])
        elif "recipients" in payload:
            raw_recipients = payload.get("recipients")
            is_sequence = isinstance(raw_recipients, Sequence) and not isinstance(raw_recipients, (str, bytes))
            recipients = _normalize_user_ids(raw_recipients if is_sequence else [])
        else:
            recipients = []

        if "recipient_user_ids" not in payload and "recipients" not in payload and uow.chats is not None and event.chat_id is not None:
            recipients = await uow.chats.list_active_participant_user_ids(chat_id=event.chat_id)
            recipients = _normalize_user_ids(recipients)
        if event.actor_user_id is not None:
            recipients = [user_id for user_id in recipients if user_id != event.actor_user_id]
        recipients = await self._filter_center_recipients(uow=uow, user_ids=recipients)
        if not recipients:
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="message.created",
            severity="info",
            title="Новое сообщение",
            body=f"В чате по заявке №{event.request_id} появилось новое сообщение."
            if event.request_id is not None
            else "В чате появилось новое сообщение.",
            entity_type="message",
            entity_id=event.message_id,
            link_url=f"/offers/{event.offer_id}/workspace" if event.offer_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "offer_id": event.offer_id,
                "chat_id": event.chat_id,
                "message_id": event.message_id,
                "actor_user_id": event.actor_user_id,
            },
        )

    async def _handle_offer_status_event(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        new_status = _normalize_optional_str(payload.get("new_status")) or ""
        title_map = {
            "accepted": "Коммерческое предложение принято",
            "rejected": "Коммерческое предложение отклонено",
            "deleted": "Коммерческое предложение удалено",
        }
        title = title_map.get(new_status, "Статус коммерческого предложения изменен")
        recipients = _normalize_user_ids(payload.get("recipient_user_ids") or payload.get("recipients") or [])
        if not recipients and uow.requests is not None and event.request_id is not None:
            request_row = await uow.requests.get_by_id(request_id=event.request_id)
            owner_id = _normalize_optional_str(getattr(request_row, "id_user", None)) if request_row is not None else None
            recipients = _normalize_user_ids([owner_id])

        if event.actor_user_id is not None:
            recipients = [user_id for user_id in recipients if user_id != event.actor_user_id]
        recipients = await self._filter_center_recipients(uow=uow, user_ids=recipients)
        if not recipients:
            logger.warning("Skip %s event without resolved recipients: event_id=%s", event.event_type, event.event_id)
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="offer.status_changed",
            severity="info",
            title=title,
            body=f"По заявке №{event.request_id} изменен статус КП." if event.request_id is not None else "Изменен статус коммерческого предложения.",
            entity_type="offer",
            entity_id=event.offer_id,
            link_url=f"/offers/{event.offer_id}/workspace" if event.offer_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "offer_id": event.offer_id,
                "actor_user_id": event.actor_user_id,
                "old_status": _normalize_optional_str(payload.get("old_status")),
                "new_status": _normalize_optional_str(payload.get("new_status")),
            },
        )

    async def _handle_request_status_changed(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        previous_status = _normalize_optional_str(payload.get("old_status") or payload.get("previous_status")) or "-"
        new_status = _normalize_optional_str(payload.get("new_status")) or "-"

        recipients: list[str] = []
        request_row = None
        if uow.requests is not None and event.request_id is not None:
            request_row = await uow.requests.get_by_id(request_id=event.request_id)

        responsible_user_id = _normalize_optional_str(payload.get("responsible_user_id") or payload.get("recipient_user_id"))
        if responsible_user_id is None and request_row is not None:
            responsible_user_id = _normalize_optional_str(getattr(request_row, "id_user", None))

        if new_status == "open" and event.request_id is not None:
            if responsible_user_id is not None:
                recipients.append(responsible_user_id)
            recipients.extend(
                await self._collect_visible_contractor_recipients_for_request(
                    uow=uow,
                    request_id=event.request_id,
                )
            )
        elif responsible_user_id is not None:
            recipients.append(responsible_user_id)

        if event.actor_user_id is not None:
            recipients = [user_id for user_id in recipients if user_id != event.actor_user_id]
        recipients = await self._filter_center_recipients(uow=uow, user_ids=recipients)
        if not recipients:
            logger.warning("Skip request.status_changed event without resolved recipients: event_id=%s", event.event_id)
            return
        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="request.status_changed",
            severity="info",
            title="Статус заявки изменен",
            body=f"Заявка №{event.request_id}: {previous_status} -> {new_status}."
            if event.request_id is not None
            else f"Статус заявки изменен: {previous_status} -> {new_status}.",
            entity_type="request",
            entity_id=event.request_id,
            link_url=f"/requests/{event.request_id}" if event.request_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "old_status": previous_status,
                "new_status": new_status,
                "actor_user_id": event.actor_user_id,
            },
        )

    async def _handle_request_created(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        recipients: list[str] = []
        responsible_user_id = _normalize_optional_str(payload.get("responsible_user_id"))
        if event.request_id is not None and uow.requests is not None:
            request_row = await uow.requests.get_by_id(request_id=event.request_id)
            if request_row is not None:
                responsible_user_id = _normalize_optional_str(getattr(request_row, "id_user", None)) or responsible_user_id
            recipients.extend(
                await self._collect_visible_contractor_recipients_for_request(
                    uow=uow,
                    request_id=event.request_id,
                )
            )
        elif not recipients:
            recipients = _normalize_user_ids(payload.get("recipient_user_ids") or payload.get("recipients") or [])
        recipients = _normalize_user_ids([responsible_user_id, *recipients])

        if event.actor_user_id is not None:
            recipients = [user_id for user_id in recipients if user_id != event.actor_user_id]
        recipients = await self._filter_center_recipients(uow=uow, user_ids=recipients)
        if not recipients:
            logger.warning("Skip request.created event due to ambiguous recipients: event_id=%s", event.event_id)
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="request.created",
            severity="info",
            title="Новая заявка",
            body=f"Создана новая заявка №{event.request_id}." if event.request_id is not None else "Создана новая заявка.",
            entity_type="request",
            entity_id=event.request_id,
            link_url=f"/requests/{event.request_id}" if event.request_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "actor_user_id": event.actor_user_id,
            },
        )

    async def _handle_request_files_changed(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        if uow.requests is None or uow.offers is None:
            logger.warning("Skip request.files_changed due to missing repositories")
            return
        if event.request_id is None:
            logger.warning("Skip request.files_changed without request_id: event_id=%s", event.event_id)
            return

        payload = event.payload or {}
        request_row = await uow.requests.get_by_id(request_id=event.request_id)
        recipients = []
        if request_row is not None:
            recipients.append(getattr(request_row, "id_user", None))
        offer_rows = await uow.offers.list_by_request(request_id=event.request_id)
        recipients.extend(
            offer.id_user
            for offer in offer_rows
            if offer.status in {"submitted", "accepted"}
        )
        normalized_recipients = _normalize_user_ids(recipients)
        if event.actor_user_id is not None:
            normalized_recipients = [user_id for user_id in normalized_recipients if user_id != event.actor_user_id]
        normalized_recipients = await self._filter_center_recipients(uow=uow, user_ids=normalized_recipients)
        if not normalized_recipients:
            logger.info("Skip request.files_changed without recipients: event_id=%s", event.event_id)
            return

        filtered_recipients: list[str] = []
        for user_id in normalized_recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="request.files_changed",
            severity="info",
            title="Изменены файлы заявки",
            body=f"По заявке №{event.request_id} обновлены вложения.",
            entity_type="request",
            entity_id=event.request_id,
            link_url=f"/requests/{event.request_id}",
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "file_ids": payload.get("file_ids"),
                "changed_file_count": payload.get("changed_file_count"),
                "actor_user_id": event.actor_user_id,
            },
        )

    async def _handle_offer_updated(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        if uow.offers is None or uow.requests is None:
            logger.warning("Skip offer.updated due to missing repositories")
            return

        payload = event.payload or {}
        request_id = event.request_id
        if request_id is None and event.offer_id is not None:
            offer_row = await uow.offers.get_by_id(offer_id=event.offer_id)
            request_id = offer_row.id_request if offer_row is not None else None
        if request_id is None:
            logger.warning("Skip offer.updated without request_id: event_id=%s", event.event_id)
            return

        offer_row = await uow.offers.get_by_id(offer_id=event.offer_id) if event.offer_id is not None else None
        request_row = await uow.requests.get_by_id(request_id=request_id)
        responsible_user_id = _normalize_optional_str(getattr(request_row, "id_user", None)) if request_row is not None else None
        offer_author_user_id = _normalize_optional_str((payload or {}).get("offer_author_user_id"))
        if offer_author_user_id is None and offer_row is not None:
            offer_author_user_id = _normalize_optional_str(getattr(offer_row, "id_user", None))

        recipients = _normalize_user_ids([responsible_user_id, offer_author_user_id])
        if event.actor_user_id is not None:
            recipients = [user_id for user_id in recipients if user_id != event.actor_user_id]
        recipients = await self._filter_center_recipients(uow=uow, user_ids=recipients)
        if not recipients:
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="offer.updated",
            severity="info",
            title="КП обновлено",
            body="По коммерческому предложению сохранены изменения.",
            entity_type="offer",
            entity_id=event.offer_id,
            link_url=f"/offers/{event.offer_id}/workspace" if event.offer_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": request_id,
                "offer_id": event.offer_id,
                "offer_author_user_id": offer_author_user_id,
                "file_ids": payload.get("file_ids"),
                "changed_file_count": payload.get("changed_file_count"),
                "old_offer_amount": payload.get("old_offer_amount"),
                "new_offer_amount": payload.get("new_offer_amount"),
                "actor_user_id": event.actor_user_id,
            },
        )

    async def _handle_user_status_changed(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        if uow.users is None or uow.profiles is None:
            logger.warning("Skip user.status_changed due to missing repositories")
            return
        payload = event.payload or {}
        actor_user_id = event.actor_user_id
        target_user_id = _normalize_optional_str(payload.get("target_user_id"))
        old_status = _normalize_optional_str(payload.get("old_status"))
        new_status = _normalize_optional_str(payload.get("new_status"))

        rows = await uow.users.list_by_role_ids_with_profiles_and_roles(
            role_ids=[settings.admin_role_id, settings.superadmin_role_id],
        )
        recipients = _normalize_user_ids(
            user.id for user, _, _ in rows if user.id != actor_user_id
        )
        if not recipients:
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        target_descriptor = target_user_id or "-"
        target_profile = await uow.profiles.get_by_id(target_user_id) if target_user_id is not None else None
        if target_profile is not None:
            target_descriptor = target_profile.full_name or target_profile.mail or target_descriptor

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="user.status_changed",
            severity=_status_severity(new_status),
            title="Изменен статус пользователя",
            body=f"Изменен статус пользователя {target_descriptor}.",
            entity_type="user",
            entity_id=None,
            link_url="/admin/users",
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "target_user_id": target_user_id,
                "old_status": old_status,
                "new_status": new_status,
                "target_role": payload.get("target_role"),
                "actor_user_id": actor_user_id,
                "email_notification_queued": payload.get("email_notification_queued"),
                "email_notification_reason": payload.get("email_notification_reason"),
            },
        )

    async def _handle_user_review_required(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        if uow.users is None or uow.profiles is None:
            logger.warning("Skip user.review_required due to missing repositories")
            return
        payload = event.payload or {}
        target_user_id = _normalize_optional_str(payload.get("target_user_id"))
        actor_user_id = event.actor_user_id

        rows = await uow.users.list_by_role_ids_with_profiles_and_roles(
            role_ids=[settings.admin_role_id, settings.superadmin_role_id],
        )
        recipients = _normalize_user_ids(
            user.id for user, _, _ in rows if user.id != actor_user_id
        )
        if not recipients:
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        target_descriptor = target_user_id or "-"
        target_profile = await uow.profiles.get_by_id(target_user_id) if target_user_id is not None else None
        if target_profile is not None:
            target_descriptor = target_profile.full_name or target_profile.mail or target_descriptor

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="user.review_required",
            severity="warning",
            title="Пользователь ожидает модерации",
            body=f"Требуется проверка пользователя {target_descriptor}.",
            entity_type="user",
            entity_id=None,
            link_url="/admin/users",
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "target_user_id": target_user_id,
                "target_role": payload.get("target_role"),
                "actor_user_id": actor_user_id,
                "source": payload.get("source"),
            },
        )

    async def _handle_request_responsible_changed(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        old_responsible = _normalize_optional_str(payload.get("old_responsible_user_id"))
        new_responsible = _normalize_optional_str(payload.get("new_responsible_user_id"))
        recipients: list[str] = []
        if old_responsible is not None:
            include_old = True
            if uow.users is not None:
                old_user = await uow.users.get_by_id(old_responsible)
                if old_user is not None and getattr(old_user, "id_role", None) == settings.operator_role_id:
                    include_old = False
            if include_old:
                recipients.append(old_responsible)
        recipients = _normalize_user_ids([*recipients, new_responsible])
        if event.actor_user_id is not None:
            recipients = [user_id for user_id in recipients if user_id != event.actor_user_id]
        recipients = await self._filter_center_recipients(uow=uow, user_ids=recipients)
        if not recipients:
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="request.responsible_changed",
            severity="info",
            title="Изменен ответственный по заявке",
            body=f"По заявке №{event.request_id} изменен ответственный." if event.request_id is not None else "Изменен ответственный по заявке.",
            entity_type="request",
            entity_id=event.request_id,
            link_url=f"/requests/{event.request_id}" if event.request_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "old_responsible_user_id": old_responsible,
                "new_responsible_user_id": new_responsible,
                "actor_user_id": event.actor_user_id,
            },
        )

    async def _handle_request_deadline_changed(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        recipient_user_id = _normalize_optional_str(payload.get("responsible_user_id"))
        if recipient_user_id is None:
            logger.warning("Skip request.deadline_changed event without responsible user: event_id=%s", event.event_id)
            return
        eligible_recipients = await self._filter_center_recipients(uow=uow, user_ids=[recipient_user_id])
        if not eligible_recipients:
            return
        recipient_user_id = eligible_recipients[0]
        if event.actor_user_id is not None and event.actor_user_id == recipient_user_id:
            return
        if await self._is_duplicate(repo=repo, user_id=recipient_user_id, notification_type=event.event_type, event=event):
            return

        await service.create_for_user(
            user_id=recipient_user_id,
            notification_type="request.deadline_changed",
            severity="info",
            title="Изменен срок заявки",
            body=f"По заявке №{event.request_id} изменен срок." if event.request_id is not None else "Изменен срок заявки.",
            entity_type="request",
            entity_id=event.request_id,
            link_url=f"/requests/{event.request_id}" if event.request_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "old_deadline": _normalize_optional_str(payload.get("old_deadline")),
                "new_deadline": _normalize_optional_str(payload.get("new_deadline")),
                "actor_user_id": event.actor_user_id,
            },
        )

    async def _handle_system_warning(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        recipients = _normalize_user_ids(payload.get("recipients") or payload.get("recipient_user_ids") or [])
        recipient_user_id = _normalize_optional_str(payload.get("recipient_user_id"))
        if recipient_user_id is not None:
            recipients = _normalize_user_ids([recipient_user_id, *recipients])

        if not recipients:
            logger.warning("Skip system.warning event without explicit recipients: event_id=%s", event.event_id)
            return
        recipients = await self._filter_center_recipients(uow=uow, user_ids=recipients)
        if not recipients:
            return

        title = _normalize_optional_str(payload.get("title")) or "Системное предупреждение"
        body = _normalize_optional_str(payload.get("body")) or "Проверьте последние изменения в системе."
        link_url = _normalize_optional_str(payload.get("link_url"))

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="system.warning",
            severity="warning",
            title=title,
            body=body,
            entity_type=event.entity_type,
            entity_id=int(event.entity_id) if event.entity_id and event.entity_id.isdigit() else None,
            link_url=link_url,
            payload={
                **payload,
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
            },
        )

    async def _handle_plan_assigned(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        recipient_user_id = _normalize_optional_str(payload.get("responsible_user_id"))
        if recipient_user_id is None:
            logger.info("Skip plan.assigned event without responsible_user_id: event_id=%s", event.event_id)
            return
        eligible_recipients = await self._filter_center_recipients(uow=uow, user_ids=[recipient_user_id])
        if not eligible_recipients:
            return
        recipient_user_id = eligible_recipients[0]
        if event.actor_user_id is not None and event.actor_user_id == recipient_user_id:
            return
        if await self._is_duplicate(repo=repo, user_id=recipient_user_id, notification_type=event.event_type, event=event):
            return

        plan_id_raw = payload.get("plan_id")
        plan_id = int(plan_id_raw) if isinstance(plan_id_raw, int) or (isinstance(plan_id_raw, str) and plan_id_raw.isdigit()) else None
        await service.create_for_user(
            user_id=recipient_user_id,
            notification_type="plan.assigned",
            severity="info",
            title="Назначен план",
            body="Вам назначен план по экономии.",
            entity_type="plan",
            entity_id=plan_id,
            link_url="/pm-dashboard/plan",
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "plan_id": plan_id,
                "responsible_user_id": recipient_user_id,
                "actor_user_id": event.actor_user_id,
                "assigned_by_user_id": _normalize_optional_str(payload.get("assigned_by_user_id")),
                "parent_plan_id": payload.get("parent_plan_id"),
                "plan_sum": payload.get("plan_sum"),
                "period": payload.get("period"),
                "period_start": payload.get("period_start"),
                "period_end": payload.get("period_end"),
            },
        )

    async def _handle_plan_updated(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
    ) -> None:
        payload = event.payload or {}
        recipient_user_id = _normalize_optional_str(payload.get("responsible_user_id"))
        if recipient_user_id is None:
            logger.info("Skip plan.updated event without responsible_user_id: event_id=%s", event.event_id)
            return
        eligible_recipients = await self._filter_center_recipients(uow=uow, user_ids=[recipient_user_id])
        if not eligible_recipients:
            return
        recipient_user_id = eligible_recipients[0]
        if event.actor_user_id is not None and event.actor_user_id == recipient_user_id:
            return
        if await self._is_duplicate(repo=repo, user_id=recipient_user_id, notification_type=event.event_type, event=event):
            return

        plan_id_raw = payload.get("plan_id")
        plan_id = int(plan_id_raw) if isinstance(plan_id_raw, int) or (isinstance(plan_id_raw, str) and plan_id_raw.isdigit()) else None
        await service.create_for_user(
            user_id=recipient_user_id,
            notification_type="plan.updated",
            severity="info",
            title="План изменен",
            body="Ваш план по экономии был обновлен.",
            entity_type="plan",
            entity_id=plan_id,
            link_url="/pm-dashboard/plan",
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "plan_id": plan_id,
                "responsible_user_id": recipient_user_id,
                "actor_user_id": event.actor_user_id,
                "assigned_by_user_id": _normalize_optional_str(payload.get("assigned_by_user_id")),
                "parent_plan_id": payload.get("parent_plan_id"),
                "plan_sum": payload.get("plan_sum"),
                "old_plan_sum": payload.get("old_plan_sum"),
                "new_plan_sum": payload.get("new_plan_sum"),
                "period": payload.get("period"),
                "old_period_end": payload.get("old_period_end"),
                "new_period_end": payload.get("new_period_end"),
                "period_start": payload.get("period_start"),
                "period_end": payload.get("period_end"),
            },
        )

    async def _is_duplicate(
        self,
        *,
        repo: NotificationRepository,
        user_id: str,
        notification_type: str,
        event: ProcessNotificationEvent,
    ) -> bool:
        if await repo.exists_by_type_user_and_payload_key(
            user_id=user_id,
            notification_type=notification_type,
            key_name="event_id",
            key_value=event.event_id,
        ):
            logger.info(
                "Skip duplicate process notification by event_id: type=%s user_id=%s event_id=%s",
                notification_type,
                user_id,
                event.event_id,
            )
            return True
        if event.dedupe_key and await repo.exists_by_type_user_and_payload_key(
            user_id=user_id,
            notification_type=notification_type,
            key_name="dedupe_key",
            key_value=event.dedupe_key,
        ):
            logger.info(
                "Skip duplicate process notification by dedupe_key: type=%s user_id=%s dedupe_key=%s",
                notification_type,
                user_id,
                event.dedupe_key,
            )
            return True
        return False

    async def _collect_visible_contractor_recipients_for_request(
        self,
        *,
        uow: UnitOfWork,
        request_id: int,
    ) -> list[str]:
        if uow.requests is None:
            return []
        return await uow.requests.list_active_keycloak_visible_contractor_user_ids(
            request_id=request_id,
            contractor_role_id=settings.contractor_role_id,
        )

    async def _filter_center_recipients(
        self,
        *,
        uow: UnitOfWork,
        user_ids: Sequence[str],
    ) -> list[str]:
        normalized = _normalize_user_ids(user_ids)
        if not normalized:
            return []
        if uow.users is None or uow.user_auth_accounts is None:
            logger.warning("Skip notification recipients filtering due to missing repositories")
            return []

        role_rows = await uow.users.list_by_ids_with_profiles_and_roles(user_ids=normalized)
        role_by_user_id = {user.id: user.id_role for user, _, _ in role_rows}
        filtered: list[str] = []
        keycloak_cache: dict[str, bool] = {}
        for user_id in normalized:
            role_id = role_by_user_id.get(user_id)
            if role_id is None:
                continue
            if role_id != settings.contractor_role_id:
                filtered.append(user_id)
                continue
            is_keycloak_eligible = keycloak_cache.get(user_id)
            if is_keycloak_eligible is None:
                account = await uow.user_auth_accounts.get_by_user_provider(
                    user_id=user_id,
                    provider="keycloak",
                )
                is_keycloak_eligible = account is not None
                keycloak_cache[user_id] = is_keycloak_eligible
            if is_keycloak_eligible:
                filtered.append(user_id)
        return filtered

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.repositories.notifications import NotificationRepository
from app.services.notifications import NotificationService
from shared.normalization import as_optional_int as _as_optional_int
from shared.normalization import normalize_optional_str as _normalize_optional_str
from shared.notification_copy import (
    message_created_body,
    message_created_title,
    offer_created_body,
    offer_created_title,
    offer_status_changed_body,
    offer_status_changed_title,
    offer_updated_body,
    offer_updated_title,
    request_created_body,
    request_created_title,
    request_deadline_changed_body,
    request_deadline_changed_title,
    request_files_changed_body,
    request_files_changed_title,
    request_status_changed_body,
    request_status_changed_title,
)
from shared.process_notifications import ProcessNotificationEvent

logger = logging.getLogger(__name__)


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


_PROFILE_PLACEHOLDER_VALUES = frozenset({"не указано", "-"})
_CONTRACTOR_REGISTRATION_SOURCES = frozenset({"contractor_tg", "oidc_invite"})
_CONTRACTOR_CREATION_SOURCES = frozenset({"manual_contractor"})
_USER_STATUS_LABELS = {
    "review": "На проверке",
    "active": "Активен",
    "inactive": "Неактивен",
    "blacklist": "В черном списке",
}


def _is_missing_profile_value(value: str | None) -> bool:
    normalized = _normalize_optional_str(value)
    if normalized is None:
        return True
    return normalized.casefold() in _PROFILE_PLACEHOLDER_VALUES


def _resolve_user_target_descriptor(
    *,
    target_user_id: str | None,
    target_profile: Any | None = None,
) -> str:
    login = target_user_id or "-"
    if target_profile is None:
        return login

    full_name = _normalize_optional_str(getattr(target_profile, "full_name", None))
    if full_name is not None and not _is_missing_profile_value(full_name):
        return full_name

    mail = _normalize_optional_str(getattr(target_profile, "mail", None))
    if mail is not None and not _is_missing_profile_value(mail):
        return mail

    return login


def _is_contractor_lifecycle_target(*, payload: dict[str, Any]) -> bool:
    target_role = payload.get("target_role")
    if target_role == settings.contractor_role_id:
        return True
    if payload.get("target_is_contractor") is True:
        return True
    source = _normalize_optional_str(payload.get("source"))
    return source in _CONTRACTOR_REGISTRATION_SOURCES or source in _CONTRACTOR_CREATION_SOURCES


def _format_user_status_label(value: str | None) -> str:
    normalized = _normalize_optional_str(value)
    if normalized is None:
        return "-"
    return _USER_STATUS_LABELS.get(normalized, normalized)


def _request_entity_id(request_id: str | None) -> int | None:
    return _as_optional_int(request_id)


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
            title=offer_created_title(),
            body=offer_created_body(request_id=event.request_id),
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
            title=message_created_title(),
            body=message_created_body(request_id=event.request_id)
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
        title = offer_status_changed_title(new_status=new_status)
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
            body=offer_status_changed_body(request_id=event.request_id),
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
            title=request_status_changed_title(),
            body=request_status_changed_body(
                request_id=event.request_id,
                previous_status=previous_status,
                new_status=new_status,
            ),
            entity_type="request",
            entity_id=_request_entity_id(event.request_id),
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
            title=request_created_title(),
            body=request_created_body(request_id=event.request_id),
            entity_type="request",
            entity_id=_request_entity_id(event.request_id),
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
            title=request_files_changed_title(),
            body=request_files_changed_body(request_id=event.request_id),
            entity_type="request",
            entity_id=_request_entity_id(event.request_id),
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
            title=offer_updated_title(),
            body=offer_updated_body(request_id=request_id),
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
        is_contractor_target = _is_contractor_lifecycle_target(payload=payload)

        recipient_role_ids = [settings.admin_role_id, settings.superadmin_role_id]
        if is_contractor_target:
            recipient_role_ids.append(settings.security_officer_role_id)
        rows = await uow.users.list_by_role_ids_with_profiles_and_roles(
            role_ids=recipient_role_ids,
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

        target_profile = await uow.profiles.get_by_id(target_user_id) if target_user_id is not None else None
        target_descriptor = _resolve_user_target_descriptor(
            target_user_id=target_user_id,
            target_profile=target_profile,
        )
        old_status_label = _format_user_status_label(old_status)
        new_status_label = _format_user_status_label(new_status)
        title = "Изменен статус контрагента" if is_contractor_target else "Изменен статус пользователя"
        body = (
            f"Изменен статус контрагента {target_descriptor}: {old_status_label} -> {new_status_label}."
            if is_contractor_target
            else f"Изменен статус пользователя {target_descriptor}."
        )
        link_url = "/contractors" if is_contractor_target else "/admin/users"

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="user.status_changed",
            severity=_status_severity(new_status),
            title=title,
            body=body,
            entity_type="user",
            entity_id=None,
            link_url=link_url,
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
        is_contractor_target = _is_contractor_lifecycle_target(payload=payload)
        source = _normalize_optional_str(payload.get("source"))

        recipient_role_ids = [settings.admin_role_id, settings.superadmin_role_id]
        if is_contractor_target:
            recipient_role_ids.append(settings.security_officer_role_id)
        rows = await uow.users.list_by_role_ids_with_profiles_and_roles(
            role_ids=recipient_role_ids,
        )
        recipients = _normalize_user_ids(user.id for user, _, _ in rows)
        if not recipients:
            return

        filtered_recipients: list[str] = []
        for user_id in recipients:
            if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
                continue
            filtered_recipients.append(user_id)
        if not filtered_recipients:
            return

        target_profile = await uow.profiles.get_by_id(target_user_id) if target_user_id is not None else None
        target_descriptor = _resolve_user_target_descriptor(
            target_user_id=target_user_id,
            target_profile=target_profile,
        )
        title = "Пользователь ожидает модерации"
        body = f"Требуется проверка пользователя {target_descriptor}."
        link_url = "/admin/users"
        if is_contractor_target and source in _CONTRACTOR_REGISTRATION_SOURCES:
            title = "Зарегистрирован новый контрагент"
            body = f"Зарегистрирован новый контрагент: {target_descriptor}."
            link_url = "/contractors"
        elif is_contractor_target and source in _CONTRACTOR_CREATION_SOURCES:
            title = "Создан новый контрагент"
            body = f"Создан новый контрагент: {target_descriptor}."
            link_url = "/contractors"

        await service.create_many_for_users(
            user_ids=filtered_recipients,
            notification_type="user.review_required",
            severity="warning",
            title=title,
            body=body,
            entity_type="user",
            entity_id=None,
            link_url=link_url,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "target_user_id": target_user_id,
                "target_role": payload.get("target_role"),
                "actor_user_id": actor_user_id,
                "source": source,
            },
        )

    async def _is_operator_user(self, *, uow: UnitOfWork, user_id: str | None) -> bool:
        if user_id is None or uow.users is None or not callable(getattr(uow.users, "get_by_id", None)):
            return False
        user = await uow.users.get_by_id(user_id)
        return user is not None and getattr(user, "id_role", None) == settings.operator_role_id

    async def _create_request_responsible_notification(
        self,
        *,
        uow: UnitOfWork,
        service: NotificationService,
        repo: NotificationRepository,
        event: ProcessNotificationEvent,
        user_id: str,
        title: str,
        body: str,
        severity: str = "info",
        old_responsible: str | None,
        new_responsible: str | None,
        assigned_from_operator: bool,
    ) -> None:
        if await self._is_duplicate(repo=repo, user_id=user_id, notification_type=event.event_type, event=event):
            return
        eligible_recipients = await self._filter_center_recipients(uow=uow, user_ids=[user_id])
        if not eligible_recipients:
            return
        await service.create_for_user(
            user_id=user_id,
            notification_type="request.responsible_changed",
            severity=severity,
            title=title,
            body=body,
            entity_type="request",
            entity_id=_request_entity_id(event.request_id),
            link_url=f"/requests/{event.request_id}" if event.request_id is not None else None,
            payload={
                "event_id": event.event_id,
                "dedupe_key": event.dedupe_key,
                "request_id": event.request_id,
                "old_responsible_user_id": old_responsible,
                "new_responsible_user_id": new_responsible,
                "actor_user_id": event.actor_user_id,
                "assigned_from_operator": assigned_from_operator,
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
        if new_responsible is None:
            logger.warning(
                "Skip request.responsible_changed event without new responsible user: event_id=%s",
                event.event_id,
            )
            return

        assigned_from_operator = await self._is_operator_user(uow=uow, user_id=old_responsible)
        request_label = f"№{event.request_id}" if event.request_id is not None else ""

        if new_responsible != event.actor_user_id:
            if assigned_from_operator:
                assignee_title = "Вам назначена заявка"
                assignee_body = (
                    f"Вы назначены ответственным по заявке {request_label}."
                    if request_label
                    else "Вы назначены ответственным по заявке."
                )
            else:
                assignee_title = "Изменен ответственный по заявке"
                assignee_body = (
                    f"По заявке {request_label} вы назначены ответственным."
                    if request_label
                    else "По заявке вы назначены ответственным."
                )
            await self._create_request_responsible_notification(
                uow=uow,
                service=service,
                repo=repo,
                event=event,
                user_id=new_responsible,
                title=assignee_title,
                body=assignee_body,
                old_responsible=old_responsible,
                new_responsible=new_responsible,
                assigned_from_operator=assigned_from_operator,
            )

        if (
            old_responsible is not None
            and not assigned_from_operator
            and old_responsible != event.actor_user_id
            and old_responsible != new_responsible
        ):
            await self._create_request_responsible_notification(
                uow=uow,
                service=service,
                repo=repo,
                event=event,
                user_id=old_responsible,
                title="Изменен ответственный по заявке",
                body=(
                    f"По заявке {request_label} с вас снята ответственность."
                    if request_label
                    else "С вас снята ответственность по заявке."
                ),
                old_responsible=old_responsible,
                new_responsible=new_responsible,
                assigned_from_operator=assigned_from_operator,
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
            title=request_deadline_changed_title(),
            body=request_deadline_changed_body(request_id=event.request_id),
            entity_type="request",
            entity_id=_request_entity_id(event.request_id),
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
        request_id: str,
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

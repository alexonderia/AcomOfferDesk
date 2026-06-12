from __future__ import annotations

import logging
from typing import Literal

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.infrastructure.email.email_templates.contractor_event_email import build_contractor_event_email_payload
from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.services.max_notifications import (
    notify_offer_updated as notify_max_offer_updated,
    notify_request_deadline_changed as notify_max_request_deadline_changed,
    notify_request_files_changed as notify_max_request_files_changed,
    notify_request_status_changed as notify_max_request_status_changed,
)
from app.services.user_notification_preferences import UserNotificationPreferencesService
from shared.normalization import normalize_optional_str as _normalize_optional_str
from shared.notification_copy import (
    email_subject,
    message_unread_email_body,
    message_unread_email_body_html,
    message_unread_email_subject,
    offer_updated_body,
    plain_to_html_paragraph,
    request_deadline_changed_body,
    request_files_changed_body,
    request_status_changed_body,
)

logger = logging.getLogger(__name__)

RequestEventKind = Literal["status_changed", "deadline_changed", "files_changed"]


def _build_email_service() -> SMTPEmailService:
    return SMTPEmailService(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        username=settings.email_address,
        password=settings.email_app_password,
        from_address=settings.email_address,
        from_name=settings.email_from_name,
    )


def _resolve_action_url(*, request_id: str | None = None, offer_id: int | None = None) -> str | None:
    base_url = (settings.web_base_url or settings.public_backend_base_url or "").strip().rstrip("/")
    if not base_url:
        return None
    if offer_id is not None:
        return f"{base_url}/login?next=/offers/{offer_id}/workspace"
    if request_id is not None:
        return f"{base_url}/login?next=/requests/{request_id}/contractor"
    return f"{base_url}/login?next=/"


def _normalize_email(value: str | None) -> str | None:
    normalized = _normalize_optional_str(value)
    if normalized is None or normalized.lower() in {"не указано", "none", "null"}:
        return None
    return normalized


async def _resolve_contractor_email(*, uow: UnitOfWork, user_id: str) -> str | None:
    if uow.profiles is None:
        return None
    profile = await uow.profiles.get_by_id(user_id)
    if profile is None:
        return None
    return _normalize_email(profile.mail)


async def _notify_contractor_channels(
    *,
    uow: UnitOfWork,
    preferences: UserNotificationPreferencesService,
    contractor_user_id: str,
    notification_type: str,
    email_subject: str | None = None,
    email_body_text: str | None = None,
    email_body_html: str | None = None,
    action_url: str | None = None,
    action_label: str = "Открыть систему",
    request_id: str | None = None,
    offer_id: int | None = None,
    max_notify,
) -> None:
    if uow.users is None:
        return

    user = await uow.users.get_by_id(contractor_user_id)
    if user is None or user.id_role != settings.contractor_role_id or user.status != "active":
        return

    email_enabled = await preferences.is_channel_enabled(
        user_id=contractor_user_id,
        channel_type="email",
        notification_type=notification_type,
    )
    if email_enabled and email_subject and email_body_text and email_body_html:
        to_email = await _resolve_contractor_email(uow=uow, user_id=contractor_user_id)
        if to_email:
            payload = build_contractor_event_email_payload(
                to_email=to_email,
                subject=email_subject,
                body_text=email_body_text,
                body_html=email_body_html,
                action_url=action_url,
                action_label=action_label,
            )
            await _build_email_service().send_email(
                to_email=payload.to_email,
                subject=payload.subject,
                text_content=payload.text_content,
                html_content=payload.html_content,
                recipient_user_id=contractor_user_id,
                request_id=request_id,
                offer_id=offer_id,
                suppress_delivery_notification=True,
            )

    if settings.max_bot_enabled:
        max_enabled = await preferences.is_channel_enabled(
            user_id=contractor_user_id,
            channel_type="max",
            notification_type=notification_type,
        )
        if max_enabled:
            max_user_id = await uow.users.get_active_approved_contractor_max_id(
                user_id=contractor_user_id,
                contractor_role_id=settings.contractor_role_id,
            )
            if max_user_id is not None:
                await max_notify(max_user_id=max_user_id)


async def notify_contractors_with_offers_about_request(
    *,
    request_id: str,
    event_kind: RequestEventKind,
    actor_user_id: str | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
) -> None:
    async with UnitOfWork() as uow:
        if uow.offers is None or uow.user_contact_channels is None or uow.user_notification_preferences is None:
            return

        contractor_user_ids = await uow.offers.list_contractor_user_ids_for_request(
            request_id=request_id,
            contractor_role_id=settings.contractor_role_id,
        )
        if actor_user_id is not None:
            contractor_user_ids = [user_id for user_id in contractor_user_ids if user_id != actor_user_id]
        if not contractor_user_ids:
            return

        preferences = UserNotificationPreferencesService(
            uow.user_contact_channels,
            uow.user_notification_preferences,
            profiles=uow.profiles,
        )
        action_url = _resolve_action_url(request_id=request_id)

        if event_kind == "status_changed":
            body_text = request_status_changed_body(
                request_id=request_id,
                previous_status=previous_status,
                new_status=new_status,
            )
            subject = email_subject(f"статус заявки №{request_id} изменён")
            body_html = plain_to_html_paragraph(body_text)
            max_notify = lambda *, max_user_id: notify_max_request_status_changed(
                max_user_id=max_user_id,
                request_id=request_id,
                previous_status=previous_status,
                new_status=new_status,
            )
        elif event_kind == "deadline_changed":
            body_text = request_deadline_changed_body(request_id=request_id)
            subject = email_subject(f"срок заявки №{request_id} изменён")
            body_html = plain_to_html_paragraph(body_text)
            max_notify = lambda *, max_user_id: notify_max_request_deadline_changed(
                max_user_id=max_user_id,
                request_id=request_id,
            )
        else:
            body_text = request_files_changed_body(request_id=request_id)
            subject = email_subject(f"файлы заявки №{request_id} обновлены")
            body_html = plain_to_html_paragraph(body_text)
            max_notify = lambda *, max_user_id: notify_max_request_files_changed(
                max_user_id=max_user_id,
                request_id=request_id,
            )

        for contractor_user_id in contractor_user_ids:
            try:
                await _notify_contractor_channels(
                    uow=uow,
                    preferences=preferences,
                    contractor_user_id=contractor_user_id,
                    notification_type="request",
                    email_subject=subject,
                    email_body_text=body_text,
                    email_body_html=body_html,
                    action_url=action_url,
                    action_label="Открыть заявку",
                    request_id=request_id,
                    max_notify=max_notify,
                )
            except Exception:
                logger.exception(
                    "Failed contractor request notification: request_id=%s event=%s user_id=%s",
                    request_id,
                    event_kind,
                    contractor_user_id,
                )


async def notify_contractor_offer_updated(
    *,
    contractor_user_id: str,
    request_id: str,
    offer_id: int,
    actor_user_id: str | None = None,
) -> None:
    if actor_user_id is not None and actor_user_id == contractor_user_id:
        return

    async with UnitOfWork() as uow:
        if uow.user_contact_channels is None or uow.user_notification_preferences is None:
            return

        preferences = UserNotificationPreferencesService(
            uow.user_contact_channels,
            uow.user_notification_preferences,
            profiles=uow.profiles,
        )
        body_text = offer_updated_body(request_id=request_id)
        subject = email_subject(f"КП по заявке №{request_id} обновлено")
        body_html = plain_to_html_paragraph(body_text)

        await _notify_contractor_channels(
            uow=uow,
            preferences=preferences,
            contractor_user_id=contractor_user_id,
            notification_type="offer",
            email_subject=subject,
            email_body_text=body_text,
            email_body_html=body_html,
            action_url=_resolve_action_url(offer_id=offer_id),
            action_label="Открыть КП",
            request_id=request_id,
            offer_id=offer_id,
            max_notify=lambda *, max_user_id: notify_max_offer_updated(
                max_user_id=max_user_id,
                request_id=request_id,
            ),
        )


async def send_unread_chat_email_if_needed(
    *,
    message_id: int,
    recipient_user_id: str,
    request_id: str,
    offer_id: int,
) -> None:
    async with UnitOfWork() as uow:
        if (
            uow.messages is None
            or uow.users is None
            or uow.user_contact_channels is None
            or uow.user_notification_preferences is None
        ):
            return

        user = await uow.users.get_by_id(recipient_user_id)
        if user is None or user.id_role != settings.contractor_role_id or user.status != "active":
            return

        if not await uow.messages.is_unread_for_user(message_id=message_id, user_id=recipient_user_id):
            return

        preferences = UserNotificationPreferencesService(
            uow.user_contact_channels,
            uow.user_notification_preferences,
            profiles=uow.profiles,
        )
        if not await preferences.is_channel_enabled(
            user_id=recipient_user_id,
            channel_type="email",
            notification_type="chat",
        ):
            return

        to_email = await _resolve_contractor_email(uow=uow, user_id=recipient_user_id)
        if to_email is None:
            return

        body_text = message_unread_email_body(request_id=request_id)
        payload = build_contractor_event_email_payload(
            to_email=to_email,
            subject=message_unread_email_subject(request_id=request_id),
            body_text=body_text,
            body_html=message_unread_email_body_html(request_id=request_id),
            action_url=_resolve_action_url(offer_id=offer_id),
            action_label="Открыть чат",
        )
        await _build_email_service().send_email(
            to_email=payload.to_email,
            subject=payload.subject,
            text_content=payload.text_content,
            html_content=payload.html_content,
            recipient_user_id=recipient_user_id,
            request_id=request_id,
            offer_id=offer_id,
            suppress_delivery_notification=True,
        )

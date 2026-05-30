from __future__ import annotations

import logging

from app.core.uow import UnitOfWork
from app.services.notifications import NotificationService
from shared.broker import RK_EMAIL_DELIVERY_FAILED, RK_EMAIL_DELIVERY_SUCCEEDED

logger = logging.getLogger(__name__)


def _as_optional_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_optional_str(value) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


class EmailDeliveryEventHandler:
    async def handle(self, *, routing_key: str, payload: dict) -> None:
        correlation_id = str(payload.get("correlation_id") or "").strip()
        if not correlation_id:
            logger.warning("Skip email delivery event without correlation_id")
            return

        recipient_user_id = str(payload.get("recipient_user_id") or "").strip()
        if not recipient_user_id:
            logger.warning("Skip email delivery event without recipient_user_id")
            return

        request_id = _normalize_optional_str(payload.get("request_id"))
        offer_id = _as_optional_int(payload.get("offer_id"))
        to_email = str(payload.get("to_email") or "").strip()
        safe_error_code = str(payload.get("safe_error_code") or "").strip() or None
        safe_error_message = str(payload.get("safe_error_message") or "").strip() or None
        suppress_delivery_notification = bool(payload.get("suppress_delivery_notification"))

        if suppress_delivery_notification:
            logger.info(
                "Skip email delivery center notification due to suppress flag: correlation_id=%s recipient_user_id=%s",
                correlation_id,
                recipient_user_id,
            )
            return

        async with UnitOfWork() as uow:
            notifications_repo = uow.notifications
            if notifications_repo is None:
                logger.warning("Notifications repository is unavailable in UnitOfWork")
                return
            service = NotificationService(notifications_repo)

            if routing_key == RK_EMAIL_DELIVERY_SUCCEEDED:
                notification_type = "email.sent"
            elif routing_key == RK_EMAIL_DELIVERY_FAILED:
                notification_type = "email.failed"
            else:
                logger.warning("Unsupported email delivery routing key: %s", routing_key)
                return
            if await notifications_repo.exists_by_type_user_and_correlation_id(
                user_id=recipient_user_id,
                notification_type=notification_type,
                correlation_id=correlation_id,
            ):
                logger.info(
                    "Skip duplicate email delivery notification: type=%s user_id=%s correlation_id=%s",
                    routing_key,
                    recipient_user_id,
                    correlation_id,
                )
                return

            payload_data = {
                "correlation_id": correlation_id,
                "request_id": request_id,
                "offer_id": offer_id,
                "to_email": to_email,
            }
            if safe_error_code:
                payload_data["safe_error_code"] = safe_error_code

            entity_type = "request" if request_id is not None else "offer" if offer_id is not None else None
            entity_id = request_id if request_id is not None else offer_id
            link_url = f"/requests/{request_id}" if request_id is not None else f"/offers/{offer_id}/workspace" if offer_id is not None else None

            if routing_key == RK_EMAIL_DELIVERY_SUCCEEDED:
                await service.notify_email_sent(
                    recipient_user_id=recipient_user_id,
                    title="Письмо отправлено",
                    body=f"Письмо успешно отправлено на адрес {to_email}.",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    link_url=link_url,
                    payload=payload_data,
                )
                return

            if routing_key == RK_EMAIL_DELIVERY_FAILED:
                await service.notify_email_failed(
                    recipient_user_id=recipient_user_id,
                    error_message=safe_error_message or "Не удалось отправить письмо. Проверьте настройки почты.",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    link_url=link_url,
                    payload=payload_data,
                )
                return

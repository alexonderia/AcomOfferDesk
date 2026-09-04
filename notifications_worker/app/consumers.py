from __future__ import annotations

import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from .email_sender import send_email
from .result_publisher import publish_email_delivery_result
from shared.broker import RK_EMAIL, RK_EMAIL_DELIVERY_FAILED, RK_EMAIL_DELIVERY_SUCCEEDED
from shared.email_delivery import EmailDeliveryResultEvent, generate_correlation_id, utc_now_iso
from shared.normalization import as_optional_int as _as_optional_int
from shared.normalization import normalize_optional_str as _normalize_optional_str

logger = logging.getLogger(__name__)


async def handle_message(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            payload = json.loads(message.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Skip notification payload: invalid JSON")
            return

        if not isinstance(payload, dict):
            logger.warning("Skip notification payload: expected JSON object")
            return

        try:
            if message.routing_key == RK_EMAIL:
                correlation_id = str(payload.get("correlation_id") or "").strip()
                if not correlation_id:
                    correlation_id = generate_correlation_id()
                    logger.warning("Email payload has no correlation_id; generated fallback id")
                result = await send_email(payload)
                event_type = RK_EMAIL_DELIVERY_SUCCEEDED if result.success else RK_EMAIL_DELIVERY_FAILED
                await publish_email_delivery_result(
                    EmailDeliveryResultEvent(
                        event_type=event_type,
                        correlation_id=correlation_id,
                        recipient_user_id=str(payload.get("recipient_user_id") or payload.get("initiator_user_id") or "").strip() or None,
                        request_id=_normalize_optional_str(payload.get("request_id")),
                        offer_id=_as_optional_int(payload.get("offer_id")),
                        to_email=str(payload.get("to_email") or "").strip(),
                        suppress_delivery_notification=bool(payload.get("suppress_delivery_notification")),
                        operation_id=_normalize_optional_str(payload.get("operation_id")),
                        operation_kind=_normalize_optional_str(payload.get("operation_kind")),
                        operation_expected_total=_as_optional_int(payload.get("operation_expected_total")),
                        safe_error_code=result.safe_error_code,
                        safe_error_message=result.safe_error_message,
                        occurred_at=utc_now_iso(),
                    )
                )
                return
            logger.info("Skip notification payload: unsupported routing key %s", message.routing_key)
        except Exception:
            logger.exception("Failed to process notification payload for routing key %s", message.routing_key)

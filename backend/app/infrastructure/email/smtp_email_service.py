from __future__ import annotations

import base64

from app.infrastructure.email.email_attachment import EmailAttachment
from app.infrastructure.notification_publisher import publish_notification
from shared.broker import RK_EMAIL
from shared.email_delivery import generate_correlation_id, utc_now_iso


class SMTPEmailService:
    def __init__(
        self,
        *,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str,
        from_name: str,
    ) -> None:
        self._from_address = from_address
        self._from_name = from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str | None = None,
        attachments: list[EmailAttachment] | None = None,
        reply_token: str | None = None,
        recipient_context: dict | None = None,
        correlation_id: str | None = None,
        recipient_user_id: str | None = None,
        request_id: str | None = None,
        offer_id: int | None = None,
        initiator_user_id: str | None = None,
        suppress_delivery_notification: bool = False,
        operation_id: str | None = None,
        operation_kind: str | None = None,
        operation_expected_total: int | None = None,
    ) -> None:
        resolved_correlation_id = (correlation_id or "").strip() or generate_correlation_id()
        normalized_recipient_user_id = (recipient_user_id or "").strip() or None
        resolved_recipient_context = recipient_context
        if resolved_recipient_context is None and normalized_recipient_user_id:
            resolved_recipient_context = {
                "user_login": normalized_recipient_user_id,
            }
        await publish_notification(
            RK_EMAIL,
            {
                "correlation_id": resolved_correlation_id,
                "queued_at": utc_now_iso(),
                "to_email": to_email,
                "subject": subject,
                "text_content": text_content,
                "html_content": html_content,
                "attachments": [
                    {
                        "filename": item.filename,
                        "mime_type": item.mime_type,
                        "content_base64": base64.b64encode(item.content_bytes).decode("utf-8"),
                    }
                    for item in (attachments or [])
                ],
                "reply_token": reply_token,
                "recipient_context": resolved_recipient_context,
                "recipient_user_id": recipient_user_id,
                "initiator_user_id": initiator_user_id,
                "request_id": request_id,
                "offer_id": offer_id,
                "suppress_delivery_notification": suppress_delivery_notification,
                "operation_id": operation_id,
                "operation_kind": operation_kind,
                "operation_expected_total": operation_expected_total,
                "from_address": self._from_address,
                "from_name": self._from_name,
            },
        )

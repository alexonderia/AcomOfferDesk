from __future__ import annotations

import base64

from app.infrastructure.email.email_attachment import EmailAttachment
from app.infrastructure.notification_publisher import publish_notification
from shared.broker import RK_EMAIL


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
    ) -> None:
        await publish_notification(
            RK_EMAIL,
            {
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
                "recipient_context": recipient_context,
                "from_address": self._from_address,
                "from_name": self._from_name,
            },
        )

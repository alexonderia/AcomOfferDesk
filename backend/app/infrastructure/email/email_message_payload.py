from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.email.email_attachment import EmailAttachment

@dataclass(slots=True, frozen=True)
class EmailMessagePayload:
    to_email: str
    subject: str
    text_content: str
    html_content: str | None = None
    attachments: list[EmailAttachment] | None = None
    reply_token: str | None = None
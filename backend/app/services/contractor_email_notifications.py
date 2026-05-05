from __future__ import annotations

from urllib.parse import quote

from app.core.config import settings
from app.infrastructure.email.email_templates.contractor_status_email import (
    build_contractor_access_closed_email_payload,
    build_contractor_access_opened_email_payload,
    build_contractor_review_email_payload,
)
from app.infrastructure.email.smtp_email_service import SMTPEmailService


def _build_authorization_link() -> str | None:
    base_url = (settings.web_base_url or settings.public_backend_base_url or "").strip().rstrip("/")
    if not base_url:
        return None

    next_path = quote("/", safe="/")
    return f"{base_url}/login?next={next_path}"


def _build_email_service() -> SMTPEmailService:
    return SMTPEmailService(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        username=settings.email_address,
        password=settings.email_app_password,
        from_address=settings.email_address,
        from_name=settings.email_from_name,
    )


async def notify_contractor_review_email(*, to_email: str) -> None:
    payload = build_contractor_review_email_payload(to_email=to_email)
    await _build_email_service().send_email(
        to_email=payload.to_email,
        subject=payload.subject,
        text_content=payload.text_content,
        html_content=payload.html_content,
    )


async def notify_contractor_access_opened_email(*, to_email: str) -> None:
    payload = build_contractor_access_opened_email_payload(
        to_email=to_email,
        authorization_url=_build_authorization_link(),
    )
    await _build_email_service().send_email(
        to_email=payload.to_email,
        subject=payload.subject,
        text_content=payload.text_content,
        html_content=payload.html_content,
    )


async def notify_contractor_access_closed_email(*, to_email: str) -> None:
    payload = build_contractor_access_closed_email_payload(to_email=to_email)
    await _build_email_service().send_email(
        to_email=payload.to_email,
        subject=payload.subject,
        text_content=payload.text_content,
        html_content=payload.html_content,
    )

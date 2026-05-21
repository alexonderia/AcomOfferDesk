from __future__ import annotations

from html import escape
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


async def notify_contractor_status_changed_email(
    *,
    to_email: str,
    user_status: str,
    recipient_user_id: str | None = None,
    initiator_user_id: str | None = None,
) -> bool:
    normalized_status = (user_status or "").strip().lower()
    if normalized_status == "active":
        subject = "AcomOfferDesk — доступ одобрен"
        text = "Ваш доступ к системе AcomOfferDesk одобрен. Вы можете войти в систему."
    elif normalized_status in {"inactive", "review"}:
        subject = "AcomOfferDesk — заявка на доступ отклонена"
        text = "Ваша заявка на доступ к системе AcomOfferDesk отклонена."
    elif normalized_status == "blacklist":
        subject = "AcomOfferDesk — доступ ограничен"
        text = "Ваш доступ к системе AcomOfferDesk ограничен."
    else:
        return False

    await _build_email_service().send_email(
        to_email=to_email,
        subject=subject,
        text_content=text,
        html_content=f"<p>{escape(text)}</p>",
        recipient_user_id=recipient_user_id,
        initiator_user_id=initiator_user_id,
        suppress_delivery_notification=True,
    )
    return True

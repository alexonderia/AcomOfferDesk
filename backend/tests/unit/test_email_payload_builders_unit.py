from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.email.email_templates.contractor_status_email import (
    build_contractor_access_opened_email_payload,
)
from app.infrastructure.email.email_templates.request_notification_email import (
    build_request_notification_email_payload,
    build_request_registration_email_payload,
)
from app.infrastructure.email.email_templates.verification_email import (
    build_verification_email_payload,
)


def _deadline() -> datetime:
    return datetime(2026, 5, 12, 10, 30, tzinfo=timezone.utc)


def test_request_notification_payload_contains_subject_urls_token_and_warning() -> None:
    payload = build_request_notification_email_payload(
        to_email="contractor@example.com",
        request_id=42,
        description="Поставка оборудования",
        deadline_at=_deadline(),
        request_url="https://acom.example/requests/42/contractor",
        reply_token="reply.token",
        attachment_warning="Вложения не добавлены: размер превышает лимит",
    )

    assert payload.subject == "AcomOfferDesk — новая заявка №42"
    assert payload.reply_token == "reply.token"
    assert "Открыть заявку: https://acom.example/requests/42/contractor" in payload.text_content
    assert "Если кнопка не работает, откройте ссылку вручную" in payload.html_content
    assert "reply.token" in payload.text_content
    assert "reply.token" in payload.html_content
    assert "Внимание: Вложения не добавлены: размер превышает лимит" in payload.text_content
    assert "Вложения не добавлены: размер превышает лимит" in payload.html_content
    assert "None" not in payload.text_content
    assert "undefined" not in payload.text_content.lower()


def test_request_notification_payload_escapes_html_content() -> None:
    payload = build_request_notification_email_payload(
        to_email="contractor@example.com",
        request_id=9,
        description='<b>Тест & "цена"</b>',
        deadline_at=_deadline(),
        request_url="https://acom.example/requests/9?q=<tag>&x=1",
        reply_token=None,
        attachment_warning="<danger>",
    )

    assert "<b>Тест & \"цена\"</b>" not in payload.html_content
    assert "&lt;b&gt;Тест &amp; &quot;цена&quot;&lt;/b&gt;" in payload.html_content
    assert "q=&lt;tag&gt;&amp;x=1" in payload.html_content
    assert "<danger>" not in payload.html_content
    assert "&lt;danger&gt;" in payload.html_content


def test_request_registration_payload_contains_registration_link_and_fallback_text() -> None:
    registration_url = "https://acom.example/api/v1/auth/oidc/register?invite_token=abc&next_path=/account"
    payload = build_request_registration_email_payload(
        to_email="invite@example.com",
        request_id=77,
        description=None,
        deadline_at=_deadline(),
        tg_bot_url="https://t.me/acom_bot?start=1",
        registration_url=registration_url,
        registration_ttl_seconds=3600,
        attachment_warning=None,
    )

    assert payload.subject == "AcomOfferDesk — новая заявка №77"
    assert "Описание: Описание не указано" in payload.text_content
    assert f"Ссылка на регистрацию: {registration_url}" in payload.text_content
    assert "Срок действия ссылки: 1 ч." in payload.text_content
    assert "Открыть legacy Telegram-бот" in payload.html_content
    assert "Если кнопка не работает, откройте ссылку вручную" in payload.html_content
    assert "None" not in payload.text_content
    assert "undefined" not in payload.text_content.lower()


def test_contractor_access_opened_payload_includes_manual_link_when_url_exists() -> None:
    payload = build_contractor_access_opened_email_payload(
        to_email="contractor@example.com",
        authorization_url="https://acom.example/login?next=/",
    )

    assert payload.subject == "AcomOfferDesk — доступ в сервис открыт"
    assert "https://acom.example/login?next=/" in payload.text_content
    assert "Если кнопка не работает, откройте ссылку вручную" in payload.html_content


def test_verification_payload_is_utf8_friendly_and_has_no_mojibake_markers() -> None:
    payload = build_verification_email_payload(
        to_email="user@example.com",
        verification_link="https://acom.example/verify-email?token=token-123",
        ttl_seconds=900,
        service_name="AcomOfferDesk",
    )

    assert payload.subject == "AcomOfferDesk — подтверждение электронной почты"
    assert "Подтвердите адрес по ссылке:" in payload.text_content
    assert "https://acom.example/verify-email?token=token-123" in payload.text_content
    assert "Если кнопка не работает, откройте ссылку вручную" in payload.html_content
    assert "\ufffd" not in payload.text_content
    assert "\ufffd" not in payload.html_content
    assert "вЂ" not in payload.subject

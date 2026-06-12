from __future__ import annotations

from app.infrastructure.email.email_templates.contractor_event_email import build_contractor_event_email_payload


def test_build_contractor_event_email_payload_contains_subject_and_body():
    payload = build_contractor_event_email_payload(
        to_email="contractor@example.com",
        subject="AcomOfferDesk — тест",
        body_text="Текст уведомления.",
        body_html="Текст <strong>уведомления</strong>.",
        action_url="https://example.com/login",
        action_label="Открыть заявку",
    )

    assert payload.to_email == "contractor@example.com"
    assert payload.subject == "AcomOfferDesk — тест"
    assert "Текст уведомления." in payload.text_content
    assert "Открыть заявку: https://example.com/login" in payload.text_content
    assert "Текст <strong>уведомления</strong>." in payload.html_content
    assert "Открыть заявку" in payload.html_content

from __future__ import annotations

from datetime import datetime, timezone

from shared.notification_copy import (
    ACCESS_CLOSED_BODY,
    ACCESS_OPENED_BODY,
    AUTHORIZATION_BUTTON_LABEL,
    NOTIFICATION_BUTTON_LABEL,
    REGISTRATION_BUTTON_LABEL,
    REGISTRATION_COMPLETED_BODY,
    message_created_body,
    new_request_outbound_body,
    offer_status_changed_body,
    offer_updated_body,
    request_created_body,
    request_status_changed_body,
)


def test_request_status_changed_body_is_shared_across_channels() -> None:
    body = request_status_changed_body(
        request_id="42",
        previous_status="open",
        new_status="review",
    )
    assert body == "Заявка №42: Открыта → На рассмотрении."


def test_new_request_outbound_body_starts_with_request_created_body() -> None:
    body = new_request_outbound_body(
        request_id="77",
        description="Тест",
        deadline_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
    )
    assert body.startswith(request_created_body(request_id="77"))
    assert "Тест" in body
    assert "Срок: 10.06.2026, 12:00" in body


def test_offer_updated_and_status_use_same_request_wording() -> None:
    assert offer_updated_body(request_id="15") == "По заявке №15 обновлено коммерческое предложение."
    assert offer_status_changed_body(request_id="15") == "По заявке №15 изменён статус КП."


def test_notification_button_labels_are_stable() -> None:
    assert NOTIFICATION_BUTTON_LABEL == "Перейти в систему"
    assert REGISTRATION_BUTTON_LABEL == "Перейти к регистрации"
    assert AUTHORIZATION_BUTTON_LABEL == "Перейти к авторизации"


def test_access_and_registration_messages_are_stable() -> None:
    assert REGISTRATION_COMPLETED_BODY == "Регистрация пройдена. Данные отправлены на проверку."
    assert ACCESS_OPENED_BODY == "Доступ к системе открыт."
    assert ACCESS_CLOSED_BODY == "Доступ к системе ограничен."
    assert message_created_body(request_id="9") == "В чате по заявке №9 появилось новое сообщение."

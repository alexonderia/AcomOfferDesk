from __future__ import annotations

from app.core.config import settings
from app.services.registration_admin_notify import (
    RegistrationNotifyContext,
    build_permission_audit,
    format_registration_message,
)


def test_build_permission_audit_contractor_has_keycloak_role_and_permissions():
    audit = build_permission_audit(settings.contractor_role_id)
    assert audit["keycloak_app_role"] == "app.contractor"
    assert audit["permissions_count"] > 0
    assert audit["matrix_ok"] is True
    from app.domain.permissions import get_permissions_for_role

    assert "offers.create" in get_permissions_for_role(settings.contractor_role_id)


def test_format_registration_message_russian_blocks():
    message = format_registration_message(
        RegistrationNotifyContext(
            source="contractor_tg",
            user_id="demo_user",
            role_id=settings.contractor_role_id,
            role_name="Контрагент",
            status="review",
            full_name="Иванов Иван",
            company_name="ООО Тест",
        )
    )
    assert "Регистрация AcomOfferDesk" in message
    assert "Пользователь: Иванов Иван" in message
    assert "Суть" not in message  # Hermes-style blocks only in relay; here flat format
    assert "Контрагент" in message
    assert "app.contractor" in message
    assert "permissions.py" in message
    assert "demo_user" in message

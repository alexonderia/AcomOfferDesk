import sys
from pathlib import Path

import pytest

# Ensure repo root is importable so `shared/` can be resolved when running tests from `backend/`.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.config import settings
from app.services import contractor_email_notifications as contractor_email_notifications_module
from shared.notification_copy import AUTHORIZATION_BUTTON_LABEL


@pytest.mark.asyncio
async def test_notify_contractor_status_changed_email_active_includes_login_button(monkeypatch):
    monkeypatch.setattr(settings, "web_base_url", "https://acom.example")

    sent = {}

    class _FakeEmailService:
        async def send_email(self, **kwargs) -> None:  # noqa: ANN002
            sent.update(kwargs)

    fake_email_service = _FakeEmailService()
    monkeypatch.setattr(contractor_email_notifications_module, "_build_email_service", lambda: fake_email_service)

    await contractor_email_notifications_module.notify_contractor_status_changed_email(
        to_email="contractor@example.com",
        user_status="active",
        recipient_user_id="recipient-1",
        initiator_user_id="initiator-1",
    )

    assert sent["subject"] == "AcomOfferDesk — доступ открыт"
    assert sent["suppress_delivery_notification"] is True
    assert AUTHORIZATION_BUTTON_LABEL in sent["html_content"]
    assert "https://acom.example/login?next=/" in sent["html_content"]


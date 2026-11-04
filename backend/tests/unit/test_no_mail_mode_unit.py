from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import Settings, settings
from app.infrastructure.email.smtp_email_service import SMTPEmailService
from app.infrastructure.email.sensitive_email_service import SensitiveEmailService
from app.services.send_request_notification_email import SendRequestNotificationEmailUseCase
from app.services.iam_bindings import recover_existing_iam_binding
from app.domain.exceptions import Conflict
from app.services.user_notification_preferences import UserNotificationPreferencesService


def test_no_mail_settings_accept_empty_mail_secrets_but_enabled_mode_rejects_them():
    parameters = dict(_env_file=None, EMAIL_ADDRESS='', EMAIL_APP_PASSWORD='', SMTP_HOST='', EMAIL_VERIFICATION_SECRET='')
    configured = Settings(EMAIL_ENABLED=False, **parameters)
    assert configured.email_enabled is False
    with pytest.raises(ValueError):
        Settings(EMAIL_ENABLED=True, **parameters)


@pytest.mark.asyncio
async def test_no_mail_operations_do_not_touch_broker_smtp_recipients_or_files(monkeypatch):
    monkeypatch.setattr(settings, 'email_enabled', False)
    publisher = AsyncMock(side_effect=AssertionError('broker must not be called'))
    monkeypatch.setattr('app.infrastructure.email.smtp_email_service.publish_notification', publisher)
    smtp = SMTPEmailService(smtp_host='', smtp_port=465, username='', password='', from_address='', from_name='')
    await smtp.send_email('recipient@example.com', 'subject', 'text')
    sensitive = SensitiveEmailService(smtp_host='', smtp_port=465, smtp_security='auto', username='', password='', from_address='', from_name='')
    monkeypatch.setattr(sensitive, '_send_sync', lambda *args: (_ for _ in ()).throw(AssertionError('SMTP must not be called')))
    await sensitive.send_email(to_email='recipient@example.com', subject='subject', text_content='text', html_content='text')
    use_case = SendRequestNotificationEmailUseCase(request_repository=object(), profile_repository=object(), users=object(), email_service=smtp, app_url='', file_service=object(), invitation_service=object())
    result = await use_case.execute(request_id='request', contractor_role_id=3)
    assert result.expected_total == 0 and result.operation_id is None
    publisher.assert_not_awaited()


@pytest.mark.asyncio
async def test_binding_recovery_checks_existing_identity_without_changing_password(monkeypatch):
    accounts = SimpleNamespace(
        get_by_user_provider=AsyncMock(return_value=None),
        get_conflicting_subject=AsyncMock(return_value=None),
        add=AsyncMock(),
    )
    state = SimpleNamespace(id='00000000-0000-4000-8000-000000000001', login='employee')
    client = SimpleNamespace(get_credential_state=AsyncMock(return_value=state))
    monkeypatch.setattr('app.services.iam_bindings.IamClient', lambda: client)
    binding = await recover_existing_iam_binding(SimpleNamespace(user_auth_accounts=accounts), user_id='employee')
    assert binding.external_subject_id == state.id and binding.is_active
    assert vars(client).keys() == {'get_credential_state'}
    state.login = 'different-employee'
    with pytest.raises(Conflict):
        await recover_existing_iam_binding(SimpleNamespace(user_auth_accounts=accounts), user_id='employee')
    assert accounts.add.await_count == 1


@pytest.mark.asyncio
async def test_disabled_mail_preferences_are_unavailable_and_preserved_for_reenable(monkeypatch):
    monkeypatch.setattr(settings, 'email_enabled', False)
    channels = SimpleNamespace(list_by_user=AsyncMock(return_value=[SimpleNamespace(
        id=1, channel_type='email', channel_value='user@example.com', is_active=True,
    )]))
    preferences = SimpleNamespace(list_by_channel_ids=AsyncMock(return_value=[SimpleNamespace(
        id_contact_channel=1, notification_type='chat', is_enabled=True,
    )]), upsert=AsyncMock())
    service = UserNotificationPreferencesService(channels, preferences)
    state = await service.get_state(user_id='user')
    assert state.email_available is False
    assert all(not item.email for item in state.preferences.values())
    with pytest.raises(Conflict, match='отключён'):
        await service.update_mode(user_id='user', mode='email_only')
    preferences.upsert.assert_not_awaited()
    monkeypatch.setattr(settings, 'email_enabled', True)
    state = await service.get_state(user_id='user')
    assert state.email_available is True and state.preferences['chat'].email is True

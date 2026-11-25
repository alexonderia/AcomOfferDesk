from unittest.mock import AsyncMock
from types import SimpleNamespace

import pytest

from app.services.email_verification import EmailVerificationService
from app.domain.exceptions import Unauthorized


@pytest.mark.asyncio
async def test_verification_email_delivery_can_be_correlated_with_its_recipient():
    service = EmailVerificationService(AsyncMock())
    service._email_service = AsyncMock()
    await service._send_verification_email(
        email="recipient@example.com",
        verification_link="https://app.example/verify-email?token=test-token",
        recipient_context={"user_login": "recipient"},
    )

    assert service._email_service.send_email.call_args.kwargs["recipient_user_id"] == "recipient"


@pytest.mark.asyncio
@pytest.mark.parametrize("verified,email", [(True, "recipient@example.com"), (False, "recipient@example.com"), (True, "changed@example.com")])
async def test_reopening_confirmation_only_reads_an_already_verified_matching_email(verified, email):
    profiles, channels, bindings, iam = AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock()
    iam.consume_action_token.side_effect = Unauthorized()
    iam.inspect_consumed_email_confirmation.return_value = SimpleNamespace(
        account_id="account-1", purpose="first_access", context={"email": "recipient@example.com"},
    )
    bindings.get_by_provider_subject.return_value = SimpleNamespace(id_user="recipient")
    channels.get_primary_by_type.return_value = SimpleNamespace(is_verified=verified, channel_value=email)
    service = EmailVerificationService(profiles, channels, user_auth_accounts=bindings, iam_client=iam)
    if verified and email == "recipient@example.com":
        result = await service.confirm_profile_verification(token="consumed-token")
        assert result.updated is False and result.next_action == "login"
    else:
        with pytest.raises(Unauthorized):
            await service.confirm_profile_verification(token="consumed-token")
    profiles.update_mail_after_verification.assert_not_called()
    channels.upsert_channel.assert_not_called()
    iam.create_action_token.assert_not_called()


@pytest.mark.asyncio
async def test_repeat_first_access_confirmation_does_not_issue_password_setup(monkeypatch):
    from app.api.v1 import auth
    from app.services import email_verification

    uow, iam = AsyncMock(), AsyncMock()
    uow.__aenter__.return_value = uow
    uow.users.get_by_id.return_value = SimpleNamespace(status="review")
    uow.user_auth_accounts.get_by_provider_subject.return_value = SimpleNamespace(id_user="recipient")
    uow.user_contact_channels.get_primary_by_type.return_value = SimpleNamespace(is_verified=True, channel_value="recipient@example.com")
    iam.consume_action_token.side_effect = Unauthorized()
    iam.inspect_consumed_email_confirmation.return_value = SimpleNamespace(account_id="account-1", purpose="first_access", context={"email": "recipient@example.com"})
    monkeypatch.setattr(email_verification, "IamClient", lambda: iam)
    result = await auth.verify_email(token="consumed-token-123456", uow=uow)

    assert result.detail == "Email уже подтверждён"
    assert result.next_action == "waiting_for_review"
    assert result.redirect_url is None
    iam.create_action_token.assert_not_called()

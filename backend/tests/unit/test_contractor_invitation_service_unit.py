from __future__ import annotations

import pytest

from app.core.config import settings
from app.domain.exceptions import Conflict, Forbidden
from app.domain.permissions import PermissionCodes
from app.infrastructure.email.email_attachment import EmailAttachment
from app.services.contractor_invitations import ContractorInvitationService


class _FakeEmailService:
    def __init__(self, *, fail_for: set[str] | None = None) -> None:
        self.fail_for = fail_for or set()
        self.calls: list[dict] = []

    async def send_email(self, **kwargs) -> None:
        self.calls.append(kwargs)
        if kwargs.get("to_email") in self.fail_for:
            raise RuntimeError("queue unavailable")


class _FakeAttachmentService:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.requested_normative_ids: list[int] = []

    async def load_required_attachment(self, *, normative_file_id: int) -> EmailAttachment:
        self.requested_normative_ids.append(normative_file_id)
        if self.should_fail:
            raise Conflict("Файл презентации не найден")
        return EmailAttachment(
            filename="instruction.pptx",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            content_bytes=b"fake-pptx",
        )


@pytest.mark.asyncio
async def test_invite_contractors_parses_dedupes_and_reports_invalid(make_current_user, monkeypatch):
    monkeypatch.setattr(settings, "contractor_invite_max_emails_per_request", 50)
    email_service = _FakeEmailService()
    attachment_service = _FakeAttachmentService()
    service = ContractorInvitationService(
        email_service=email_service,
        attachment_service=attachment_service,
    )
    current_user = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.CONTRACTORS_MANUAL_CREATE},
    )

    result = await service.invite_contractors(
        current_user=current_user,
        emails=["valid1@example.com, BAD-EMAIL", "valid2@example.com valid1@example.com", "another-bad"],
        normative_file_id=7,
    )

    assert result.sent == ["valid1@example.com", "valid2@example.com"]
    assert result.invalid == ["bad-email", "another-bad"]
    assert result.failed == []
    assert [item["to_email"] for item in email_service.calls] == ["valid1@example.com", "valid2@example.com"]
    assert attachment_service.requested_normative_ids == [7]
    for call in email_service.calls:
        assert len(call["attachments"]) == 1


@pytest.mark.asyncio
async def test_invite_contractors_keeps_partial_success_on_send_errors(make_current_user):
    email_service = _FakeEmailService(fail_for={"fail@example.com"})
    service = ContractorInvitationService(
        email_service=email_service,
        attachment_service=_FakeAttachmentService(),
    )
    current_user = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.CONTRACTORS_MANUAL_CREATE},
    )

    result = await service.invite_contractors(
        current_user=current_user,
        emails=["ok@example.com fail@example.com"],
        normative_file_id=3,
    )

    assert result.sent == ["ok@example.com"]
    assert [item.email for item in result.failed] == ["fail@example.com"]
    assert result.failed[0].reason
    assert result.invalid == []


@pytest.mark.asyncio
async def test_invite_contractors_denies_without_permissions(make_current_user):
    service = ContractorInvitationService(
        email_service=_FakeEmailService(),
        attachment_service=_FakeAttachmentService(),
    )
    current_user = make_current_user(
        role_id=settings.economist_role_id,
        permissions=set(),
    )

    with pytest.raises(Forbidden):
        await service.invite_contractors(
            current_user=current_user,
            emails=["valid@example.com"],
            normative_file_id=1,
        )


@pytest.mark.asyncio
async def test_invite_contractors_requires_attachment_for_manual_flow(make_current_user):
    service = ContractorInvitationService(
        email_service=_FakeEmailService(),
        attachment_service=_FakeAttachmentService(should_fail=True),
    )
    current_user = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.CONTRACTORS_MANUAL_CREATE},
    )

    with pytest.raises(Conflict):
        await service.invite_contractors(
            current_user=current_user,
            emails=["valid@example.com"],
            normative_file_id=1,
        )


@pytest.mark.asyncio
async def test_invite_contractors_blocks_when_limit_exceeded(make_current_user, monkeypatch):
    monkeypatch.setattr(settings, "contractor_invite_max_emails_per_request", 1)
    service = ContractorInvitationService(
        email_service=_FakeEmailService(),
        attachment_service=_FakeAttachmentService(),
    )
    current_user = make_current_user(
        role_id=settings.economist_role_id,
        permissions={PermissionCodes.CONTRACTORS_MANUAL_CREATE},
    )

    with pytest.raises(Conflict):
        await service.invite_contractors(
            current_user=current_user,
            emails=["first@example.com second@example.com"],
            normative_file_id=1,
        )

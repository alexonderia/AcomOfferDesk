from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest

from app.core.config import settings
from app.domain.exceptions import Conflict
from app.domain.permissions import PermissionCodes, get_role_permissions_map
from app.infrastructure.email.email_attachment import EmailAttachment
from app.repositories.profiles import ActiveContractorEmailRecipient
from app.services.files import PreparedUpload
from app.services.requests import RequestService
from app.services.send_request_notification_email import SendRequestNotificationEmailUseCase
from app.services import send_request_notification_email as send_request_notification_email_module
from app.services.email_delivery_events import BATCH_OPERATION_KIND_REQUEST_ADDITIONAL


def _future_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=10)


class _FakeRequestRepoForCreate:
    def __init__(self) -> None:
        self._next_request_id = 1
        self.created_requests: list[SimpleNamespace] = []
        self.attached: list[tuple[int, int]] = []
        self.hidden: list[tuple[int, list[str]]] = []

    async def create(self, *, request_id=None, id_user, deadline_at, description, initial_amount, id_plan):
        row = SimpleNamespace(
            id=request_id if request_id is not None else self._next_request_id,
            id_user=id_user,
            deadline_at=deadline_at,
            description=description,
            initial_amount=initial_amount,
            id_plan=id_plan,
            status="open",
        )
        self.created_requests.append(row)
        if request_id is None:
            self._next_request_id += 1
        return row

    async def exists_by_id(self, *, request_id: str) -> bool:
        return any(item.id == request_id for item in self.created_requests)

    async def attach_file(self, *, request_id: str, file_id: int) -> None:
        self.attached.append((request_id, file_id))

    async def hide_from_contractors(self, *, request_id: str, contractor_user_ids: list[str]) -> None:
        self.hidden.append((request_id, contractor_user_ids))

    async def get_economy_plan_owner_user_id(self, *, plan_id: int):
        _ = plan_id
        return "plan-owner"

    async def get_by_id(self, *, request_id: str):
        for item in self.created_requests:
            if item.id == request_id:
                return item
        return None

    async def list_active_visible_contractor_user_ids(
        self,
        *,
        request_id: str,
        contractor_role_id: int,
    ) -> list[str]:
        _ = (request_id, contractor_role_id)
        return []


class _FakeFilesRepo:
    async def get_normative_file_status(self, *, normative_id: int):
        _ = normative_id
        return "actual"

    async def get_normative_file(self, *, normative_id: int):
        _ = normative_id
        return SimpleNamespace(id_storage_object=501, original_name="partner-card.pdf")

    async def create(self, *, storage_object_id: int, original_name: str):
        _ = (storage_object_id, original_name)
        return SimpleNamespace(id=900)


class _FakeUsersRepo:
    async def get_by_id(self, user_id: str):
        return SimpleNamespace(id=user_id, id_role=settings.contractor_role_id)

    async def list_active_user_parent_pairs(self):
        return []

    async def list_active_units(self):
        return [
            (1, None),
        ]

    async def list_active_unit_memberships(self):
        return [
            ("owner-33", 1),
            ("owner-44", 1),
            ("owner-45", 1),
            ("owner-50", 1),
            ("contractor-1", 1),
            ("contractor-2", 1),
            ("contractor-3", 1),
            ("vendor_login", 1),
        ]


class _FakeOffersRepo:
    async def get_by_id(self, *, offer_id: int):
        _ = offer_id
        return None


class _FakeUserStatusPeriodsRepo:
    async def get_active_for_user(self, *, user_id: str):
        _ = user_id
        return None


class _FakeFileServiceForCreate:
    async def prepare_bytes(self, *, original_name: str, content_bytes: bytes, mime_type: str):
        return SimpleNamespace(
            original_name=original_name,
            content_bytes=content_bytes,
            mime_type=mime_type,
        )

    async def create_request_file(self, *, request_id: str, upload):
        _ = (request_id, upload)
        return SimpleNamespace(id=901)

    async def cleanup_tracked_objects(self):
        return None


class _FakeEmailNotificationService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def notify_new_request(self, *, request_id: str, additional_emails: list[str] | None, hidden_contractor_ids: list[str] | None):
        self.calls.append(
            {
                "request_id": request_id,
                "additional_emails": additional_emails,
                "hidden_contractor_ids": hidden_contractor_ids,
            }
        )

    async def notify_request_to_additional_emails(
        self,
        *,
        request_id: str,
        additional_emails: list[str],
        initiator_user_id: str | None = None,
    ) -> None:
        self.calls.append(
            {
                "request_id": request_id,
                "additional_emails": additional_emails,
                "initiator_user_id": initiator_user_id,
            }
        )


class _TypeErrorEmailNotificationService:
    async def notify_request_to_additional_emails(
        self,
        *,
        request_id: str,
        additional_emails: list[str],
        initiator_user_id: str | None = None,
    ) -> None:
        _ = (request_id, additional_emails, initiator_user_id)
        raise TypeError("transport bug")


class _FakeRequestRepoForSendUseCase:
    def __init__(self, *, request_row: SimpleNamespace, files: list[SimpleNamespace] | None = None) -> None:
        self._request_row = request_row
        self._files = files or []

    async def get_by_id(self, *, request_id: str):
        return self._request_row if self._request_row.id == request_id else None

    async def list_files_by_request_id(self, *, request_id: str):
        _ = request_id
        return self._files


class _FakeProfileRepoForSendUseCase:
    def __init__(
        self,
        recipients: list[ActiveContractorEmailRecipient],
        *,
        economist_email_to_user_id: dict[str, str] | None = None,
    ) -> None:
        self._recipients = recipients
        self._economist_email_to_user_id = economist_email_to_user_id or {}

    async def list_active_contractor_email_recipients(self, *, contractor_role_id: int):
        _ = contractor_role_id
        return self._recipients

    async def find_contractor_user_id_by_notification_email(
        self,
        *,
        email: str,
        contractor_role_id: int,
    ) -> str | None:
        _ = contractor_role_id
        return self._economist_email_to_user_id.get(email.strip().lower())


class _FakeFileServiceForSendUseCase:
    def __init__(self, payload_by_file_name: dict[str, bytes] | None = None) -> None:
        self._payload_by_file_name = payload_by_file_name or {}

    async def read_bytes(self, *, db_file):
        return self._payload_by_file_name.get(db_file.name, b"")


class _FakeOutboxEmailService:
    def __init__(self) -> None:
        self.outbox: list[dict] = []

    async def send_email(self, **kwargs) -> None:
        self.outbox.append(kwargs)


class _FakeUsersRepoForSendUseCase(_FakeUsersRepo):
    pass



@pytest.mark.asyncio
async def test_create_request_triggers_email_notification_event(make_current_user, monkeypatch):
    requests_repo = _FakeRequestRepoForCreate()
    email_notifications = _FakeEmailNotificationService()
    service = RequestService(
        requests=requests_repo,
        files=_FakeFilesRepo(),
        users=_FakeUsersRepo(),
        offers=_FakeOffersRepo(),
        user_status_periods=_FakeUserStatusPeriodsRepo(),
        email_notifications=email_notifications,
        file_service=_FakeFileServiceForCreate(),
    )
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions=set(get_role_permissions_map()[settings.lead_economist_role_id]),
    )

    request_id, _ = await service.create_request(
        current_user=user,
        deadline_at=_future_dt().replace(tzinfo=None),
        description="Новая заявка",
        initial_amount=0,
        id_plan=None,
        normative_file_id=1,
        files=[
            PreparedUpload(
                original_name="spec.pdf",
                content_bytes=b"file-bytes",
                mime_type="application/pdf",
                content_sha256="sha-1",
            )
        ],
        additional_emails=[" INVITE@example.com ", "invite@example.com", ""],
        hidden_contractor_ids=None,
    )

    assert request_id == 1
    assert email_notifications.calls == [
        {
            "request_id": 1,
            "additional_emails": ["invite@example.com"],
            "hidden_contractor_ids": [],
        }
    ]


@pytest.mark.asyncio
async def test_create_request_rejects_missing_initial_amount(make_current_user):
    service = RequestService(
        requests=_FakeRequestRepoForCreate(),
        files=_FakeFilesRepo(),
        users=_FakeUsersRepo(),
        offers=_FakeOffersRepo(),
        user_status_periods=_FakeUserStatusPeriodsRepo(),
        file_service=_FakeFileServiceForCreate(),
    )
    user = make_current_user(
        role_id=settings.lead_economist_role_id,
        permissions=set(get_role_permissions_map()[settings.lead_economist_role_id]),
    )

    with pytest.raises(Conflict, match="Укажите начальную сумму заявки"):
        await service.create_request(
            current_user=user,
            deadline_at=_future_dt().replace(tzinfo=None),
            description="Новая заявка",
            initial_amount=None,
            id_plan=None,
            normative_file_id=1,
            files=[],
        )


@pytest.mark.asyncio
async def test_manual_request_email_notification_rejects_invalid_email(make_current_user):
    request_row = SimpleNamespace(id=10, id_user="owner-10", status="open")
    requests_repo = _FakeRequestRepoForCreate()
    requests_repo.created_requests.append(request_row)
    service = RequestService(
        requests=requests_repo,
        files=_FakeFilesRepo(),
        users=_FakeUsersRepo(),
        offers=_FakeOffersRepo(),
        user_status_periods=_FakeUserStatusPeriodsRepo(),
        email_notifications=_FakeEmailNotificationService(),
    )
    user = make_current_user(
        user_id="owner-10",
        role_id=settings.economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND,
            PermissionCodes.REQUESTS_UPDATE,
        },
    )

    with pytest.raises(Conflict, match="Invalid additional email"):
        await service.send_request_email_notification(
            current_user=user,
            request_id=10,
            additional_emails=["not-an-email"],
        )


@pytest.mark.asyncio
async def test_manual_request_email_notification_does_not_swallow_internal_type_error(make_current_user):
    request_row = SimpleNamespace(id=10, id_user="owner-10", status="open")
    requests_repo = _FakeRequestRepoForCreate()
    requests_repo.created_requests.append(request_row)
    service = RequestService(
        requests=requests_repo,
        files=_FakeFilesRepo(),
        users=_FakeUsersRepo(),
        offers=_FakeOffersRepo(),
        user_status_periods=_FakeUserStatusPeriodsRepo(),
        email_notifications=_TypeErrorEmailNotificationService(),
    )
    user = make_current_user(
        user_id="owner-10",
        role_id=settings.economist_role_id,
        permissions={
            PermissionCodes.REQUESTS_EMAIL_NOTIFICATIONS_SEND,
            PermissionCodes.REQUESTS_UPDATE,
        },
    )

    with pytest.raises(TypeError, match="transport bug"):
        await service.send_request_email_notification(
            current_user=user,
            request_id=10,
            additional_emails=["user@example.com"],
        )


@pytest.mark.asyncio
async def test_send_use_case_generates_verified_and_invite_email_events(monkeypatch):
    monkeypatch.setattr(settings, "reply_email_token_secret", "reply-secret")
    monkeypatch.setattr(settings, "reply_email_ttl_seconds", 1800)
    monkeypatch.setattr(settings, "public_backend_base_url", "https://api.acom.example")
    monkeypatch.setattr(settings, "invitation_portal_url", "https://portal.acom.example/login")
    monkeypatch.setattr(settings, "web_base_url", "https://web.acom.example")
    monkeypatch.setattr(settings, "email_verification_secret", "invite-test-secret")

    request_row = SimpleNamespace(
        id=33,
        id_user="owner-33",
        description="Поставка металла",
        deadline_at=_future_dt().replace(tzinfo=None),
    )
    use_case = SendRequestNotificationEmailUseCase(
        request_repository=_FakeRequestRepoForSendUseCase(request_row=request_row),
        profile_repository=_FakeProfileRepoForSendUseCase(
            recipients=[
                ActiveContractorEmailRecipient(
                    user_id="contractor-1",
                    email="contractor@example.com",
                    tg_id=123,
                )
            ]
        ),
        users=_FakeUsersRepoForSendUseCase(),
        email_service=_FakeOutboxEmailService(),
        app_url="https://web.acom.example",
    )

    await use_case.execute(
        request_id=33,
        contractor_role_id=settings.contractor_role_id,
        initiator_user_id="economist-1",
        additional_emails=[
            "CONTRACTOR@example.com",
            "invite@example.com",
            " invite@example.com ",
        ],
        hidden_contractor_ids=[],
        include_verified_contractors=True,
    )

    outbox = use_case._email_service.outbox
    assert sorted(item["to_email"] for item in outbox) == [
        "contractor@example.com",
        "invite@example.com",
    ]

    verified_item = next(item for item in outbox if item["to_email"] == "contractor@example.com")
    invite_item = next(item for item in outbox if item["to_email"] == "invite@example.com")

    assert verified_item["reply_token"]
    assert "/requests/33/contractor" in verified_item["text_content"]
    assert "Перейти в систему:" in verified_item["text_content"]
    assert verified_item["operation_kind"] == BATCH_OPERATION_KIND_REQUEST_ADDITIONAL
    assert verified_item["operation_expected_total"] == 2
    assert invite_item["reply_token"] is None
    assert "/register?token=" in invite_item["text_content"]
    assert "https://web.acom.example/register?token=" in invite_item["text_content"]
    assert "https://portal.acom.example/login" not in invite_item["text_content"]
    assert "Ссылка для входа:" in invite_item["text_content"]
    assert invite_item["operation_kind"] == BATCH_OPERATION_KIND_REQUEST_ADDITIONAL
    assert invite_item["operation_expected_total"] == 2
    assert verified_item["operation_id"] == invite_item["operation_id"]



@pytest.mark.asyncio
async def test_send_use_case_skips_when_no_safe_recipients(monkeypatch):
    monkeypatch.setattr(settings, "reply_email_token_secret", "reply-secret")
    request_row = SimpleNamespace(
        id=44,
        id_user="owner-44",
        description="Тест",
        deadline_at=_future_dt().replace(tzinfo=None),
    )
    outbox = _FakeOutboxEmailService()
    use_case = SendRequestNotificationEmailUseCase(
        request_repository=_FakeRequestRepoForSendUseCase(request_row=request_row),
        profile_repository=_FakeProfileRepoForSendUseCase(
            recipients=[
                ActiveContractorEmailRecipient(
                    user_id="contractor-2",
                    email="contractor2@example.com",
                    tg_id=555,
                )
            ]
        ),
        users=_FakeUsersRepoForSendUseCase(),
        email_service=outbox,
        app_url="https://web.acom.example",
    )

    await use_case.execute(
        request_id=44,
        contractor_role_id=settings.contractor_role_id,
        additional_emails=["   "],
        hidden_contractor_ids=["contractor-2"],
        include_verified_contractors=True,
    )

    assert outbox.outbox == []


@pytest.mark.asyncio
async def test_send_use_case_adds_attachment_warning_when_total_size_exceeds_limit(monkeypatch):
    monkeypatch.setattr(send_request_notification_email_module, "MAX_EMAIL_ATTACHMENT_SIZE_MB", 1)
    monkeypatch.setattr(settings, "reply_email_token_secret", "reply-secret")
    request_row = SimpleNamespace(
        id=45,
        id_user="owner-45",
        description="Тест",
        deadline_at=_future_dt().replace(tzinfo=None),
    )
    request_file = SimpleNamespace(name="oversized.pdf", mime_type="application/pdf")
    outbox = _FakeOutboxEmailService()
    use_case = SendRequestNotificationEmailUseCase(
        request_repository=_FakeRequestRepoForSendUseCase(request_row=request_row, files=[request_file]),
        profile_repository=_FakeProfileRepoForSendUseCase(
            recipients=[
                ActiveContractorEmailRecipient(
                    user_id="contractor-3",
                    email="contractor3@example.com",
                    tg_id=777,
                )
            ]
        ),
        users=_FakeUsersRepoForSendUseCase(),
        email_service=outbox,
        app_url="https://web.acom.example",
        file_service=_FakeFileServiceForSendUseCase(payload_by_file_name={"oversized.pdf": b"x" * (2 * 1024 * 1024)}),
    )

    await use_case.execute(
        request_id=45,
        contractor_role_id=settings.contractor_role_id,
        additional_emails=[],
        hidden_contractor_ids=[],
    )

    assert len(outbox.outbox) == 1
    event = outbox.outbox[0]
    assert event["attachments"] == []
    assert "Вложения не добавлены" in event["text_content"]
    assert "Вложения не добавлены" in (event["html_content"] or "")


class _FakePresentationAttachmentService:
    async def load_presentation_attachment(self) -> EmailAttachment:
        return EmailAttachment(
            filename="onboarding.pptx",
            content_bytes=b"presentation-bytes",
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )


@pytest.mark.asyncio
async def test_send_use_case_additional_email_with_economist_account_gets_invitation_content(monkeypatch):
    monkeypatch.setattr(settings, "reply_email_token_secret", "reply-secret")
    monkeypatch.setattr(settings, "email_verification_secret", "verify-secret")
    request_row = SimpleNamespace(
        id=50,
        id_user="owner-50",
        description="Поставка",
        deadline_at=_future_dt().replace(tzinfo=None),
    )
    outbox = _FakeOutboxEmailService()
    use_case = SendRequestNotificationEmailUseCase(
        request_repository=_FakeRequestRepoForSendUseCase(request_row=request_row),
        profile_repository=_FakeProfileRepoForSendUseCase(
            recipients=[],
            economist_email_to_user_id={"vendor@example.com": "vendor_login"},
        ),
        users=_FakeUsersRepoForSendUseCase(),
        email_service=outbox,
        app_url="https://web.acom.example",
        presentation_attachment_service=_FakePresentationAttachmentService(),
    )

    await use_case.execute(
        request_id=50,
        contractor_role_id=settings.contractor_role_id,
        additional_emails=["vendor@example.com"],
        hidden_contractor_ids=[],
        include_verified_contractors=False,
    )

    assert len(outbox.outbox) == 1
    event = outbox.outbox[0]
    assert event["to_email"] == "vendor@example.com"
    assert "Вы приглашены к работе в системе AcomOfferDesk." in event["text_content"]
    assert "Инструкция по получению доступа приложена к письму в виде презентации." in event["text_content"]
    assert "Поступила новая заявка №50." in event["text_content"]
    assert "Перейти в систему:" in event["text_content"]
    assert "invite_token=" not in event["text_content"]
    assert "/register?token=" not in event["text_content"]
    assert event["attachments"][0].filename == "onboarding.pptx"



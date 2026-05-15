from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.config import settings
from app.core.registration_invite_tokens import RegistrationInviteTokenCodec
from app.domain.exceptions import Conflict
from app.domain.permissions import PermissionCodes, get_role_permissions_map
from app.repositories.profiles import ActiveContractorEmailRecipient
from app.services.requests import RequestFileCreateInput, RequestService
from app.services.send_request_notification_email import SendRequestNotificationEmailUseCase
from app.services import send_request_notification_email as send_request_notification_email_module


def _future_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=10)


class _FakeRequestRepoForCreate:
    def __init__(self) -> None:
        self._next_request_id = 1
        self.created_requests: list[SimpleNamespace] = []
        self.attached: list[tuple[int, int]] = []
        self.hidden: list[tuple[int, list[str]]] = []

    async def create(self, *, id_user, deadline_at, description, initial_amount, id_plan):
        row = SimpleNamespace(
            id=self._next_request_id,
            id_user=id_user,
            deadline_at=deadline_at,
            description=description,
            initial_amount=initial_amount,
            id_plan=id_plan,
            status="open",
        )
        self.created_requests.append(row)
        self._next_request_id += 1
        return row

    async def attach_file(self, *, request_id: int, file_id: int) -> None:
        self.attached.append((request_id, file_id))

    async def hide_from_contractors(self, *, request_id: int, contractor_user_ids: list[str]) -> None:
        self.hidden.append((request_id, contractor_user_ids))

    async def get_economy_plan_owner_user_id(self, *, plan_id: int):
        _ = plan_id
        return "plan-owner"

    async def get_by_id(self, *, request_id: int):
        for item in self.created_requests:
            if item.id == request_id:
                return item
        return None


class _FakeFilesRepo:
    async def get_normative_file(self, *, normative_id: int):
        _ = normative_id
        return SimpleNamespace(id_storage_object=501, original_name="partner-card.pdf")

    async def create(self, *, storage_object_id: int, original_name: str):
        _ = (storage_object_id, original_name)
        return SimpleNamespace(id=900)


class _FakeUsersRepo:
    async def get_by_id(self, user_id: str):
        return SimpleNamespace(id=user_id, id_role=settings.contractor_role_id)

    async def list_active_approved_contractor_tg_ids(self, *, contractor_role_id: int, exclude_user_ids: list[str]):
        _ = (contractor_role_id, exclude_user_ids)
        return []

    async def list_active_user_parent_pairs(self):
        return []


class _FakeOffersRepo:
    async def list_contractor_tg_ids_for_request(self, *, request_id: int, contractor_role_id: int):
        _ = (request_id, contractor_role_id)
        return []

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

    async def create_request_file(self, *, request_id: int, upload):
        _ = (request_id, upload)
        return SimpleNamespace(id=901)

    async def cleanup_tracked_objects(self):
        return None


class _FakeEmailNotificationService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def notify_new_request(self, *, request_id: int, additional_emails: list[str] | None, hidden_contractor_ids: list[str] | None):
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
        request_id: int,
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


class _FakeRequestRepoForSendUseCase:
    def __init__(self, *, request_row: SimpleNamespace, files: list[SimpleNamespace] | None = None) -> None:
        self._request_row = request_row
        self._files = files or []

    async def get_by_id(self, *, request_id: int):
        return self._request_row if self._request_row.id == request_id else None

    async def list_files_by_request_id(self, *, request_id: int):
        _ = request_id
        return self._files


class _FakeProfileRepoForSendUseCase:
    def __init__(self, recipients: list[ActiveContractorEmailRecipient]) -> None:
        self._recipients = recipients

    async def list_active_contractor_email_recipients(self, *, contractor_role_id: int):
        _ = contractor_role_id
        return self._recipients


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


@pytest.mark.asyncio
async def test_create_request_triggers_email_notification_event(make_current_user, monkeypatch):
    monkeypatch.setattr(settings, "telegram_legacy_enabled", False)
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
        initial_amount=None,
        id_plan=None,
        files=[
            RequestFileCreateInput(
                original_name="spec.pdf",
                content_bytes=b"file-bytes",
                mime_type="application/pdf",
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
async def test_send_use_case_generates_verified_and_invite_email_events(monkeypatch):
    monkeypatch.setattr(settings, "reply_email_token_secret", "reply-secret")
    monkeypatch.setattr(settings, "email_verification_secret", "verify-secret")
    monkeypatch.setattr(settings, "tg_register_ttl_seconds", 3600)
    monkeypatch.setattr(settings, "reply_email_ttl_seconds", 1800)
    monkeypatch.setattr(settings, "public_backend_base_url", "https://api.acom.example")

    request_row = SimpleNamespace(
        id=33,
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
        email_service=_FakeOutboxEmailService(),
        app_url="https://web.acom.example",
    )

    await use_case.execute(
        request_id=33,
        contractor_role_id=settings.contractor_role_id,
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
    assert "Открыть заявку:" in verified_item["text_content"]
    assert invite_item["reply_token"] is None
    assert "/api/v1/auth/oidc/register?invite_token=" in invite_item["text_content"]
    assert "Ссылка на регистрацию:" in invite_item["text_content"]

    registration_url = next(
        line.removeprefix("Ссылка на регистрацию: ").strip()
        for line in invite_item["text_content"].splitlines()
        if line.startswith("Ссылка на регистрацию: ")
    )
    parsed = urlparse(registration_url)
    qs = parse_qs(parsed.query)
    invite_token = qs["invite_token"][0]
    claims = RegistrationInviteTokenCodec(secret="verify-secret", ttl_seconds=3600).parse_token(invite_token)
    assert claims.email == "invite@example.com"


@pytest.mark.asyncio
async def test_send_use_case_skips_when_no_safe_recipients(monkeypatch):
    monkeypatch.setattr(settings, "reply_email_token_secret", "reply-secret")
    request_row = SimpleNamespace(
        id=44,
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

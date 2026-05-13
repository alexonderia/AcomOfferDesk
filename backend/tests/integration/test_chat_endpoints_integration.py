"""Integration-style tests for chat/workspace API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from app.api.dependencies import get_current_user
from app.api.v1 import offers as offers_api
from app.core.config import settings
from app.domain.exceptions import Forbidden, Unauthorized
from app.domain.permissions import PermissionCodes
from app.schemas.actions import ChatActionsSchema


def _dt() -> datetime:
    return datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc)


class _FakeRuntime:
    async def publish_chat_event(self, *, chat_id: int, event) -> None:
        _ = (chat_id, event)


class _FakeOfferService:
    async def list_messages(self, *, current_user, offer_id: int):
        _ = offer_id
        if PermissionCodes.CHAT_READ not in current_user.permissions:
            raise Forbidden("Insufficient permissions to view chat")
        if current_user.role_id == settings.contractor_role_id and current_user.user_id != "contractor-1":
            raise Forbidden("Insufficient permissions to view chat")
        return [
            SimpleNamespace(
                id=1,
                user_id="contractor-1",
                user_full_name="Contractor",
                text="hello",
                type="text",
                status="send",
                created_at=_dt(),
                updated_at=_dt(),
                read_by=[],
                attachments=[],
            )
        ]

    async def create_message(
        self,
        *,
        current_user,
        offer_id: int,
        text: str,
        attachments=None,
    ):
        _ = (offer_id, text, attachments)
        if PermissionCodes.CHAT_MESSAGE_SEND not in current_user.permissions:
            raise Forbidden("Insufficient permissions to send chat message")
        if attachments and PermissionCodes.CHAT_MESSAGE_ATTACH not in current_user.permissions:
            raise Forbidden("Insufficient permissions to attach files to chat messages")
        if current_user.role_id == settings.contractor_role_id and current_user.user_id != "contractor-1":
            raise Forbidden("Insufficient permissions to send chat message")
        return SimpleNamespace(offer_id=10, chat_id=10, request_id=99, message_id=777)

    async def mark_messages_received(
        self,
        *,
        current_user,
        offer_id: int,
        message_ids,
        up_to_message_id,
    ):
        _ = (offer_id, message_ids, up_to_message_id)
        if PermissionCodes.CHAT_RECEIPTS_MARK_RECEIVED not in current_user.permissions:
            raise Forbidden("Insufficient permissions to acknowledge delivered chat messages")
        return SimpleNamespace(chat_id=10, updated_message_ids=[1, 2], updated_count=2)

    async def mark_messages_read(
        self,
        *,
        current_user,
        offer_id: int,
        message_ids,
        up_to_message_id,
    ):
        _ = (offer_id, message_ids, up_to_message_id)
        if PermissionCodes.CHAT_RECEIPTS_MARK_READ not in current_user.permissions:
            raise Forbidden("Insufficient permissions to mark chat messages as read")
        return SimpleNamespace(chat_id=10, updated_message_ids=[1], last_read_message_id=1, updated_count=1)


class _FakeResolver:
    async def resolve_workspace_context(self, *, current_user, offer_id: int):
        _ = (current_user, offer_id)
        return SimpleNamespace(
            chat_actions=ChatActionsSchema(
                can_view_messages=True,
                can_send_message=True,
                can_attach_files=True,
                can_mark_messages_received=True,
                can_mark_messages_read=True,
            )
        )


class _FakeRealtimeService:
    async def create_message(self, *, current_user, offer_id: int, text: str):
        _ = (current_user, offer_id, text)
        if PermissionCodes.CHAT_MESSAGE_SEND not in current_user.permissions:
            raise Forbidden("Insufficient permissions to send chat message")
        if current_user.role_id == settings.contractor_role_id and current_user.user_id != "contractor-1":
            raise Forbidden("Insufficient permissions to send chat message")
        return (
            SimpleNamespace(offer_id=offer_id, chat_id=offer_id, request_id=55, message_id=901),
            {"chat_id": offer_id, "message": {"id": 901}},
        )

    async def load_message_payload(self, *, offer_id: int, message_id: int):
        _ = (offer_id, message_id)
        return {"chat_id": offer_id, "message": {"id": message_id}}


def _patch_chat_stack(monkeypatch) -> None:
    monkeypatch.setattr(offers_api, "build_offer_service", lambda uow, file_service=None: _FakeOfferService())
    monkeypatch.setattr(offers_api, "_offer_action_resolver", lambda uow: _FakeResolver())
    monkeypatch.setattr(offers_api, "ChatRealtimeService", lambda: _FakeRealtimeService())
    monkeypatch.setattr(offers_api, "get_chat_runtime", lambda: _FakeRuntime())


def test_allowed_user_can_read_workspace_messages(test_client, monkeypatch, set_current_user, make_current_user):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.CHAT_READ},
    )
    set_current_user(user)

    response = test_client.get("/api/v1/offers/10/messages")

    assert response.status_code == 200
    assert response.json()["data"]["items"]
    assert response.json()["data"]["actions"]["can_view_messages"] is True


def test_allowed_user_can_send_text_message(test_client, monkeypatch, set_current_user, make_current_user):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.CHAT_MESSAGE_SEND},
    )
    set_current_user(user)

    response = test_client.post("/api/v1/offers/10/messages", json={"text": "message"})

    assert response.status_code == 200
    assert response.json()["data"]["message_id"] == 901


def test_allowed_user_can_send_message_with_attachment(test_client, monkeypatch, set_current_user, make_current_user):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.CHAT_MESSAGE_SEND, PermissionCodes.CHAT_MESSAGE_ATTACH},
    )
    set_current_user(user)

    response = test_client.post(
        "/api/v1/offers/10/messages/attachments",
        data={"text": "message with file"},
        files=[("files", ("evidence.txt", b"payload", "text/plain"))],
    )

    assert response.status_code == 200
    assert response.json()["data"]["message_id"] == 777


def test_mark_delivered_and_read_updates_receipts_for_allowed_user(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.CHAT_RECEIPTS_MARK_RECEIVED, PermissionCodes.CHAT_RECEIPTS_MARK_READ},
    )
    set_current_user(user)

    delivered = test_client.patch(
        "/api/v1/offers/10/messages/received",
        json={"message_ids": [1, 2]},
    )
    read = test_client.patch(
        "/api/v1/offers/10/messages/read",
        json={"up_to_message_id": 1},
    )

    assert delivered.status_code == 200
    assert delivered.json()["data"]["updated_count"] == 2
    assert read.status_code == 200
    assert read.json()["data"]["updated_count"] == 1


def test_anonymous_user_gets_401_for_chat_endpoint(test_client, api_app):
    async def _anonymous():
        raise Unauthorized("Missing credentials")

    api_app.dependency_overrides[get_current_user] = _anonymous

    response = test_client.get("/api/v1/offers/10/messages")

    assert response.status_code == 401


def test_user_without_chat_read_permission_gets_403(test_client, monkeypatch, set_current_user, make_current_user):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions=set(),
    )
    set_current_user(user)

    response = test_client.get("/api/v1/offers/10/messages")

    assert response.status_code == 403


def test_user_without_chat_send_permission_gets_403(test_client, monkeypatch, set_current_user, make_current_user):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions=set(),
    )
    set_current_user(user)

    response = test_client.post("/api/v1/offers/10/messages", json={"text": "blocked"})

    assert response.status_code == 403


def test_user_without_chat_attach_permission_gets_403(test_client, monkeypatch, set_current_user, make_current_user):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-1",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.CHAT_MESSAGE_SEND},
    )
    set_current_user(user)

    response = test_client.post(
        "/api/v1/offers/10/messages/attachments",
        data={"text": "blocked"},
        files=[("files", ("evidence.txt", b"payload", "text/plain"))],
    )

    assert response.status_code == 403


def test_non_participant_contractor_cannot_access_foreign_workspace_chat(
    test_client,
    monkeypatch,
    set_current_user,
    make_current_user,
):
    _patch_chat_stack(monkeypatch)
    user = make_current_user(
        user_id="contractor-2",
        role_id=settings.contractor_role_id,
        permissions={PermissionCodes.CHAT_READ, PermissionCodes.CHAT_MESSAGE_SEND},
    )
    set_current_user(user)

    response = test_client.get("/api/v1/offers/10/messages")

    assert response.status_code == 403

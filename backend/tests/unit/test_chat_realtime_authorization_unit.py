from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.exceptions import AuthenticationUnavailable, Forbidden
from app.realtime.contracts import OutboundEnvelope
from app.realtime.runtime import ChatRealtimeRuntime
from app.services import chat_realtime


class Socket:
    def __init__(self):
        self.events = []

    async def accept(self):
        pass

    async def send_json(self, payload):
        self.events.append(payload)


@pytest.mark.asyncio
async def test_existing_room_subscriptions_are_filtered_before_every_broadcast():
    runtime = ChatRealtimeRuntime()
    allowed, revoked = Socket(), Socket()
    for user_id, socket in [("allowed", allowed), ("revoked", revoked)]:
        connection = await runtime.manager.connect(websocket=socket, user_id=user_id)
        await runtime.manager.subscribe(connection_id=connection, chat_id=1)
    authorizer = AsyncMock(side_effect=[{"allowed"}, set()])
    runtime.service = SimpleNamespace(authorized_recipients=authorizer)

    assert await runtime._broadcast_to_chat(chat_id=1, event=OutboundEnvelope(type="chat.message.created", data={})) == {"allowed"}
    assert len(allowed.events) == 1
    assert revoked.events == []
    assert await runtime._broadcast_to_chat(chat_id=1, event=OutboundEnvelope(type="chat.message.created", data={})) == set()
    assert len(allowed.events) == 1
    assert authorizer.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["active", "inactive", "missing_user", "missing_binding", "revoked_scope", "iam_unavailable"])
async def test_chat_delivery_requires_current_identity_permissions_and_scope(monkeypatch, state):
    user = None if state == "missing_user" else SimpleNamespace(status="inactive" if state == "inactive" else "active", id_role=6)
    binding = None if state == "missing_binding" else SimpleNamespace(external_subject_id="account")
    uow = SimpleNamespace(
        users=SimpleNamespace(get_by_id=AsyncMock(return_value=user)),
        user_auth_accounts=SimpleNamespace(get_by_user_provider=AsyncMock(return_value=binding)),
    )

    @asynccontextmanager
    async def unit_of_work():
        yield uow

    permissions = AsyncMock(return_value=SimpleNamespace(effective_permissions=frozenset({"chat.read"})))
    if state == "iam_unavailable":
        permissions.side_effect = AuthenticationUnavailable()
    monkeypatch.setattr(chat_realtime, "IamClient", lambda: SimpleNamespace(get_account_permissions=permissions))
    chat_state = AsyncMock(side_effect=Forbidden() if state == "revoked_scope" else None)
    monkeypatch.setattr(chat_realtime, "build_offer_service", lambda _: SimpleNamespace(get_chat_state=chat_state))
    service = chat_realtime.ChatRealtimeService(uow_factory=unit_of_work)

    assert await service.authorized_recipients(offer_id=1, user_ids={"user"}) == ({"user"} if state == "active" else set())
    if state == "active":
        assert chat_state.call_args.kwargs["current_user"].permissions == frozenset({"chat.read"})
    if state in {"inactive", "missing_user", "missing_binding"}:
        permissions.assert_not_awaited()

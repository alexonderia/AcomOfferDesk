from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.exceptions import AuthenticationUnavailable, Forbidden, Unauthorized
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
@pytest.mark.parametrize("state", [
    "active", "inactive", "missing_user", "missing_binding", "revoked_scope", "iam_unavailable",
    "iam_blocked", "role_inactive", "unknown_role", "first_login", "unknown_permission",
])
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
    if state == "unknown_permission":
        permissions.return_value.effective_permissions = frozenset({"unknown.permission"})
    credentials = AsyncMock(return_value=SimpleNamespace(
        role="unknown" if state == "unknown_role" else "economist",
        auth_status="blocked" if state == "iam_blocked" else "active",
        role_active=state != "role_inactive",
        required_actions=("complete_profile",) if state == "first_login" else (),
    ))
    monkeypatch.setattr(chat_realtime, "IamClient", lambda: SimpleNamespace(
        get_account_permissions=permissions, get_credential_state=credentials,
    ))
    chat_state = AsyncMock(side_effect=Forbidden() if state == "revoked_scope" else None)
    monkeypatch.setattr(chat_realtime, "build_offer_service", lambda _: SimpleNamespace(get_chat_state=chat_state))
    service = chat_realtime.ChatRealtimeService(uow_factory=unit_of_work)

    assert await service.authorized_recipients(offer_id=1, user_ids={"user"}) == ({"user"} if state == "active" else set())
    if state == "active":
        assert chat_state.call_args.kwargs["current_user"].permissions == frozenset({"chat.read"})
        assert chat_state.call_args.kwargs["current_user"].system_role == "economist"
    if state in {"inactive", "missing_user", "missing_binding"}:
        permissions.assert_not_awaited()


@pytest.mark.asyncio
async def test_chat_refresh_uses_iam_role_and_keeps_session_without_local_role_fallback(monkeypatch, make_current_user):
    actor = make_current_user()
    uow = SimpleNamespace(
        users=SimpleNamespace(get_by_id=AsyncMock(return_value=SimpleNamespace(status="active", id_role=1))),
        user_auth_accounts=SimpleNamespace(get_by_user_provider=AsyncMock(
            return_value=SimpleNamespace(external_subject_id=actor.iam_account_id),
        )),
    )

    @asynccontextmanager
    async def unit_of_work():
        yield uow

    iam = SimpleNamespace(
        get_credential_state=AsyncMock(return_value=SimpleNamespace(
            role="contractor", auth_status="active", role_active=True, required_actions=(),
        )),
        get_account_permissions=AsyncMock(return_value=SimpleNamespace(effective_permissions=frozenset())),
    )
    monkeypatch.setattr(chat_realtime, "IamClient", lambda: iam)
    service = chat_realtime.ChatRealtimeService(uow_factory=unit_of_work)
    refreshed = await service.refresh_current_user(current_user=actor)
    assert refreshed.role_id == 3
    assert refreshed.system_role == "contractor"
    assert refreshed.iam_session_id == actor.iam_session_id
    uow.user_auth_accounts.get_by_user_provider.return_value.external_subject_id = "another-account"
    with pytest.raises(Unauthorized):
        await service.refresh_current_user(current_user=actor)

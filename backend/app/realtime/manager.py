from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import WebSocket

from app.realtime.contracts import OutboundEnvelope


@dataclass(slots=True)
class ConnectionState:
    connection_id: str
    websocket: WebSocket
    user_id: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subscriptions: set[int] = field(default_factory=set)
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, ConnectionState] = {}
        self._connection_ids_by_user: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, *, websocket: WebSocket, user_id: str) -> str:
        await websocket.accept()
        connection_id = uuid4().hex
        async with self._lock:
            self._connections[connection_id] = ConnectionState(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
            )
            self._connection_ids_by_user.setdefault(user_id, set()).add(connection_id)
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        async with self._lock:
            state = self._connections.pop(connection_id, None)
            if state is None:
                return
            connection_ids = self._connection_ids_by_user.get(state.user_id)
            if connection_ids is None:
                return
            connection_ids.discard(connection_id)
            if not connection_ids:
                self._connection_ids_by_user.pop(state.user_id, None)

    async def subscribe(self, *, connection_id: str, chat_id: int) -> None:
        state = await self._get_state(connection_id)
        state.subscriptions.add(chat_id)

    async def unsubscribe(self, *, connection_id: str, chat_id: int) -> None:
        state = await self._get_state(connection_id)
        state.subscriptions.discard(chat_id)

    async def send_to_connection(self, *, connection_id: str, event: OutboundEnvelope) -> bool:
        state = await self._get_state(connection_id)
        return await self._send(state=state, payload=event.model_dump(mode="json"))

    async def send_to_user(self, *, user_id: str, event: OutboundEnvelope) -> bool:
        async with self._lock:
            connection_ids = list(self._connection_ids_by_user.get(user_id, set()))
            targets = [
                self._connections[connection_id]
                for connection_id in connection_ids
                if connection_id in self._connections
            ]

        if not targets:
            return False

        payload = event.model_dump(mode="json")
        delivered = False
        for state in targets:
            if await self._send(state=state, payload=payload):
                delivered = True
        return delivered

    async def broadcast_to_users(self, *, user_ids: set[str], event: OutboundEnvelope) -> set[str]:
        if not user_ids:
            return set()

        async with self._lock:
            targets: list[ConnectionState] = []
            for user_id in user_ids:
                for connection_id in self._connection_ids_by_user.get(user_id, set()):
                    state = self._connections.get(connection_id)
                    if state is not None:
                        targets.append(state)

        payload = event.model_dump(mode="json")
        delivered_user_ids: set[str] = set()
        for state in targets:
            if await self._send(state=state, payload=payload):
                delivered_user_ids.add(state.user_id)
        return delivered_user_ids

    async def broadcast_to_chat(
        self,
        *,
        chat_id: int,
        event: OutboundEnvelope,
        exclude_user_ids: set[str] | None = None,
    ) -> set[str]:
        async with self._lock:
            targets = [
                state
                for state in self._connections.values()
                if chat_id in state.subscriptions and state.user_id not in (exclude_user_ids or set())
            ]

        delivered_user_ids: set[str] = set()
        payload = event.model_dump(mode="json")
        for state in targets:
            if await self._send(state=state, payload=payload):
                delivered_user_ids.add(state.user_id)
        return delivered_user_ids

    async def is_user_subscribed(self, *, user_id: str, chat_id: int) -> bool:
        async with self._lock:
            return any(state.user_id == user_id and chat_id in state.subscriptions for state in self._connections.values())

    async def _get_state(self, connection_id: str) -> ConnectionState:
        async with self._lock:
            state = self._connections.get(connection_id)
        if state is None:
            raise KeyError(connection_id)
        return state

    async def _send(self, *, state: ConnectionState, payload: dict[str, Any]) -> bool:
        try:
            async with state.send_lock:
                await state.websocket.send_json(payload)
            return True
        except Exception:
            await self.disconnect(state.connection_id)
            return False

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from app.core.datetime_utils import utc_now_naive

from sqlalchemy import Select, and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm_models import Chat, ChatParticipant, Message


@dataclass(frozen=True, slots=True)
class ChatState:
    chat_id: int
    last_message_id: int | None
    last_message_at: object
    participant_user_id: str
    last_read_message_id: int | None
    last_read_at: object
    is_muted: bool
    is_archived: bool


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def reconcile_participants(self, *, chat_id: int, user_ids: set[str], primary_user_ids: set[str]) -> None:
        # Serialize membership reconciliation with other access to this chat.
        await self._session.execute(select(Chat.id).where(Chat.id == chat_id).with_for_update())
        rows = list((await self._session.execute(select(ChatParticipant).where(ChatParticipant.id_chat == chat_id))).scalars().all())
        by_user = {row.id_user: row for row in rows}
        now = utc_now_naive()
        for user_id in user_ids:
            row = by_user.get(user_id)
            if row is None:
                self._session.add(ChatParticipant(id_chat=chat_id, id_user=user_id, joined_at=now, last_read_at=now, is_muted=user_id not in primary_user_ids, is_archived=False))
            elif row.left_at is not None:
                row.left_at = None
        for row in rows:
            if row.id_user not in user_ids and row.left_at is None:
                row.left_at = now
        await self._session.flush()

    async def get_active_participant(self, *, chat_id: int, user_id: str) -> ChatParticipant | None:
        stmt = select(ChatParticipant).where(
            ChatParticipant.id_chat == chat_id,
            ChatParticipant.id_user == user_id,
            ChatParticipant.left_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_participant_user_ids(self, *, chat_id: int) -> list[str]:
        stmt: Select[tuple[str]] = (
            select(ChatParticipant.id_user)
            .where(
                ChatParticipant.id_chat == chat_id,
                ChatParticipant.left_at.is_(None),
            )
            .order_by(ChatParticipant.id_user.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_chat_state_for_user(self, *, chat_id: int, user_id: str) -> ChatState | None:
        stmt = (
            select(
                Chat.id.label("chat_id"),
                Chat.last_message_id.label("last_message_id"),
                Chat.last_message_at.label("last_message_at"),
                ChatParticipant.id_user.label("participant_user_id"),
                ChatParticipant.last_read_message_id.label("last_read_message_id"),
                ChatParticipant.last_read_at.label("last_read_at"),
                ChatParticipant.is_muted.label("is_muted"),
                ChatParticipant.is_archived.label("is_archived"),
            )
            .join(
                ChatParticipant,
                and_(
                    ChatParticipant.id_chat == Chat.id,
                    ChatParticipant.id_user == user_id,
                    ChatParticipant.left_at.is_(None),
                ),
            )
            .where(Chat.id == chat_id)
        )
        result = await self._session.execute(stmt)
        row = result.mappings().one_or_none()
        if row is None:
            return None

        return ChatState(
            chat_id=int(row["chat_id"]),
            last_message_id=row["last_message_id"],
            last_message_at=row["last_message_at"],
            participant_user_id=str(row["participant_user_id"]),
            last_read_message_id=row["last_read_message_id"],
            last_read_at=row["last_read_at"],
            is_muted=bool(row["is_muted"]),
            is_archived=bool(row["is_archived"]),
        )

    async def advance_last_read(
        self,
        *,
        chat_id: int,
        user_id: str,
        message_id: int,
    ) -> bool:
        stmt = (
            update(ChatParticipant)
            .where(
                ChatParticipant.id_chat == chat_id,
                ChatParticipant.id_user == user_id,
                ChatParticipant.left_at.is_(None),
                func.coalesce(ChatParticipant.last_read_message_id, 0) < message_id,
            )
            .values(
                last_read_message_id=message_id,
                last_read_at=func.now(),
            )
        )
        result = await self._session.execute(stmt)
        return bool(result.rowcount)

    async def get_message_read_boundary(
        self,
        *,
        chat_id: int,
        user_id: str,
        up_to_message_id: int | None = None,
        message_ids: Sequence[int] | None = None,
    ) -> int | None:
        stmt = (
            select(func.max(Message.id))
            .where(
                Message.id_chat == chat_id,
                Message.id_user != user_id,
            )
        )

        if up_to_message_id is not None:
            stmt = stmt.where(Message.id <= up_to_message_id)
        if message_ids is not None:
            if not message_ids and up_to_message_id is None:
                return None
            if message_ids:
                stmt = stmt.where(Message.id.in_(message_ids))

        result = await self._session.execute(stmt)
        boundary = result.scalar_one_or_none()
        return int(boundary) if boundary is not None else None

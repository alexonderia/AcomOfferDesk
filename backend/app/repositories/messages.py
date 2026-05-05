from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re

from sqlalchemy import Select, func, literal, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.orm_models import ChatParticipant, File, Message, MessageFile, MessageReceipt


EMAIL_MESSAGE_ID_MARKER = "[email_message_id:"
AUTO_EMAIL_MESSAGE_PREFIX = (
    "Сообщение "
    "сформировано "
    "автоматически "
    "из письма"
)
AUTO_EMAIL_OFFER_CREATED_TEXT = (
    "Оффер "
    "сформирован "
    "автоматически "
    "из письма"
)

def strip_email_message_marker(text: str) -> str:
    normalized = text.strip()
    pattern = rf"^{re.escape(EMAIL_MESSAGE_ID_MARKER)}[^\]]+\]\s*"
    cleaned = re.sub(pattern, "", normalized, count=1)
    return cleaned.strip()


def build_auto_email_content(*, text: str) -> str:
    clean_text = text.strip()
    if clean_text:
        return f"{AUTO_EMAIL_MESSAGE_PREFIX}\n\n{clean_text}"
    return ""


def build_email_message_text(*, text: str, message_id: str) -> str:
    marker = f"{EMAIL_MESSAGE_ID_MARKER}{message_id}]"
    clean_text = text.strip()
    if clean_text:
        return f"{marker}\n\n{clean_text}"
    return marker


@dataclass(frozen=True, slots=True)
class MessageReceiptRow:
    message_id: int
    user_id: str
    delivered_at: object | None
    read_at: object | None


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        chat_id: int,
        user_id: str,
        text: str,
        message_type: str = "text",
        reply_to_id: int | None = None,
    ) -> Message:
        message = Message(
            id_chat=chat_id,
            id_user=user_id,
            text=text,
            type=message_type,
            reply_to_id=reply_to_id,
        )
        self._session.add(message)
        await self._session.flush()
        await self._create_receipts_for_new_message(message_id=message.id, chat_id=chat_id, sender_user_id=user_id)
        return message

    async def get_by_id(self, *, message_id: int) -> Message | None:
        stmt = select(Message).where(Message.id == message_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_chat(self, *, chat_id: int) -> list[Message]:
        stmt: Select[tuple[Message]] = (
            select(Message)
            .where(Message.id_chat == chat_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_files_by_message_ids(self, *, message_ids: Sequence[int]) -> list[tuple[int, File]]:
        if not message_ids:
            return []

        stmt: Select[tuple[int, File]] = (
            select(MessageFile.id_message, File)
            .options(joinedload(File.storage_object))
            .join(File, File.id == MessageFile.id)
            .where(MessageFile.id_message.in_(message_ids))
            .order_by(MessageFile.id_message.asc(), File.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def attach_file(self, *, message_id: int, file_id: int) -> None:
        self._session.add(MessageFile(id=file_id, id_message=message_id))

    async def list_receipts_by_message_ids(
        self,
        *,
        message_ids: Sequence[int],
        recipient_user_ids: Sequence[str] | None = None,
    ) -> list[MessageReceiptRow]:
        if not message_ids:
            return []

        stmt = (
            select(
                MessageReceipt.id_message,
                MessageReceipt.id_user,
                MessageReceipt.delivered_at,
                MessageReceipt.read_at,
            )
            .where(MessageReceipt.id_message.in_(message_ids))
            .order_by(MessageReceipt.id_message.asc(), MessageReceipt.id_user.asc())
        )
        if recipient_user_ids is not None:
            if not recipient_user_ids:
                return []
            stmt = stmt.where(MessageReceipt.id_user.in_(recipient_user_ids))

        result = await self._session.execute(stmt)
        return [
            MessageReceiptRow(
                message_id=int(row.id_message),
                user_id=str(row.id_user),
                delivered_at=row.delivered_at,
                read_at=row.read_at,
            )
            for row in result.all()
        ]

    async def mark_delivered(
        self,
        *,
        chat_id: int,
        recipient_user_id: str,
        message_ids: Sequence[int] | None = None,
        up_to_message_id: int | None = None,
    ) -> list[int]:
        if message_ids is not None and not message_ids and up_to_message_id is None:
            return []

        message_ids_stmt = self._build_recipient_message_ids_stmt(
            chat_id=chat_id,
            recipient_user_id=recipient_user_id,
            message_ids=message_ids,
            up_to_message_id=up_to_message_id,
        )
        await self._ensure_receipts_for_recipient(
            recipient_user_id=recipient_user_id,
            message_ids_stmt=message_ids_stmt,
        )
        stmt = (
            update(MessageReceipt)
            .where(
                MessageReceipt.id_user == recipient_user_id,
                MessageReceipt.id_message.in_(message_ids_stmt),
                MessageReceipt.delivered_at.is_(None),
            )
            .values(delivered_at=func.now())
            .returning(MessageReceipt.id_message)
        )
        result = await self._session.execute(stmt)
        return [int(message_id) for message_id in result.scalars().all()]

    async def mark_read(
        self,
        *,
        chat_id: int,
        recipient_user_id: str,
        message_ids: Sequence[int] | None = None,
        up_to_message_id: int | None = None,
    ) -> list[int]:
        if message_ids is not None and not message_ids and up_to_message_id is None:
            return []

        message_ids_stmt = self._build_recipient_message_ids_stmt(
            chat_id=chat_id,
            recipient_user_id=recipient_user_id,
            message_ids=message_ids,
            up_to_message_id=up_to_message_id,
        )
        await self._ensure_receipts_for_recipient(
            recipient_user_id=recipient_user_id,
            message_ids_stmt=message_ids_stmt,
        )
        stmt = (
            update(MessageReceipt)
            .where(
                MessageReceipt.id_user == recipient_user_id,
                MessageReceipt.id_message.in_(message_ids_stmt),
                MessageReceipt.read_at.is_(None),
            )
            .values(
                delivered_at=func.coalesce(MessageReceipt.delivered_at, func.now()),
                read_at=func.now(),
            )
            .returning(MessageReceipt.id_message)
        )
        result = await self._session.execute(stmt)
        return [int(message_id) for message_id in result.scalars().all()]

    async def _create_receipts_for_new_message(self, *, message_id: int, chat_id: int, sender_user_id: str) -> None:
        await self._session.execute(
            pg_insert(MessageReceipt).from_select(
                ["id_message", "id_user"],
                select(
                    Message.id.label("id_message"),
                    ChatParticipant.id_user.label("id_user"),
                ).where(
                    Message.id == message_id,
                    Message.id_chat == chat_id,
                ).join(
                    ChatParticipant,
                    ChatParticipant.id_chat == Message.id_chat,
                ).where(
                    ChatParticipant.id_user != sender_user_id,
                    ChatParticipant.left_at.is_(None),
                ),
            ).on_conflict_do_nothing(
                index_elements=[MessageReceipt.id_message, MessageReceipt.id_user],
            )
        )

    async def _ensure_receipts_for_recipient(
        self,
        *,
        recipient_user_id: str,
        message_ids_stmt,
    ) -> None:
        message_ids_subquery = message_ids_stmt.subquery()
        await self._session.execute(
            pg_insert(MessageReceipt).from_select(
                ["id_message", "id_user"],
                select(
                    message_ids_subquery.c.id.label("id_message"),
                    literal(recipient_user_id).label("id_user"),
                ),
            ).on_conflict_do_nothing(
                index_elements=[MessageReceipt.id_message, MessageReceipt.id_user],
            )
        )

    def _build_recipient_message_ids_stmt(
        self,
        *,
        chat_id: int,
        recipient_user_id: str,
        message_ids: Sequence[int] | None,
        up_to_message_id: int | None,
    ):
        stmt = select(Message.id).where(
            Message.id_chat == chat_id,
            Message.id_user != recipient_user_id,
        )
        if message_ids is not None:
            stmt = stmt.where(Message.id.in_(message_ids))
        if up_to_message_id is not None:
            stmt = stmt.where(Message.id <= up_to_message_id)
        return stmt

    async def exists_with_email_message_id(self, *, email_message_id: str) -> bool:
        marker = f"{EMAIL_MESSAGE_ID_MARKER}{email_message_id}]"
        stmt = select(Message.id).where(Message.text.contains(marker)).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

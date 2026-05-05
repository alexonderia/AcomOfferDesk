from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import BigInteger, Select, and_, cast, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.auth_models import UserAuthAccount, UserContactChannel
from app.models.orm_models import Chat, File, Message, MessageFile, Offer, OfferFile, User


class OfferRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, *, request_id: int, contractor_user_id: str, offer_amount: float | None = None) -> Offer:
        offer = Offer(id_request=request_id, id_user=contractor_user_id, offer_amount=offer_amount)
        self._session.add(offer)
        await self._session.flush()
        return offer

    async def get_by_id(self, *, offer_id: int) -> Offer | None:
        stmt = select(Offer).where(Offer.id == offer_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_status(self, *, offer: Offer, status: str) -> None:
        offer.status = status

    async def update_amount(self, *, offer: Offer, offer_amount: float) -> None:
        offer.offer_amount = offer_amount

    async def get_contractor_offer_for_request(self, *, request_id: int, contractor_user_id: str) -> Offer | None:
        stmt: Select[tuple[Offer]] = (
            select(Offer)
            .where(Offer.id_request == request_id, Offer.id_user == contractor_user_id)
            .order_by(Offer.created_at.desc(), Offer.id.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_latest_contractor_offers_by_request_ids(
        self,
        *,
        contractor_user_id: str,
        request_ids: Sequence[int],
    ) -> list[Offer]:
        if not request_ids:
            return []

        stmt: Select[tuple[Offer]] = (
            select(Offer)
            .where(Offer.id_request.in_(request_ids), Offer.id_user == contractor_user_id)
            .order_by(Offer.id_request.asc(), Offer.created_at.desc(), Offer.id.desc())
        )
        result = await self._session.execute(stmt)

        latest_by_request_id: dict[int, Offer] = {}
        for offer in result.scalars().all():
            latest_by_request_id.setdefault(offer.id_request, offer)
        return list(latest_by_request_id.values())

    async def list_by_request(self, *, request_id: int) -> list[Offer]:
        stmt: Select[tuple[Offer]] = (
            select(Offer)
            .where(Offer.id_request == request_id)
            .order_by(Offer.created_at.desc(), Offer.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_offer_files(self, *, offer_id: int) -> list[File]:
        stmt: Select[tuple[File]] = (
            select(File)
            .options(joinedload(File.storage_object))
            .join(OfferFile, OfferFile.id == File.id)
            .where(OfferFile.id_offer == offer_id)
            .order_by(File.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_offer_files_by_offer_ids(self, *, offer_ids: Sequence[int]) -> list[tuple[int, File]]:
        if not offer_ids:
            return []

        stmt: Select[tuple[int, File]] = (
            select(OfferFile.id_offer, File)
            .options(joinedload(File.storage_object))
            .join(File, File.id == OfferFile.id)
            .where(OfferFile.id_offer.in_(offer_ids))
            .order_by(OfferFile.id_offer.asc(), File.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def attach_file(self, *, offer_id: int, file_id: int) -> None:
        self._session.add(OfferFile(id=file_id, id_offer=offer_id))

    async def detach_file(self, *, offer_id: int, file_id: int) -> bool:
        stmt = delete(OfferFile).where(OfferFile.id_offer == offer_id, OfferFile.id == file_id)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)

    async def get_chat(self, *, offer_id: int) -> Chat | None:
        stmt = select(Chat).where(Chat.id == offer_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_contractor_tg_ids_for_request(self, *, request_id: int, contractor_role_id: int) -> list[int]:
        stmt = (
            select(cast(UserAuthAccount.external_subject_id, BigInteger))
            .select_from(Offer)
            .join(User, User.id == Offer.id_user)
            .join(
                UserAuthAccount,
                and_(
                    UserAuthAccount.id_user == User.id,
                    UserAuthAccount.provider == "telegram",
                    UserAuthAccount.is_active.is_(True),
                ),
            )
            .join(
                UserContactChannel,
                and_(
                    UserContactChannel.id_user == User.id,
                    UserContactChannel.channel_type == "telegram",
                    UserContactChannel.channel_value == UserAuthAccount.external_subject_id,
                    UserContactChannel.is_active.is_(True),
                    UserContactChannel.is_verified.is_(True),
                ),
            )
            .where(Offer.id_request == request_id)
            .where(User.id_role == contractor_role_id)
            .where(User.status == "active")
            .distinct()
            .order_by(cast(UserAuthAccount.external_subject_id, BigInteger).asc())
        )
        result = await self._session.execute(stmt)
        return [tg_id for tg_id in result.scalars().all() if tg_id is not None]

    async def is_file_linked(self, *, offer_id: int, file_id: int) -> bool:
        stmt = select(OfferFile.id).where(OfferFile.id_offer == offer_id, OfferFile.id == file_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        stmt = (
            select(OfferFile.id)
            .join(Offer, Offer.id == OfferFile.id_offer)
            .where(OfferFile.id == file_id, Offer.id_user == contractor_user_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def is_message_file_linked_to_contractor(self, *, contractor_user_id: str, file_id: int) -> bool:
        stmt = (
            select(MessageFile.id)
            .join(Message, Message.id == MessageFile.id_message)
            .join(Chat, Chat.id == Message.id_chat)
            .join(Offer, Offer.id == Chat.id)
            .where(MessageFile.id == file_id, Offer.id_user == contractor_user_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

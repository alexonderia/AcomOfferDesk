from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm_models import FeedBack


class FeedBackRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, *, text: str) -> FeedBack:
        feedback = FeedBack(text=text)
        self._session.add(feedback)
        await self._session.flush()
        return feedback
    
    async def list_items(self) -> list[FeedBack]:
        result = await self._session.execute(select(FeedBack).order_by(FeedBack.id.desc()))
        return list(result.scalars().all())
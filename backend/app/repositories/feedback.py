from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_expression

from app.models.orm_models import FeedBack, Profile


class FeedBackRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, *, text: str, author_user_id: str) -> FeedBack:
        feedback = FeedBack(text=text, author_user_id=author_user_id, created_at=datetime.now(timezone.utc))
        self._session.add(feedback)
        await self._session.flush()
        return feedback
    
    async def list_items(self) -> list[FeedBack]:
        result = await self._session.execute(select(FeedBack).order_by(FeedBack.id.desc()))
        return list(result.scalars().all())

    async def list_page(self, *, search: str, author_user_id: str | None, sort_by: str, sort_order: str, limit: int, offset: int):
        filters = []
        if search.strip():
            filters.append(or_(FeedBack.text.icontains(search.strip(), autoescape=True), Profile.full_name.icontains(search.strip(), autoescape=True), FeedBack.author_user_id.icontains(search.strip(), autoescape=True)))
        if author_user_id:
            filters.append(FeedBack.author_user_id == author_user_id)
        count = select(func.count(FeedBack.id)).outerjoin(Profile, Profile.id == FeedBack.author_user_id).where(*filters)
        total = int((await self._session.execute(count)).scalar_one())
        field = {"id": FeedBack.id, "created_at": FeedBack.created_at, "author": Profile.full_name, "text": FeedBack.text}[sort_by]
        order = field.asc().nulls_last() if sort_order == "asc" else field.desc().nulls_last()
        query = (select(FeedBack).outerjoin(Profile, Profile.id == FeedBack.author_user_id)
                 .options(with_expression(FeedBack.author_name, Profile.full_name)).where(*filters)
                 .order_by(order, FeedBack.id.desc()).limit(limit).offset(offset))
        return list((await self._session.execute(query)).scalars().all()), total

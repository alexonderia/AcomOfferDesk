from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.policies import CurrentUser, UserPolicy
from app.repositories.feedback import FeedBackRepository


@dataclass(frozen=True)
class FeedBackCreateResult:
    feedback_id: int

@dataclass(frozen=True)
class FeedBackItem:
    id: int
    text: str
    author_user_id: str | None = None
    author_name: str | None = None
    created_at: datetime | None = None


class FeedBackService:
    def __init__(self, feedback: FeedBackRepository):
        self._feedback = feedback

    async def create_feedback(self, *, current_user: CurrentUser, text: str) -> FeedBackCreateResult:
        UserPolicy.ensure_can_create_feedback(current_user)
        item = await self._feedback.create(text=text, author_user_id=current_user.user_id)
        return FeedBackCreateResult(feedback_id=item.id)

    async def list_feedback(self, *, current_user: CurrentUser) -> list[FeedBackItem]:
        UserPolicy.ensure_can_view_feedback(current_user)
        items = await self._feedback.list_items()
        return [FeedBackItem(id=item.id, text=item.text) for item in items]

    async def list_page(self, *, current_user: CurrentUser, search: str = "", author_user_id: str | None = None,
                        sort_by: str = "created_at", sort_order: str = "desc", limit: int = 50, offset: int = 0):
        UserPolicy.ensure_can_view_feedback(current_user)
        items, total = await self._feedback.list_page(search=search, author_user_id=author_user_id, sort_by=sort_by, sort_order=sort_order, limit=limit, offset=offset)
        return [FeedBackItem(id=item.id, text=item.text, author_user_id=getattr(item, "author_user_id", None), author_name=getattr(item, "author_name", None), created_at=getattr(item, "created_at", None)) for item in items], total

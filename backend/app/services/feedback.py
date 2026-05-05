from __future__ import annotations

from dataclasses import dataclass

from app.domain.policies import CurrentUser, UserPolicy
from app.repositories.feedback import FeedBackRepository


@dataclass(frozen=True)
class FeedBackCreateResult:
    feedback_id: int

@dataclass(frozen=True)
class FeedBackItem:
    id: int
    text: str


class FeedBackService:
    def __init__(self, feedback: FeedBackRepository):
        self._feedback = feedback

    async def create_feedback(self, *, current_user: CurrentUser, text: str) -> FeedBackCreateResult:
        UserPolicy.ensure_can_create_feedback(current_user)
        item = await self._feedback.create(text=text)
        return FeedBackCreateResult(feedback_id=item.id)

    async def list_feedback(self, *, current_user: CurrentUser) -> list[FeedBackItem]:
        UserPolicy.ensure_can_view_feedback(current_user)
        items = await self._feedback.list_items()
        return [FeedBackItem(id=item.id, text=item.text) for item in items]

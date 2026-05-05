from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.feedback import FeedBackCreateRequest, FeedBackCreateResponse, FeedBackListResponse
from app.schemas.links import Link, LinkSet
from app.services.feedback import FeedBackService

router = APIRouter()


@router.post("/feedback", response_model=FeedBackCreateResponse)
@router.post("/feedback/", response_model=FeedBackCreateResponse, include_in_schema=False)
async def create_feedback(
    payload: FeedBackCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> FeedBackCreateResponse:
    async with uow:
        service = FeedBackService(uow.feedback)
        result = await service.create_feedback(current_user=current_user, text=payload.text.strip())

    return FeedBackCreateResponse(
        data={"feedback_id": result.feedback_id},
        _links=LinkSet(
            self=Link(href="/api/v1/feedback", method="POST"),
        ),
    )

@router.get("/feedback", response_model=FeedBackListResponse)
@router.get("/feedback/", response_model=FeedBackListResponse, include_in_schema=False)
async def list_feedback(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> FeedBackListResponse:
    async with uow:
        service = FeedBackService(uow.feedback)
        items = await service.list_feedback(current_user=current_user)
    serialized_items = [{"id": item.id, "text": item.text} for item in items]

    return FeedBackListResponse(
        data={"items": serialized_items},
        _links=LinkSet(
            self=Link(href="/api/v1/feedback", method="GET"),
        ),
    )

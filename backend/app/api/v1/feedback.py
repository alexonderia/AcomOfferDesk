from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.feedback import FeedBackCreateRequest, FeedBackCreateResponse, FeedBackListResponse
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
    )

@router.get("/feedback", response_model=FeedBackListResponse)
@router.get("/feedback/", response_model=FeedBackListResponse, include_in_schema=False)
async def list_feedback(
    search: str = Query(default="", max_length=200),
    author_user_id: str | None = Query(default=None, max_length=128),
    sort_by: Literal["id", "created_at", "author", "text"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> FeedBackListResponse:
    async with uow:
        service = FeedBackService(uow.feedback)
        items, total = await service.list_page(current_user=current_user, search=search, author_user_id=author_user_id, sort_by=sort_by, sort_order=sort_order, limit=limit, offset=offset)
    serialized_items = [asdict(item) for item in items]

    return FeedBackListResponse(
        data={"items": serialized_items, "total": total, "limit": limit, "offset": offset},
    )

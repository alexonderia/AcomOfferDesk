from __future__ import annotations

from fastapi import APIRouter, Depends, Path as PathParam, Query

from app.api.dependencies import get_current_user, get_uow
from app.core.uow import UnitOfWork
from app.domain.policies import CurrentUser
from app.schemas.notifications import (
    NotificationItemSchema,
    NotificationListData,
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationMarkReadResponse,
    NotificationUnreadCountResponse,
)
from app.services.notifications import NotificationService, notification_to_dict

router = APIRouter()

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


def _build_service(uow: UnitOfWork) -> NotificationService:
    notifications_repo = getattr(uow, "notifications", None)
    if notifications_repo is None:
        raise RuntimeError("Notifications repository is not configured")
    return NotificationService(notifications_repo)


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationListResponse:
    async with uow:
        service = _build_service(uow)
        items = await service.list_for_current_user(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset,
        )

    return NotificationListResponse(
        data=NotificationListData(
            items=[NotificationItemSchema(**notification_to_dict(item)) for item in items],
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/notifications/unread-count", response_model=NotificationUnreadCountResponse)
async def get_unread_count(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationUnreadCountResponse:
    async with uow:
        service = _build_service(uow)
        count = await service.count_unread_for_current_user(user_id=current_user.user_id)

    return NotificationUnreadCountResponse(data={"count": count})


@router.patch("/notifications/{notification_id}/read", response_model=NotificationMarkReadResponse)
async def mark_notification_read(
    notification_id: int = PathParam(..., ge=1),
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationMarkReadResponse:
    async with uow:
        service = _build_service(uow)
        notification = await service.mark_as_read_for_current_user(
            user_id=current_user.user_id,
            notification_id=notification_id,
        )
    notification_data = notification_to_dict(notification)
    return NotificationMarkReadResponse(
        data={
            "notification_id": notification.id,
            "read_at": notification_data["read_at"],
        }
    )


@router.patch("/notifications/read-all", response_model=NotificationMarkAllReadResponse)
async def mark_all_notifications_read(
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> NotificationMarkAllReadResponse:
    async with uow:
        service = _build_service(uow)
        updated_count = await service.mark_all_as_read_for_current_user(user_id=current_user.user_id)

    return NotificationMarkAllReadResponse(data={"updated_count": updated_count})

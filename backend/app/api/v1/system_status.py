from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden
from app.schemas.system_status import SystemStatusResponse
from app.services.system_status import SystemStatusService


router = APIRouter()
status_service = SystemStatusService()


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    response: Response, current_user: CurrentUser = Depends(get_current_user),
) -> SystemStatusResponse:
    if current_user.role_id != settings.superadmin_role_id or current_user.status != "active":
        raise Forbidden("Состояние системы доступно только суперадминистратору")
    response.headers["Cache-Control"] = "no-store"
    return SystemStatusResponse(data=await status_service.get_status())

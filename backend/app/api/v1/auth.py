from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_uow
from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.authentication import reject_unavailable_authentication
from app.domain.auth_context import CurrentUser
from app.domain.policies import UserPolicy
from app.schemas.auth import RegisterUserRequest, RegisterUserResponse
from app.services.email_verification import EmailVerificationService
from app.services.unit_hierarchy import UnitHierarchyService
from app.services.units import UnitService
from app.services.users import UserRegistrationService

router = APIRouter()


class RequestEmailVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)


class EmailVerificationActionResponse(BaseModel):
    detail: str


@router.get("/auth/oidc/login")
@router.get("/auth/oidc/register")
@router.get("/auth/callback")
@router.post("/auth/refresh")
@router.post("/auth/logout")
async def unavailable_authentication_flow() -> None:
    """Keep legacy auth URLs explicit and fail closed during the IAM transition."""

    reject_unavailable_authentication()


@router.post("/auth/request-email-verification", response_model=EmailVerificationActionResponse)
async def request_email_verification(
    payload: RequestEmailVerificationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> EmailVerificationActionResponse:
    UserPolicy.ensure_can_manage_own_profile(current_user)
    async with uow:
        service = EmailVerificationService(uow.profiles, uow.user_contact_channels)
        result = await service.request_profile_verification(user_id=current_user.user_id, email=payload.email)

    if result == "same_email":
        return EmailVerificationActionResponse(detail="Указан текущий подтверждённый email")
    if result == "already_sent":
        return EmailVerificationActionResponse(detail="Письмо уже отправлено. Проверьте вашу почту")
    return EmailVerificationActionResponse(detail="Письмо для подтверждения email отправлено")


@router.get("/auth/verify-email", response_model=EmailVerificationActionResponse)
async def verify_email(
    token: str = Query(..., min_length=20),
    uow: UnitOfWork = Depends(get_uow),
) -> EmailVerificationActionResponse:
    async with uow:
        service = EmailVerificationService(uow.profiles, uow.user_contact_channels)
        updated = await service.confirm_profile_verification(token=token)

    if updated:
        return EmailVerificationActionResponse(detail="Email подтверждён")
    return EmailVerificationActionResponse(detail="Email уже подтверждён")


@router.post("/users/register", response_model=RegisterUserResponse)
async def register_user(
    payload: RegisterUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> RegisterUserResponse:
    UserPolicy.ensure_can_register_user(current_user)
    async with uow:
        service = UserRegistrationService(uow.users, uow.profiles, uow.user_auth_accounts)
        user = await service.register_user(
            current_user,
            user_id=payload.login.strip(),
            password=payload.password.strip() if payload.password else None,
            role_id=payload.role_id,
            id_parent=payload.id_parent.strip() if payload.id_parent else None,
            full_name=payload.full_name.strip() if payload.full_name else None,
            phone=payload.phone.strip() if payload.phone else None,
            mail=payload.mail.strip() if payload.mail else None,
        )
        unit_service = UnitService(uow.units, uow.users)
        if payload.unit_id is not None:
            if UserPolicy.can_manage_unit_members(current_user):
                await unit_service.add_member(
                    current_user=current_user,
                    unit_id=payload.unit_id,
                    user_id=user.id,
                )
            else:
                await unit_service.add_member_on_registration(
                    current_user=current_user,
                    unit_id=payload.unit_id,
                    user_id=user.id,
                )
        else:
            hierarchy = UnitHierarchyService(uow.users)
            seed_unit_ids = await hierarchy.get_management_seed_unit_ids(user_id=current_user.user_id)
            for seed_unit_id in sorted(seed_unit_ids):
                await unit_service.add_member_on_registration(
                    current_user=current_user,
                    unit_id=seed_unit_id,
                    user_id=user.id,
                )
    return RegisterUserResponse(
        data={
            "user_id": user.id,
            "role_id": user.id_role,
            "status": user.status,
        },
    )

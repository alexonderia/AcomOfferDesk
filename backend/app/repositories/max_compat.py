from __future__ import annotations

from app.models.orm_models import MaxUser


def max_subject_value(max_user_id: int | str) -> str:
    return str(max_user_id).strip()


def derive_max_status(
    *,
    account_is_active: bool | None,
    channel_is_verified: bool | None,
    channel_is_active: bool | None,
    user_status: str | None = None,
) -> str | None:
    if account_is_active is None and channel_is_verified is None and channel_is_active is None:
        return None
    if user_status in {"inactive", "blacklist"}:
        return "disapproved"
    if account_is_active is False or channel_is_active is False:
        return "disapproved"
    if channel_is_verified and user_status == "active":
        return "approved"
    return "review"


def build_max_user(
    *,
    max_user_id: int | str | None,
    account_is_active: bool | None,
    channel_is_verified: bool | None,
    channel_is_active: bool | None,
    user_status: str | None = None,
) -> MaxUser | None:
    if max_user_id is None:
        return None
    status = derive_max_status(
        account_is_active=account_is_active,
        channel_is_verified=channel_is_verified,
        channel_is_active=channel_is_active,
        user_status=user_status,
    )
    if status is None:
        return None
    return MaxUser(id=max_subject_value(max_user_id), status=status)

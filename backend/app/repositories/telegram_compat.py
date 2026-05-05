from __future__ import annotations

from app.models.orm_models import TgUser


def telegram_subject_value(tg_id: int) -> str:
    return str(tg_id).strip()


def derive_tg_status(
    *,
    account_is_active: bool | None,
    channel_is_verified: bool | None,
    channel_is_active: bool | None,
) -> str | None:
    if account_is_active is None and channel_is_verified is None and channel_is_active is None:
        return None
    if account_is_active is False or channel_is_active is False:
        return "disapproved"
    if channel_is_verified:
        return "approved"
    return "review"


def build_tg_user(
    *,
    tg_id: int | None,
    account_is_active: bool | None,
    channel_is_verified: bool | None,
    channel_is_active: bool | None,
) -> TgUser | None:
    if tg_id is None:
        return None
    status = derive_tg_status(
        account_is_active=account_is_active,
        channel_is_verified=channel_is_verified,
        channel_is_active=channel_is_active,
    )
    if status is None:
        return None
    return TgUser(id=tg_id, status=status)

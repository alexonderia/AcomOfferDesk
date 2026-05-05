from __future__ import annotations

from app.models.orm_models import TgUser
from app.repositories.tg_users import TgUserRepository


class TgUserRegistrationService:
    def __init__(self, tg_users: TgUserRepository):
        self._tg_users = tg_users

    async def register(self, tg_id: int) -> TgUser:
        # Current DB schema does not persist standalone tg_users rows.
        return await self._tg_users.get_or_create(tg_id)

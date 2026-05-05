from __future__ import annotations

from app.core.security import create_access_token, verify_password
from app.domain.exceptions import Forbidden, NotFound
from app.domain.policies import UserPolicy
from app.repositories.users import UserRepository


class AuthService:
    def __init__(self, users: UserRepository):
        self._users = users

    async def login(self, login: str, password: str) -> tuple[str, int]:
        user = await self._users.get_by_id(login)
        if not user:
            raise NotFound("User not found")
        password_hash = getattr(user, "password_hash", None)
        if not password_hash:
            raise Forbidden("Password is managed by the identity provider")
        if not await verify_password(password, password_hash):
            raise Forbidden("Invalid credentials")
        UserPolicy.ensure_can_login(user.status)
        token = await create_access_token(subject=user.id, role_id=user.id_role)
        return token, user.id_role

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

from app.core.config import settings
from app.domain.exceptions import Conflict
from app.models.orm_models import TgUser
from app.repositories.requests import RequestRepository
from app.repositories.tg_users import TgUserRepository
from app.repositories.users import UserRepository
from app.services.tg_registration_links import build_keycloak_registration_link, create_tg_registration_token


@dataclass(frozen=True)
class TgOpenRequestItem:
    request_id: int
    description: str | None
    deadline_at: datetime
    link: str


@dataclass(frozen=True)
class TgStartResult:
    tg_user: TgUser
    action: str
    registration_link: str | None
    requests: list[TgOpenRequestItem]
    user_status: str | None


class TgStartService:
    def __init__(
        self,
        tg_users: TgUserRepository,
        users: UserRepository,
        requests: RequestRepository,
    ) -> None:
        self._tg_users = tg_users
        self._users = users
        self._requests = requests

    async def handle_start(self, tg_id: int) -> TgStartResult:
        tg_user = await self._tg_users.get_or_create(tg_id)

        linked_user = await self._users.get_by_tg_user_id(tg_id)
        if linked_user and linked_user.id_role == settings.contractor_role_id and linked_user.status == "active" and tg_user.status == "approved":
            open_requests = await self._requests.list_open_for_contractor(contractor_user_id=linked_user.id)
            request_items = [
                TgOpenRequestItem(
                    request_id=request.id,
                    description=request.description,
                    deadline_at=request.deadline_at,
                    link=self._build_authorization_link(request_id=request.id),
                )
                for request in open_requests
            ]
            return TgStartResult(
                tg_user=tg_user,
                action="open_requests",
                registration_link=None,
                requests=request_items,
                user_status=linked_user.status,
            )

        if linked_user:
            return TgStartResult(
                tg_user=tg_user,
                action="pending",
                registration_link=None,
                requests=[],
                user_status=linked_user.status,
            )
        if tg_user.status == "disapproved":
            return TgStartResult(
                tg_user=tg_user,
                action="pending",
                registration_link=None,
                requests=[],
                user_status=linked_user.status if linked_user else None,
            )
        
        return TgStartResult(
            tg_user=tg_user,
            action="register",
            registration_link=self._build_registration_link(tg_id=tg_id),
            requests=[],
            user_status=None,
        )

    def _build_registration_link(self, *, tg_id: int) -> str:
        if not settings.tg_link_secret or not (settings.web_base_url or settings.public_backend_base_url):
            raise Conflict("TG links are not configured")
        code = create_tg_registration_token(tg_id=tg_id)
        return build_keycloak_registration_link(token=code)

    def _build_authorization_link(self, *, request_id: int) -> str:
        if not settings.public_backend_base_url:
            raise Conflict("TG links are not configured")
        next_path = quote(f"/requests/{request_id}/contractor", safe="/")
        return f"{settings.public_backend_base_url.rstrip('/')}/login?next={next_path}"

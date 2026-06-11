from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

from app.core.config import settings
from app.domain.exceptions import Conflict
from app.repositories.max_users import MaxUserRepository
from app.repositories.requests import RequestRepository
from app.repositories.users import UserRepository
from app.services.max_registration_links import build_keycloak_max_registration_link, create_max_registration_token


@dataclass(frozen=True)
class MaxOpenRequestItem:
    id: str
    description: str | None
    deadline_at: datetime
    url: str


@dataclass(frozen=True)
class MaxStartResult:
    action: str
    registration_url: str | None
    requests: list[MaxOpenRequestItem]


class MaxStartService:
    def __init__(
        self,
        max_users: MaxUserRepository,
        users: UserRepository,
        requests: RequestRepository,
    ) -> None:
        self._max_users = max_users
        self._users = users
        self._requests = requests

    async def handle_start(self, max_user_id: str) -> MaxStartResult:
        normalized_id = str(max_user_id).strip()
        max_user = await self._max_users.get_or_create(normalized_id)
        linked_user = await self._users.get_by_max_user_id(normalized_id)

        if linked_user is not None and self._is_blocked(linked_user.status, max_user.status):
            return MaxStartResult(action="blocked", registration_url=None, requests=[])

        if linked_user is None:
            return MaxStartResult(
                action="register",
                registration_url=self._build_registration_url(max_user_id=normalized_id),
                requests=[],
            )

        if linked_user.status != "active" or max_user.status != "approved":
            return MaxStartResult(action="pending", registration_url=None, requests=[])

        if linked_user.id_role != settings.contractor_role_id:
            return MaxStartResult(action="pending", registration_url=None, requests=[])

        open_requests = await self._requests.list_open_for_contractor(contractor_user_id=linked_user.id)
        request_items = [
            MaxOpenRequestItem(
                id=request.id,
                description=request.description,
                deadline_at=request.deadline_at,
                url=self._build_request_url(request_id=request.id),
            )
            for request in open_requests
        ]
        return MaxStartResult(
            action="open_requests",
            registration_url=None,
            requests=request_items,
        )

    @staticmethod
    def _is_blocked(user_status: str, max_status: str) -> bool:
        if user_status in {"inactive", "blacklist"}:
            return True
        return max_status == "disapproved"

    def _build_registration_url(self, *, max_user_id: str) -> str:
        if not settings.max_link_secret or not settings.public_backend_base_url:
            raise Conflict("MAX links are not configured")
        code = create_max_registration_token(max_user_id=max_user_id)
        return build_keycloak_max_registration_link(token=code)

    def _build_request_url(self, *, request_id: str) -> str:
        if not settings.public_backend_base_url:
            raise Conflict("MAX links are not configured")
        next_path = quote(f"/requests/{request_id}/contractor", safe="/")
        return f"{settings.public_backend_base_url.rstrip('/')}/login?next={next_path}"

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import httpx

from app.core.config import settings

StartAction = Literal["register", "pending", "open_requests", "blocked"]


class BackendClientError(RuntimeError):
    pass


@dataclass(slots=True)
class MaxOpenRequestItem:
    id: str
    description: str | None
    deadline_at: datetime | None
    url: str | None


@dataclass(slots=True)
class MaxStartResponse:
    action: StartAction
    registration_url: str | None
    requests: list[MaxOpenRequestItem]


@dataclass(slots=True)
class BackendClient:
    base_url: str
    timeout_seconds: float

    async def start(
        self,
        max_user_id: str,
        *,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> MaxStartResponse:
        payload = {
            "max_user_id": max_user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        }
        response = await self._post("/api/v1/max/start", payload)
        return self._parse_start_response(response)

    async def create_register_link(self, max_user_id: str) -> str:
        response = await self._post("/api/v1/max/links/register", {"max_user_id": max_user_id})
        public_base_url = settings.public_backend_base_url or self.base_url
        url = response.get("data", {}).get("url")
        resolved = _resolve_link(public_base_url, url)
        if not resolved:
            raise BackendClientError("Invalid backend response")
        return resolved

    async def _post(self, path: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(f"{self.base_url.rstrip('/')}{path}", json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise BackendClientError("Backend request failed") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise BackendClientError("Invalid backend response") from exc
        if not isinstance(body, dict):
            raise BackendClientError("Invalid backend response")
        return body

    def _parse_start_response(self, body: dict) -> MaxStartResponse:
        action = body.get("action")
        if action not in {"register", "pending", "open_requests", "blocked"}:
            raise BackendClientError("Unexpected backend action")

        public_base_url = settings.public_backend_base_url or self.base_url
        requests: list[MaxOpenRequestItem] = []
        for item in body.get("requests", []):
            if not isinstance(item, dict):
                raise BackendClientError("Invalid backend response")
            deadline_raw = item.get("deadline_at")
            deadline_at: datetime | None = None
            if isinstance(deadline_raw, str) and deadline_raw:
                normalized = deadline_raw.replace("Z", "+00:00")
                try:
                    deadline_at = datetime.fromisoformat(normalized)
                except ValueError:
                    deadline_at = None
            requests.append(
                MaxOpenRequestItem(
                    id=str(item.get("id", "")),
                    description=item.get("description"),
                    deadline_at=deadline_at,
                    url=_resolve_link(public_base_url, item.get("url")),
                )
            )

        return MaxStartResponse(
            action=action,
            registration_url=_resolve_link(public_base_url, body.get("registration_url")),
            requests=requests,
        )


def get_backend_client() -> BackendClient:
    return BackendClient(
        base_url=settings.backend_base_url.rstrip("/"),
        timeout_seconds=settings.max_bot_timeout_seconds,
    )


def _resolve_link(base_url: str, link: str | None) -> str | None:
    if not link:
        return None
    if link.startswith("http://") or link.startswith("https://"):
        return link
    if not link.startswith("/"):
        return f"{base_url.rstrip('/')}/{link}"
    return f"{base_url.rstrip('/')}{link}"

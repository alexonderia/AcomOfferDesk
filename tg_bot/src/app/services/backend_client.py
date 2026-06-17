from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings


class BackendClientError(RuntimeError):
    pass


@dataclass(slots=True)
class BackendClient:
    base_url: str

    async def start(self, tg_id: int) -> "TgStartResponse":
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/tg/start",
                    json={"tg_id": tg_id},
                    headers=_bot_api_headers(),
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise BackendClientError("Backend request failed") from exc
        payload = response.json().get("data", {})
        public_base_url = settings.public_backend_base_url or self.base_url
        requests = [
            TgOpenRequestItem(
                request_id=item["request_id"],
                description=item.get("description"),
                deadline_at=item["deadline_at"],
                link=_resolve_link(public_base_url, item["link"]),
            )
            for item in payload.get("requests", [])
        ]
        return TgStartResponse(
            action=payload.get("action", ""),
            registration_link=_resolve_link(public_base_url, payload.get("registration_link")),
            requests=requests,
            tg_status=payload.get("tg_status"),
            user_status=payload.get("user_status"),
        )

    async def get_register_link(self, tg_id: int) -> str:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/tg/links/register",
                    json={"tg_id": tg_id},
                    headers=_bot_api_headers(),
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise BackendClientError("Backend request failed") from exc
        payload = response.json().get("data", {})
        public_base_url = settings.public_backend_base_url or self.base_url
        return _resolve_link(public_base_url, payload.get("url")) or ""

@dataclass(slots=True)
class TgOpenRequestItem:
    request_id: int
    description: str | None
    deadline_at: str
    link: str


@dataclass(slots=True)
class TgStartResponse:
    action: str
    registration_link: str | None
    requests: list[TgOpenRequestItem]
    tg_status: str | None
    user_status: str | None


def _bot_api_headers() -> dict[str, str]:
    shared_secret = (settings.bot_api_shared_secret or "").strip()
    if shared_secret:
        return {"X-Bot-Api-Secret": shared_secret}
    return {}


def get_backend_client() -> BackendClient:
    return BackendClient(base_url=settings.backend_base_url.rstrip("/"))


def _resolve_link(base_url: str, link: str | None) -> str | None:
    if not link:
        return None
    if link.startswith("http://") or link.startswith("https://"):
        return link
    if not link.startswith("/"):
        return f"{base_url.rstrip('/')}/{link}"
    return f"{base_url.rstrip('/')}{link}"
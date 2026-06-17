from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_MAX_API_BASE_URL = "https://platform-api.max.ru"

MAX_BOT_COMMANDS: tuple[dict[str, str], ...] = (
    {"name": "start", "description": "Регистрация или открытые заявки"},
    {"name": "info", "description": "Справка по сервису"},
)


async def register_bot_commands(
    *,
    token: str,
    api_base_url: str = _DEFAULT_MAX_API_BASE_URL,
    timeout_seconds: float = 10.0,
) -> None:
    normalized_token = token.strip()
    if not normalized_token:
        logger.warning("MAX_BOT_TOKEN is empty. Skip bot commands registration")
        return

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.patch(
                f"{api_base_url.rstrip('/')}/me",
                headers={"Authorization": normalized_token},
                json={"commands": list(MAX_BOT_COMMANDS)},
            )
            response.raise_for_status()
    except Exception:
        logger.warning("Failed to register MAX bot commands menu. Continue without menu", exc_info=True)

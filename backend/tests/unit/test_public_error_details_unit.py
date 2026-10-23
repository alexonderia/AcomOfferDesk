import json
import sys
from types import SimpleNamespace

import pytest

sys.modules.setdefault("fcntl", SimpleNamespace(LOCK_EX=0, LOCK_NB=0, LOCK_UN=0, flock=lambda *_: None))

from app.domain.exceptions import Conflict
from app.main import _normalize_public_error_detail, conflict_handler


def test_conflict_with_business_reason_keeps_specific_russian_message() -> None:
    assert _normalize_public_error_detail(
        status_code=409,
        detail="Нельзя закрыть заявку, пока есть нерассмотренные коммерческие предложения.",
    ) == "Нельзя закрыть заявку, пока есть нерассмотренные коммерческие предложения."


def test_conflict_without_business_reason_does_not_use_data_conflict_copy() -> None:
    assert _normalize_public_error_detail(status_code=409, detail=None) == (
        "Не удалось применить изменение. Повторите попытку."
    )


@pytest.mark.asyncio
async def test_conflict_handler_returns_business_reason_code() -> None:
    response = await conflict_handler(
        None,
        Conflict("Offer for this contractor already exists", reason_code="offer_already_exists"),
    )
    payload = json.loads(response.body)
    assert response.status_code == 409
    assert payload["reason_code"] == "offer_already_exists"

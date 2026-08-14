import pytest

from app.api.v1 import ws as ws_module
from app.domain.exceptions import AuthenticationUnavailable


class _FakeWebSocket:
    query_params: dict[str, str] = {"ticket": "legacy-ticket"}


@pytest.mark.asyncio
@pytest.mark.parametrize("purpose", ["realtime_ws", "notifications_ws"])
async def test_websocket_auth_fails_closed_during_iam_transition(purpose: str) -> None:
    with pytest.raises(AuthenticationUnavailable):
        await ws_module._get_current_user_from_websocket_with_purpose(  # noqa: SLF001
            _FakeWebSocket(),
            expected_purpose=purpose,
        )

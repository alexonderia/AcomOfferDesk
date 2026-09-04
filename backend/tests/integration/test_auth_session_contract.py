import pytest
from starlette.requests import Request

from app.api.dependencies import get_current_user
from app.domain.exceptions import Unauthorized


def _request(*, authorization: str | None = None) -> Request:
    headers = [] if authorization is None else [(b"authorization", authorization.encode("ascii"))]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/protected",
            "headers": headers,
            "scheme": "https",
            "server": ("app.example", 443),
            "client": ("127.0.0.1", 12345),
        }
    )


@pytest.mark.asyncio
async def test_protected_authentication_requires_iam_cookie() -> None:
    with pytest.raises(Unauthorized) as exc_info:
        await get_current_user(_request())
    assert str(exc_info.value) == "Missing credentials"


@pytest.mark.asyncio
async def test_authorization_header_cannot_enable_legacy_authentication() -> None:
    with pytest.raises(Unauthorized):
        await get_current_user(_request(authorization="Bearer legacy-token"))

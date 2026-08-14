import pytest

from app.api.dependencies import get_current_user
from app.domain.exceptions import AuthenticationUnavailable


@pytest.mark.asyncio
async def test_protected_authentication_dependency_fails_closed() -> None:
    with pytest.raises(AuthenticationUnavailable) as exc_info:
        await get_current_user()

    assert exc_info.value.status_code == 503
    assert exc_info.value.reason_code == "AUTH_SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_authorization_header_cannot_enable_legacy_authentication() -> None:
    # The dependency intentionally has no header/provider input at this stage.
    with pytest.raises(AuthenticationUnavailable):
        await get_current_user()

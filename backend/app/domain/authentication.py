from __future__ import annotations

from typing import NoReturn

from app.domain.exceptions import AuthenticationUnavailable


AUTH_SERVICE_UNAVAILABLE_CODE = "AUTH_SERVICE_UNAVAILABLE"


def reject_unavailable_authentication() -> NoReturn:
    """Fail closed until a supported IAM adapter provides an auth context."""

    raise AuthenticationUnavailable()

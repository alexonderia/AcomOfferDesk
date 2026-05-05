from __future__ import annotations

from fastapi import Response

from app.core.config import settings


def set_cookie(
    response: Response,
    *,
    key: str,
    value: str,
    max_age: int,
    path: str = "/api/v1/auth",
) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        domain=settings.refresh_cookie_domain or None,
        path=path,
    )


def clear_cookie(
    response: Response,
    *,
    key: str,
    path: str = "/api/v1/auth",
) -> None:
    response.delete_cookie(
        key=key,
        domain=settings.refresh_cookie_domain or None,
        path=path,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def set_refresh_cookie(response: Response, token: str, *, max_age: int) -> None:
    set_cookie(
        response,
        key=settings.refresh_cookie_name,
        value=token,
        max_age=max_age,
    )


def clear_refresh_cookie(response: Response) -> None:
    clear_cookie(response, key=settings.refresh_cookie_name)


def set_keycloak_refresh_cookie(response: Response, token: str, *, max_age: int) -> None:
    set_cookie(
        response,
        key=settings.keycloak_refresh_cookie_name,
        value=token,
        max_age=max_age,
    )


def clear_keycloak_refresh_cookie(response: Response) -> None:
    clear_cookie(response, key=settings.keycloak_refresh_cookie_name)


def set_keycloak_state_cookie(response: Response, token: str, *, max_age: int) -> None:
    set_cookie(
        response,
        key=settings.keycloak_state_cookie_name,
        value=token,
        max_age=max_age,
    )


def clear_keycloak_state_cookie(response: Response) -> None:
    clear_cookie(response, key=settings.keycloak_state_cookie_name)

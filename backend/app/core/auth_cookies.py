from __future__ import annotations

from fastapi import Response

from app.core.config import settings


ACCESS_COOKIE_PATH = "/"
AUTH_COOKIE_PATH = "/api/v1/auth"
IAM_BROWSER_SESSION_COOKIE_PATH = "/iam"


def set_iam_access_cookie(response: Response, token: str, *, max_age: int) -> None:
    response.set_cookie(
        key=settings.iam_access_cookie_name,
        value=token,
        max_age=max_age,
        path=ACCESS_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def clear_iam_access_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.iam_access_cookie_name,
        path=ACCESS_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def set_iam_refresh_cookie(response: Response, token: str, *, max_age: int) -> None:
    response.set_cookie(
        key=settings.iam_refresh_cookie_name,
        value=token,
        max_age=max_age,
        path=AUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def clear_iam_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.iam_refresh_cookie_name,
        path=AUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def set_iam_flow_cookie(response: Response, token: str, *, max_age: int) -> None:
    response.set_cookie(
        key=settings.iam_state_cookie_name,
        value=token,
        max_age=max_age,
        path=AUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def clear_iam_flow_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.iam_state_cookie_name,
        path=AUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def set_iam_flow_recovery_cookie(response: Response) -> None:
    response.set_cookie(
        key=settings.iam_flow_recovery_cookie_name,
        value="1",
        max_age=60,
        path=AUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def clear_iam_flow_recovery_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.iam_flow_recovery_cookie_name,
        path=AUTH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def clear_iam_browser_session_cookie(response: Response) -> None:
    """Clear the IAM UI session through the BFF response, never browser JS."""

    response.delete_cookie(
        key=settings.iam_browser_session_cookie_name,
        path=IAM_BROWSER_SESSION_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def set_csrf_cookie(response: Response, token: str, *, max_age: int) -> None:
    response.set_cookie(
        key=settings.iam_csrf_cookie_name,
        value=token,
        max_age=max_age,
        httponly=False,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/",
    )


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.iam_csrf_cookie_name,
        path="/",
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )

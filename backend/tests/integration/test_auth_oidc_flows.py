import pytest


@pytest.mark.parametrize("path", ["/api/v1/auth/oidc/login", "/api/v1/auth/oidc/register"])
def test_legacy_oidc_entrypoints_remain_unavailable_without_outbound_calls(
    test_client,
    monkeypatch,
    path: str,
) -> None:
    class _ForbiddenHttpClient:
        def __init__(self, *args, **kwargs) -> None:
            _ = args, kwargs
            raise AssertionError("legacy endpoint attempted an outbound HTTP request")

    monkeypatch.setattr("httpx.AsyncClient", _ForbiddenHttpClient)
    response = test_client.get(path)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Сервис авторизации временно недоступен.",
        "reason_code": "AUTH_SERVICE_UNAVAILABLE",
    }


def test_iam_callback_requires_code_and_state(test_client) -> None:
    response = test_client.get("/api/v1/auth/callback")
    assert response.status_code == 422


def test_iam_callback_with_expired_flow_retries_login_once_instead_of_returning_json(test_client) -> None:
    response = test_client.get(
        "/api/v1/auth/callback",
        params={"code": "c" * 20, "state": "s" * 16},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/api/v1/auth/login"
    assert "acom_iam_flow_recovery" in response.headers["set-cookie"]
    assert response.headers["set-cookie"]


def test_refresh_without_iam_cookie_is_unauthorized(test_client) -> None:
    response = test_client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_logout_without_iam_cookie_is_idempotent(test_client) -> None:
    response = test_client.post("/api/v1/auth/logout")
    assert response.status_code == 204


def test_oidc_login_never_redirects(test_client) -> None:
    response = test_client.get("/api/v1/auth/oidc/login", follow_redirects=False)
    assert response.status_code == 503
    assert "location" not in response.headers

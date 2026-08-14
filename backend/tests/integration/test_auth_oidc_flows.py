import pytest


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/auth/oidc/login"),
        ("get", "/api/v1/auth/oidc/register"),
        ("get", "/api/v1/auth/callback"),
        ("post", "/api/v1/auth/refresh"),
        ("post", "/api/v1/auth/logout"),
    ],
)
def test_legacy_oidc_runtime_is_unavailable_without_outbound_calls(
    test_client,
    monkeypatch,
    method: str,
    path: str,
) -> None:
    class _ForbiddenHttpClient:
        def __init__(self, *args, **kwargs) -> None:
            _ = args, kwargs
            raise AssertionError("auth endpoint attempted an outbound HTTP request")

    monkeypatch.setattr("httpx.AsyncClient", _ForbiddenHttpClient)

    response = getattr(test_client, method)(path)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Сервис авторизации временно недоступен.",
        "reason_code": "AUTH_SERVICE_UNAVAILABLE",
    }


def test_oidc_login_never_redirects(test_client) -> None:
    response = test_client.get("/api/v1/auth/oidc/login", follow_redirects=False)

    assert response.status_code == 503
    assert "location" not in response.headers

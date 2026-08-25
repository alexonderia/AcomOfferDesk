from __future__ import annotations

import pytest

from app.core.iam_flow import sanitize_next_path


@pytest.mark.parametrize(
    "next_path",
    [
        "https://evil.example",
        "//evil.example",
        "/\\evil.example",
        "/%5Cevil.example",
        "/%255Cevil.example",
        "/%2F%2Fevil.example",
        "/%252F%252Fevil.example",
        "javascript:alert(1)",
    ],
)
def test_sanitize_next_path_rejects_external_and_backslash_redirects(next_path: str) -> None:
    assert sanitize_next_path(next_path) == "/"


def test_sanitize_next_path_keeps_local_application_path() -> None:
    assert sanitize_next_path("/requests/123?tab=offers") == "/requests/123?tab=offers"

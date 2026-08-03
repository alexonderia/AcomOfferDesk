"""Global test bootstrap.

Ensures required application settings are present for tests without relying on
local `.env` files or real secrets.
"""

from __future__ import annotations

import os


def _ensure_test_env() -> None:
    defaults = {
        "APP_ENV": "development",
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
        "JWT_SECRET": "ci-test-jwt-secret",
        "EMAIL_ADDRESS": "ci@example.com",
        "EMAIL_APP_PASSWORD": "ci-email-app-password",
        "SMTP_HOST": "smtp.example.com",
        "EMAIL_VERIFICATION_SECRET": "ci-email-verification-secret",
        "S3_ENDPOINT": "localhost:9000",
        "S3_ACCESS_KEY": "ci-access-key",
        "S3_SECRET_KEY": "ci-secret-key",
        "S3_BUCKET": "ci-bucket",
        "PUBLIC_BACKEND_BASE_URL": "http://localhost:8080",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


_ensure_test_env()

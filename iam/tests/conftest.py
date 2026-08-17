from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


IAM_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IAM_ROOT))

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_private_key = _key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode("utf-8")
_public_key = _key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode("utf-8")

os.environ.update(
    {
        "APP_ENV": "test",
        "IAM_DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "IAM_PUBLIC_BASE_URL": "http://testserver/iam",
        "IAM_ISSUER": "http://testserver/iam",
        "IAM_AUDIENCE": "acomofferdesk-test",
        "IAM_ALLOWED_REDIRECT_URIS": "http://testserver/api/v1/auth/callback",
        "IAM_INTERNAL_SERVICE_TOKEN": "test-internal-service-token-value-1234567890",
        "IAM_SIGNING_PRIVATE_KEY": _private_key,
        "IAM_SIGNING_PUBLIC_KEY": _public_key,
        "IAM_AUTH_REQUEST_SECRET": "test-auth-request-secret-value-1234567890",
        "IAM_TOKEN_HASH_SECRET": "test-token-hash-secret-value-1234567890",
        "IAM_LOGIN_MAX_FAILURES": "3",
        "IAM_LOGIN_LOCK_SECONDS": "60",
    }
)

from iam_app.db import SessionLocal, engine  # noqa: E402
from iam_app.models import Base  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def clean_database() -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def session():
    async with SessionLocal() as db_session:
        yield db_session
        await db_session.rollback()

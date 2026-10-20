from __future__ import annotations

import time
import uuid
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from app.api import dependencies
from app.core.config import settings
from app.domain.authentication import IamAccessClaims, decode_iam_access_token
from app.domain.exceptions import Unauthorized
from app.domain.iam_identity import stable_iam_account_id
from app.domain.permissions import PermissionCodes


ACCOUNT_ID = "00000000-0000-4000-8000-000000000001"
SESSION_ID = "00000000-0000-4000-8000-000000000002"


@pytest.fixture
def rsa_keys(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    monkeypatch.setattr(settings, "iam_signing_public_key", public_pem)
    monkeypatch.setattr(settings, "iam_signing_kid", "test-kid")
    monkeypatch.setattr(settings, "iam_issuer", "https://issuer.example/iam")
    monkeypatch.setattr(settings, "iam_audience", "acom-test")
    return private_pem


def _token(private_key: str, **overrides) -> str:
    now = int(time.time())
    payload = {
        "sub": ACCOUNT_ID,
        "sid": SESSION_ID,
        "role": "economist",
        "permissions": [PermissionCodes.REQUESTS_READ],
        "iat": now,
        "exp": now + 300,
        "iss": "https://issuer.example/iam",
        "aud": "acom-test",
        **overrides,
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "test-kid"})


def test_decodes_iam_rs256_claims_without_network_calls(rsa_keys) -> None:
    claims = decode_iam_access_token(_token(rsa_keys))

    assert claims.account_id == ACCOUNT_ID
    assert claims.session_id == SESSION_ID
    assert claims.system_role == "economist"
    assert claims.role_id == settings.economist_role_id
    assert claims.permissions == frozenset({PermissionCodes.REQUESTS_READ})


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "another-service"},
        {"iss": "https://wrong.example/iam"},
        {"role": "unknown-role"},
        {"permissions": ["unknown.permission"]},
        {"sub": "not-a-uuid"},
        {"sid": "not-a-uuid"},
        {"exp": 1},
    ],
)
def test_rejects_invalid_or_expired_claims(rsa_keys, overrides) -> None:
    with pytest.raises(Unauthorized):
        decode_iam_access_token(_token(rsa_keys, **overrides))


def test_rejects_unknown_kid_and_symmetric_algorithm(rsa_keys, caplog) -> None:
    token_with_wrong_kid = jwt.encode(
        jwt.get_unverified_claims(_token(rsa_keys)),
        rsa_keys,
        algorithm="RS256",
        headers={"kid": "unknown"},
    )
    with pytest.raises(Unauthorized):
        decode_iam_access_token(token_with_wrong_kid)

    symmetric = jwt.encode(
        jwt.get_unverified_claims(_token(rsa_keys)),
        "x" * 64,
        algorithm="HS256",
        headers={"kid": "test-kid"},
    )
    with pytest.raises(Unauthorized):
        decode_iam_access_token(symmetric)
    assert '"event_type": "invalid_jwt_kid"' in caplog.text
    assert '"reason_code": "unknown_kid"' in caplog.text


def test_accepts_active_and_retiring_keys_during_overlap(rsa_keys, monkeypatch) -> None:
    old_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    old_private = old_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    old_public = old_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    monkeypatch.setattr(settings, "iam_signing_verification_keys", {"old-kid": old_public})
    old_token = jwt.encode(
        jwt.get_unverified_claims(_token(rsa_keys)),
        old_private,
        algorithm="RS256",
        headers={"kid": "old-kid"},
    )

    assert decode_iam_access_token(_token(rsa_keys)).account_id == ACCOUNT_ID
    assert decode_iam_access_token(old_token).account_id == ACCOUNT_ID

    monkeypatch.setattr(settings, "iam_signing_verification_keys", {})
    with pytest.raises(Unauthorized):
        decode_iam_access_token(old_token)


def test_rejects_conflicting_public_keys_for_same_kid(rsa_keys, monkeypatch) -> None:
    _ = rsa_keys
    conflicting_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    conflicting_public = conflicting_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    monkeypatch.setattr(
        settings,
        "iam_signing_verification_keys",
        {"test-kid": conflicting_public},
    )

    with pytest.raises(ValueError, match="conflicts"):
        settings._normalize()


def test_rejects_wildcard_cors_when_cookie_credentials_are_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "cors_allow_origins", ["*"])

    with pytest.raises(ValueError, match="CORS_ALLOW_ORIGINS"):
        settings._normalize()


def test_rejects_signature_from_wrong_rsa_private_key(rsa_keys) -> None:
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    wrong_private = wrong_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    token = jwt.encode(
        jwt.get_unverified_claims(_token(rsa_keys)),
        wrong_private,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    with pytest.raises(Unauthorized):
        decode_iam_access_token(token)


@pytest.mark.parametrize(
    "missing_claim",
    ["sub", "sid", "role", "permissions", "iat", "exp", "iss", "aud"],
)
def test_requires_all_registered_iam_claims(rsa_keys, missing_claim: str) -> None:
    payload = jwt.get_unverified_claims(_token(rsa_keys))
    payload.pop(missing_claim)
    token = jwt.encode(payload, rsa_keys, algorithm="RS256", headers={"kid": "test-kid"})

    with pytest.raises(Unauthorized):
        decode_iam_access_token(token)


@pytest.mark.asyncio
async def test_resolves_only_active_iam_binding(monkeypatch) -> None:
    observed: dict[str, str] = {}

    class AuthAccounts:
        async def get_by_provider_subject(self, *, provider: str, subject: str):
            observed.update(provider=provider, subject=subject)
            return SimpleNamespace(id_user="local-user")

    class Users:
        async def get_by_id(self, user_id: str):
            assert user_id == "local-user"
            return SimpleNamespace(id=user_id, status="active")

    class FakeUow:
        user_auth_accounts = AuthAccounts()
        users = Users()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    monkeypatch.setattr(dependencies, "UnitOfWork", FakeUow)
    claims = IamAccessClaims(
        account_id=ACCOUNT_ID,
        session_id=SESSION_ID,
        system_role="economist",
        role_id=settings.economist_role_id,
        permissions=frozenset({PermissionCodes.REQUESTS_READ}),
        issued_at=int(time.time()),
        expires_at=int(time.time()) + 300,
    )

    current_user = await dependencies.resolve_iam_current_user(claims)

    assert observed == {"provider": "iam", "subject": ACCOUNT_ID}
    assert current_user.user_id == "local-user"
    assert current_user.iam_account_id == ACCOUNT_ID
    assert current_user.permissions == claims.permissions


@pytest.mark.asyncio
async def test_keycloak_only_binding_cannot_resolve_iam_identity(monkeypatch) -> None:
    class AuthAccounts:
        async def get_by_provider_subject(self, *, provider: str, subject: str):
            assert provider == "iam"
            _ = subject
            return None

    class FakeUow:
        user_auth_accounts = AuthAccounts()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    monkeypatch.setattr(dependencies, "UnitOfWork", FakeUow)
    claims = IamAccessClaims(
        account_id=ACCOUNT_ID,
        session_id=SESSION_ID,
        system_role="economist",
        role_id=settings.economist_role_id,
        permissions=frozenset(),
        issued_at=int(time.time()),
        expires_at=int(time.time()) + 300,
    )
    with pytest.raises(Unauthorized):
        await dependencies.resolve_iam_current_user(claims)


def test_stable_account_id_is_retry_safe_and_opaque() -> None:
    first = stable_iam_account_id("same.login")
    second = stable_iam_account_id("same.login")
    assert first == second
    assert first.version == 4
    assert first != stable_iam_account_id("other.login")
    assert isinstance(first, uuid.UUID)

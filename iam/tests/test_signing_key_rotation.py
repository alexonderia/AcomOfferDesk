from __future__ import annotations

import time
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt

from iam_app.api import jwks
from iam_app.core.config import settings
from iam_app.core.security import encode_access_token


def _key_pair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return (
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("utf-8"),
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8"),
    )


def _claims(**overrides) -> dict:
    now = int(time.time())
    return {
        "sub": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
        "role": "economist",
        "permissions": ["requests.read"],
        "iat": now,
        "exp": now + 300,
        "iss": settings.issuer,
        "aud": settings.audience,
        **overrides,
    }


def _verify(token: str, key_ring: dict[str, str]) -> dict:
    header = jwt.get_unverified_header(token)
    if header.get("alg") != "RS256":
        raise JWTError("invalid algorithm")
    public_key = key_ring.get(str(header.get("kid") or ""))
    if public_key is None:
        raise JWTError("unknown kid")
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        issuer=settings.issuer,
        audience=settings.audience,
    )


@pytest.fixture
def rotation_keys(monkeypatch) -> dict[str, str]:
    old_private, old_public = _key_pair()
    new_private, new_public = _key_pair()
    monkeypatch.setattr(settings, "signing_private_key", new_private)
    monkeypatch.setattr(settings, "signing_public_key", new_public)
    monkeypatch.setattr(settings, "signing_kid", "new-key")
    monkeypatch.setattr(
        settings,
        "signing_verification_keys",
        {"old-key": old_public},
    )
    return {
        "old_private": old_private,
        "old_public": old_public,
        "new_private": new_private,
        "new_public": new_public,
    }


def test_new_access_token_uses_active_kid(rotation_keys) -> None:
    _ = rotation_keys
    token, _expires_at = encode_access_token(
        account_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        role="economist",
        permissions=["requests.read"],
    )
    assert jwt.get_unverified_header(token)["kid"] == "new-key"


@pytest.mark.asyncio
async def test_jwks_contains_active_key(rotation_keys) -> None:
    _ = rotation_keys
    result = await jwks()
    assert "new-key" in {key["kid"] for key in result["keys"]}


@pytest.mark.asyncio
async def test_overlap_jwks_contains_old_and_new_keys(rotation_keys) -> None:
    _ = rotation_keys
    result = await jwks()
    assert {key["kid"] for key in result["keys"]} == {"old-key", "new-key"}


def test_token_signed_by_retiring_key_remains_verifiable(rotation_keys) -> None:
    token = jwt.encode(
        _claims(),
        rotation_keys["old_private"],
        algorithm="RS256",
        headers={"kid": "old-key"},
    )
    assert _verify(token, settings.verification_public_keys)["role"] == "economist"


def test_token_signed_by_active_key_is_verifiable(rotation_keys) -> None:
    token = jwt.encode(
        _claims(),
        rotation_keys["new_private"],
        algorithm="RS256",
        headers={"kid": "new-key"},
    )
    assert _verify(token, settings.verification_public_keys)["role"] == "economist"


def test_unknown_kid_is_rejected(rotation_keys) -> None:
    token = jwt.encode(
        _claims(),
        rotation_keys["new_private"],
        algorithm="RS256",
        headers={"kid": "unknown-key"},
    )
    with pytest.raises(JWTError):
        _verify(token, settings.verification_public_keys)


def test_wrong_rsa_signature_is_rejected(rotation_keys) -> None:
    unrelated_private, _unrelated_public = _key_pair()
    token = jwt.encode(
        _claims(),
        unrelated_private,
        algorithm="RS256",
        headers={"kid": "new-key"},
    )
    with pytest.raises(JWTError):
        _verify(token, settings.verification_public_keys)


def test_wrong_issuer_is_rejected(rotation_keys) -> None:
    token = jwt.encode(
        _claims(iss="https://wrong.example/iam"),
        rotation_keys["new_private"],
        algorithm="RS256",
        headers={"kid": "new-key"},
    )
    with pytest.raises(JWTError):
        _verify(token, settings.verification_public_keys)


def test_wrong_audience_is_rejected(rotation_keys) -> None:
    token = jwt.encode(
        _claims(aud="wrong-audience"),
        rotation_keys["new_private"],
        algorithm="RS256",
        headers={"kid": "new-key"},
    )
    with pytest.raises(JWTError):
        _verify(token, settings.verification_public_keys)


def test_old_token_is_rejected_after_retiring_key_removal(rotation_keys) -> None:
    token = jwt.encode(
        _claims(),
        rotation_keys["old_private"],
        algorithm="RS256",
        headers={"kid": "old-key"},
    )
    with pytest.raises(JWTError):
        _verify(token, {"new-key": rotation_keys["new_public"]})

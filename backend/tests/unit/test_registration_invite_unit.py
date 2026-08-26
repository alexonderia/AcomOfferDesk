from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.core.registration_invite import RegistrationInviteTokenCodec
from app.domain.exceptions import Unauthorized
from app.services.registration_invitations import RegistrationInvitationService


def _token(*, ttl_seconds: int = 3600) -> str:
    return RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=ttl_seconds).issue(
        email="invitee@example.com", role_id=settings.contractor_role_id, inviter_id="admin-1", unit_id=12,
    )


def _tamper(token: str) -> str:
    payload, signature = token.split(".", 1)
    decoded = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    decoded["role_id"] = settings.admin_role_id
    replacement = base64.urlsafe_b64encode(json.dumps(decoded, separators=(",", ":")).encode()).rstrip(b"=").decode()
    return f"{replacement}.{signature}"


def test_signed_stateless_invite_valid_expired_and_tampered() -> None:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    claims = codec.parse(_token())
    assert claims.email == "invitee@example.com"
    assert claims.role_id == settings.contractor_role_id
    with pytest.raises(Unauthorized):
        codec.parse(_tamper(_token()))
    with pytest.raises(Unauthorized, match="истёк"):
        RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=-1).parse(_token(ttl_seconds=-1))


@pytest.mark.asyncio
async def test_reopening_stateless_link_and_existing_identity_states() -> None:
    token = _token()
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    service = RegistrationInvitationService(codec=codec)
    assert (await service.inspect(raw_token=token)).status == "ok"
    assert (await service.inspect(raw_token=token)).status == "ok"

from __future__ import annotations

import base64
import json
import logging
from types import SimpleNamespace

import pytest

from app.core.registration_invite import RegistrationInviteTokenCodec
from app.core.config import settings
from app.domain.exceptions import Unauthorized
from app.domain.permissions import PermissionCodes
from app.services.registration_invitations import RegistrationInvitationService


def _tamper_claim(token: str, **updates) -> str:
    payload_part, signature = token.split(".", maxsplit=1)
    padding = "=" * ((4 - len(payload_part) % 4) % 4)
    payload = json.loads(base64.urlsafe_b64decode(f"{payload_part}{padding}").decode("utf-8"))
    payload.update(updates)
    new_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).rstrip(b"=").decode("utf-8")
    return f"{new_payload}.{signature}"


def _issue(**overrides) -> str:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    kwargs = {
        "email": "invitee@example.com",
        "role_id": settings.contractor_role_id,
        "inviter_id": "admin-1",
        "unit_id": 12,
    }
    kwargs.update(overrides)
    return codec.issue(**kwargs)


def test_invite_token_roundtrip_preserves_signed_claims() -> None:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    token = codec.issue(
        email="Invitee@Example.com",
        role_id=settings.contractor_role_id,
        inviter_id="admin-1",
        unit_id=12,
    )
    claims = codec.parse(token)
    assert claims.purpose == "registration_invite"
    assert claims.email == "invitee@example.com"
    assert claims.role_id == settings.contractor_role_id
    assert claims.unit_id == 12
    assert claims.inviter_id == "admin-1"
    assert claims.nonce
    assert claims.exp > 0


@pytest.mark.parametrize(
    "updates",
    [
        {"email": "attacker@example.com"},
        {"role_id": 1},
        {"unit_id": 99},
    ],
)
def test_modified_invite_claims_break_signature(updates) -> None:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    token = _issue()
    with pytest.raises(Unauthorized):
        codec.parse(_tamper_claim(token, **updates))


def test_expired_invite_token_is_rejected() -> None:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=-10)
    token = codec.issue(
        email="invitee@example.com",
        role_id=settings.contractor_role_id,
        inviter_id="admin-1",
    )
    with pytest.raises(Unauthorized, match="истёк"):
        codec.parse(token)


def test_wrong_purpose_and_malformed_invite_tokens_are_rejected() -> None:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    token = _issue()
    with pytest.raises(Unauthorized):
        codec.parse(_tamper_claim(token, purpose="password_reset"))
    with pytest.raises(Unauthorized):
        codec.parse("not-a-valid-token")
    with pytest.raises(Unauthorized):
        codec.parse("abc.def")


@pytest.mark.asyncio
async def test_inspect_reports_already_registered_without_storing_token() -> None:
    class _Uow:
        def __init__(self) -> None:
            self.users = SimpleNamespace(get_by_id=self._get_user)
            self.profiles = SimpleNamespace(get_id_by_mail=self._id_by_mail, get_by_id=self._profile)
            self.company_contacts = SimpleNamespace(get_by_id=self._missing)
            self.user_contact_channels = SimpleNamespace(
                list_user_ids_by_primary_email=self._no_ids,
                get_primary_by_type=self._verified,
            )
            self.user_auth_accounts = SimpleNamespace(get_by_external_email=self._missing)
            self.writes = 0

        async def _id_by_mail(self, *, email: str) -> str:
            _ = email
            return "taken-1"

        async def _get_user(self, user_id: str):
            return SimpleNamespace(id=user_id, status="active")

        async def _profile(self, user_id: str):
            return SimpleNamespace(id=user_id, mail="taken@example.com", full_name="Taken", phone=None)

        async def _verified(self, **_kwargs):
            return SimpleNamespace(is_verified=True, channel_value="taken@example.com")

        async def _no_ids(self, *, email: str) -> list[str]:
            _ = email
            return []

        async def _missing(self, *args, **kwargs):
            _ = (args, kwargs)
            return None

    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    token = codec.issue(
        email="taken@example.com",
        role_id=settings.contractor_role_id,
        inviter_id="admin-1",
    )
    result = await RegistrationInvitationService(_Uow(), codec=codec).inspect(raw_token=token)
    assert result.status == "already_registered"
    assert result.email == "taken@example.com"


def test_create_invitation_does_not_log_raw_token(make_current_user, caplog) -> None:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    service = RegistrationInvitationService(codec=codec)
    current_user = make_current_user(
        user_id="admin-1",
        role_id=settings.admin_role_id,
        permissions={PermissionCodes.USERS_REGISTRATION_INVITE},
    )
    with caplog.at_level(logging.DEBUG):
        token = service.create_contractor_invitation(
            current_user=current_user,
            email="invitee@example.com",
            unit_id=4,
        )
    assert token
    assert token not in caplog.text


def test_issue_contractor_registration_token_does_not_require_invite_permission() -> None:
    codec = RegistrationInviteTokenCodec(secret="invite-test-secret", ttl_seconds=3600)
    service = RegistrationInvitationService(codec=codec)
    token = service.issue_contractor_registration_token(
        email=" invitee@example.com ",
        inviter_id="economist-1",
    )
    claims = codec.parse(token)
    assert claims.email == "invitee@example.com"
    assert claims.inviter_id == "economist-1"
    assert claims.role_id == settings.contractor_role_id
    assert "/register?token=" in service.registration_portal_url(token)


def test_registration_portal_url_uses_web_base_url(monkeypatch) -> None:
    monkeypatch.setattr(settings, "web_base_url", "https://web.acom.example/")
    token = "raw-token-value"
    assert (
        RegistrationInvitationService.registration_portal_url(token)
        == "https://web.acom.example/register?token=raw-token-value"
    )

from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings
from app.core.registration_invite import RegistrationInviteTokenCodec
from app.domain.permissions import PermissionCodes


class _ExplodingUow:
    async def __aenter__(self):
        raise AssertionError("MAIN UoW must not be used when minting a registration invite")

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def test_create_registration_invitation_does_not_touch_main_db(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
    monkeypatch,
):
    sent = []

    async def _fake_send(self, *args, **kwargs):
        sent.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr("app.api.v1.registration.SMTPEmailService.send_email", _fake_send)
    monkeypatch.setattr(settings, "web_base_url", "https://web.example")
    set_uow(_ExplodingUow())
    set_current_user(
        make_current_user(
            user_id="admin-1",
            role_id=settings.admin_role_id,
            permissions={PermissionCodes.USERS_REGISTRATION_INVITE},
        )
    )

    response = test_client.post(
        "/api/v1/registration/invitations",
        json={"email": "invitee@example.com", "unit_id": 4},
    )

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "invitee@example.com"
    assert sent
    body = " ".join(str(item) for item in sent)
    assert "/register?token=" in body


def test_inspect_registration_invitation_validates_signed_token(
    test_client,
    set_uow,
    monkeypatch,
):
    class _Uow:
        def __init__(self) -> None:
            self.users = SimpleNamespace(get_by_id=self._missing)
            self.profiles = SimpleNamespace(get_id_by_mail=self._missing, get_by_id=self._missing)
            self.company_contacts = SimpleNamespace(get_by_id=self._missing)
            self.user_contact_channels = SimpleNamespace(
                list_user_ids_by_primary_email=self._no_ids,
                get_primary_by_type=self._missing,
            )
            self.user_auth_accounts = SimpleNamespace(get_by_external_email=self._missing)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            _ = (exc_type, exc, tb)

        async def _missing(self, *args, **kwargs):
            _ = (args, kwargs)
            return None

        async def _no_ids(self, *, email: str) -> list[str]:
            _ = email
            return []

    set_uow(_Uow())
    token = RegistrationInviteTokenCodec(secret=settings.email_verification_secret, ttl_seconds=3600).issue(
        email="invitee@example.com",
        role_id=settings.contractor_role_id,
        inviter_id="admin-1",
        unit_id=4,
    )
    ok = test_client.get(f"/api/v1/registration/invitations/{token}")
    assert ok.status_code == 200
    assert ok.json()["data"]["status"] == "ok"
    assert ok.json()["data"]["email"] == "invitee@example.com"

    expired = RegistrationInviteTokenCodec(secret=settings.email_verification_secret, ttl_seconds=-10).issue(
        email="invitee@example.com",
        role_id=settings.contractor_role_id,
        inviter_id="admin-1",
    )
    expired_response = test_client.get(f"/api/v1/registration/invitations/{expired}")
    assert expired_response.status_code == 200
    assert expired_response.json()["data"]["status"] == "expired"

    invalid = test_client.get("/api/v1/registration/invitations/not-a-valid-registration-token-value")
    assert invalid.status_code == 200
    assert invalid.json()["data"]["status"] == "invalid"

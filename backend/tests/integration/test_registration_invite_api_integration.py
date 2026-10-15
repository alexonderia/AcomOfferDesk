from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings
from app.core.registration_invite import RegistrationInviteTokenCodec


def test_inspect_registration_invitation_validates_signed_token(test_client, set_uow):
    async def missing(*args, **kwargs): return None
    async def no_ids(**kwargs): return []
    class Uow:
        users = SimpleNamespace(get_by_id=missing)
        profiles = SimpleNamespace(get_id_by_mail=missing, get_by_id=missing)
        company_contacts = SimpleNamespace(get_by_id=missing)
        user_contact_channels = SimpleNamespace(list_user_ids_by_primary_email=no_ids, get_primary_by_type=missing)
        user_auth_accounts = SimpleNamespace(get_by_external_email=missing)
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None

    set_uow(Uow())
    token = RegistrationInviteTokenCodec(secret=settings.email_verification_secret).issue(
        email="invitee@example.com", role_id=settings.contractor_role_id, inviter_id="admin-1"
    )
    response = test_client.get(f"/api/v1/registration/invitations/{token}")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"

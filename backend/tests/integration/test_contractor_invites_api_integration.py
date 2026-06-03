from __future__ import annotations

from app.domain.permissions import PermissionCodes
from app.services.contractor_invitations import ContractorInviteResult, InviteFailure


def test_contractor_invite_endpoint_requires_permission(
    test_client,
    set_current_user,
    make_current_user,
):
    set_current_user(make_current_user(permissions=set()))

    response = test_client.post(
        "/api/v1/contractors/invite",
        json={"emails": ["valid@example.com"], "normative_file_id": 1},
    )

    assert response.status_code == 403


def test_contractor_invite_endpoint_returns_structured_result(
    test_client,
    set_current_user,
    make_current_user,
    monkeypatch,
):
    set_current_user(
        make_current_user(
            permissions={PermissionCodes.CONTRACTORS_MANUAL_CREATE},
        )
    )

    async def _fake_invite_contractors(self, *, current_user, emails, normative_file_id):
        _ = (self, current_user, emails, normative_file_id)
        return ContractorInviteResult(
            sent=["ok@example.com"],
            failed=[InviteFailure(email="failed@example.com", reason="send failed")],
            invalid=["bad-email"],
        )

    monkeypatch.setattr(
        "app.api.v1.contractors.ContractorInvitationService.invite_contractors",
        _fake_invite_contractors,
    )

    response = test_client.post(
        "/api/v1/contractors/invite",
        json={
            "emails": ["ok@example.com", "bad-email", "failed@example.com"],
            "normative_file_id": 7,
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["sent"] == ["ok@example.com"]
    assert payload["invalid"] == ["bad-email"]
    assert payload["failed"] == [{"email": "failed@example.com", "reason": "send failed"}]

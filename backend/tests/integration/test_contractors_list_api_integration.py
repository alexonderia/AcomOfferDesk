from __future__ import annotations

from app.domain.permissions import PermissionCodes
from app.services.contractors import ContractorListItemResult, ContractorListResult


def test_contractors_list_endpoint_requires_permission(
    test_client,
    set_current_user,
    make_current_user,
):
    set_current_user(make_current_user(permissions=set()))

    response = test_client.get("/api/v1/contractors")

    assert response.status_code == 403


def test_contractors_list_endpoint_returns_table_payload(
    test_client,
    set_current_user,
    make_current_user,
    monkeypatch,
):
    set_current_user(
        make_current_user(
            permissions={
                PermissionCodes.CONTRACTORS_READ,
                PermissionCodes.CONTRACTORS_PROFILE_READ,
                PermissionCodes.CONTRACTORS_MANUAL_MANAGE,
            },
        )
    )

    async def _fake_list_contractors(self, *, current_user, search=None, status=None, sort_by="created_at", sort_order="desc", limit=25, offset=0):
        _ = (self, current_user, search, status, sort_by, sort_order)
        return ContractorListResult(
            items=[
                ContractorListItemResult(
                    user_id="contractor-1",
                    role_id=6,
                    status="review",
                    full_name="Иван Петров",
                    phone="+79990000000",
                    mail="contractor@example.com",
                    company_name="ООО Ромашка",
                    inn="1234567890",
                    company_phone="+79990000001",
                    company_mail="office@example.com",
                    address="Москва",
                    note="Тест",
                    created_at="2026-06-01 10:00:00",
                    updated_at="2026-06-10 11:00:00",
                    is_manual=True,
                ),
            ],
            total=1,
            limit=limit,
            offset=offset,
        )

    monkeypatch.setattr(
        "app.api.v1.contractors.ContractorService.list_contractors",
        _fake_list_contractors,
    )

    response = test_client.get(
        "/api/v1/contractors",
        params={
            "search": "ромашка",
            "status": "review",
            "sort_by": "company_name",
            "sort_order": "asc",
            "limit": 10,
            "offset": 20,
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 1
    assert payload["limit"] == 10
    assert payload["offset"] == 20
    assert "max_user_id" not in payload["items"][0]
    assert "registration_source" not in payload["items"][0]
    assert payload["items"][0]["email_verified"] is False
    assert payload["items"][0]["actions"]["can_manage_manual_contractor"] is True

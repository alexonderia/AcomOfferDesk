from __future__ import annotations

from app.domain.permissions import PermissionCodes
from app.services.requests import EligibleRequestOwnerItem
from app.services.users import ManualContractorDuplicateItem


def test_eligible_request_owners_are_returned_for_the_specific_request(
    test_client,
    set_current_user,
    make_current_user,
    monkeypatch,
):
    set_current_user(
        make_current_user(
            permissions={PermissionCodes.REQUESTS_OWNER_CHANGE},
        )
    )

    async def _fake_list_eligible_request_owners(self, *, current_user, request_id):
        _ = (self, current_user)
        assert request_id == "request-42"
        return [
            EligibleRequestOwnerItem(
                user_id="economist-1",
                full_name="Иван Петров",
                role="economist",
                unavailable_period=None,
            ),
        ]

    monkeypatch.setattr(
        "app.api.v1.requests.RequestService.list_eligible_request_owners",
        _fake_list_eligible_request_owners,
    )

    response = test_client.get("/api/v1/requests/request-42/eligible-owners")

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "items": [
                {
                    "user_id": "economist-1",
                    "full_name": "Иван Петров",
                    "role": "economist",
                    "unavailable_period": None,
                },
            ],
        },
    }


def test_global_request_economists_endpoint_is_not_exposed(
    test_client,
    set_current_user,
    make_current_user,
):
    set_current_user(make_current_user(permissions={PermissionCodes.REQUESTS_OWNER_CHANGE}))

    response = test_client.get("/api/v1/users/request-economists")

    assert response.status_code == 404


def test_manual_contractor_duplicate_suggestions_return_safe_preview(
    test_client,
    set_current_user,
    make_current_user,
    monkeypatch,
):
    set_current_user(make_current_user(permissions={PermissionCodes.CONTRACTORS_MANUAL_CREATE}))

    async def _fake_list_possible_duplicates(self, *, current_user, company_name=None, inn=None, company_mail=None):
        _ = (self, current_user, company_name, inn, company_mail)
        return [
            ManualContractorDuplicateItem(
                user_id="contractor-1",
                full_name="ООО Ромашка",
                phone="+79990000000",
                mail="contact@example.com",
                company_name="ООО Ромашка",
                inn="1234567890",
                company_phone="+79990000001",
                company_mail="office@example.com",
                address="Москва",
                note="Тестовый контрагент",
                status="active",
                created_at="2026-08-01 10:00:00",
                updated_at="2026-08-02 11:00:00",
            ),
        ]

    monkeypatch.setattr(
        "app.api.v1.users.ManualContractorService.list_possible_duplicates",
        _fake_list_possible_duplicates,
    )

    response = test_client.get(
        "/api/v1/users/manual-contractor-duplicates",
        params={"company_name": "Ромаш"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["items"] == [
        {
            "user_id": "contractor-1",
            "full_name": "ООО Ромашка",
            "phone": "+79990000000",
            "mail": "contact@example.com",
            "company_name": "ООО Ромашка",
            "inn": "1234567890",
            "company_phone": "+79990000001",
            "company_mail": "office@example.com",
            "address": "Москва",
            "note": "Тестовый контрагент",
            "status": "active",
            "created_at": "2026-08-01 10:00:00",
            "updated_at": "2026-08-02 11:00:00",
        },
    ]

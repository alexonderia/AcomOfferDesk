from unittest.mock import AsyncMock

from app.api.v1 import offers as offers_api
from app.domain.permissions import PermissionCodes
from app.services.users import ManualContractorDuplicateItem


def test_request_duplicate_api_serializes_selection_state(test_client, monkeypatch, set_current_user, make_current_user):
    set_current_user(make_current_user(permissions={PermissionCodes.OFFERS_MANUAL_CREATE}))
    item = ManualContractorDuplicateItem(
        user_id="beton", full_name=None, phone=None, mail=None,
        company_name="ООО Бетон", inn="7707083893", company_phone=None,
        company_mail=None, address=None, note=None, status="active",
        created_at=None, updated_at=None, can_select=False,
        disabled_reason="Данный контрагент уже приложил КП к текущей заявке",
    )
    service = AsyncMock()
    service.list_manual_offer_contractor_duplicates.return_value = [item]
    monkeypatch.setattr(offers_api, "build_offer_service", lambda uow: service)

    response = test_client.get(
        "/api/v1/requests/request-1/offers/manual/contractor-duplicates",
        params={"company_name": "Бетон", "inn": "770708"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]["items"][0]
    assert payload["can_select"] is False
    assert payload["disabled_reason"] == item.disabled_reason
    assert payload["inn"] == "7707083893"
    arguments = service.list_manual_offer_contractor_duplicates.await_args.kwargs
    assert arguments["request_id"] == "request-1"
    assert arguments["company_name"] == "Бетон"
    assert arguments["inn"] == "770708"


def test_request_duplicate_api_limits_search_input(test_client, monkeypatch, set_current_user, make_current_user):
    set_current_user(make_current_user(permissions={PermissionCodes.OFFERS_MANUAL_CREATE}))
    service = AsyncMock()
    monkeypatch.setattr(offers_api, "build_offer_service", lambda uow: service)
    response = test_client.get(
        "/api/v1/requests/request-1/offers/manual/contractor-duplicates",
        params={"company_name": "а" * 257},
    )
    assert response.status_code == 422
    service.list_manual_offer_contractor_duplicates.assert_not_awaited()

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.exceptions import Conflict
from app.services.offers import OfferService


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["add", "remove", "amount"])
@pytest.mark.parametrize("status", ["closed", "cancelled"])
async def test_offer_mutation_observes_request_closed_while_waiting(operation, status, make_current_user):
    request = SimpleNamespace(id="request-1", status="open")
    offer = SimpleNamespace(id=1, id_request=request.id, status="submitted")
    requests = AsyncMock()
    requests.get_by_id.return_value = request
    offers = AsyncMock()
    offers.get_by_id.return_value = offer
    file_service = AsyncMock()
    service = OfferService(
        requests=requests, offers=offers, users=AsyncMock(), units=AsyncMock(),
        chats=AsyncMock(), files=AsyncMock(), messages=AsyncMock(),
        profiles=AsyncMock(), company_contacts=AsyncMock(), file_service=file_service,
    )

    async def close_request(**kwargs):
        request.status = status

    requests.lock_offer_lifecycle.side_effect = close_request
    actor = make_current_user()
    with pytest.raises(Conflict):
        if operation == "add":
            await service.add_file(current_user=actor, offer_id=offer.id, upload=SimpleNamespace())
        elif operation == "remove":
            await service.remove_file(current_user=actor, offer_id=offer.id, file_id=2)
        else:
            await service.update_amount(current_user=actor, offer_id=offer.id, offer_amount=10)
    file_service.create_offer_file.assert_not_awaited()
    file_service.delete_file.assert_not_awaited()
    offers.attach_file.assert_not_awaited()
    offers.detach_file.assert_not_awaited()
    offers.update_amount.assert_not_awaited()

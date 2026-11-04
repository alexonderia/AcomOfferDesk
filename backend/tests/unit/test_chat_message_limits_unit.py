from unittest.mock import AsyncMock
from types import SimpleNamespace

import pytest

from app.domain.exceptions import Conflict, Forbidden
from app.domain.permissions import PermissionCodes
from app.services.offers import OfferService


@pytest.mark.asyncio
@pytest.mark.parametrize("attachments", [None, [object()]])
async def test_oversized_message_cannot_reach_chat_or_file_storage(attachments):
    service = object.__new__(OfferService)
    service._require_chat_context = AsyncMock()

    with pytest.raises(Conflict, match="Максимум 3000"):
        await service.create_message(current_user=None, offer_id=1, text="x" * 3001, attachments=attachments)

    service._require_chat_context.assert_not_awaited()


@pytest.mark.asyncio
async def test_maximum_message_is_not_rejected_by_length_check():
    service = object.__new__(OfferService)
    service._require_chat_context = AsyncMock(side_effect=PermissionError("authorization reached"))

    with pytest.raises(PermissionError, match="authorization reached"):
        await service.create_message(current_user=None, offer_id=1, text="  " + "x" * 3000 + "  ")

    service._require_chat_context.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("role_id", [4, 5, 6])
@pytest.mark.parametrize("has_base_send", [True, False])
@pytest.mark.parametrize("same_department", [True, False])
async def test_explicit_send_delegation_respects_department_even_with_base_permission(
    make_current_user, role_id, has_base_send, same_department,
):
    permissions = {PermissionCodes.DEPARTMENT_CHATS_SEND_MESSAGE}
    if has_base_send:
        permissions.add(PermissionCodes.CHAT_MESSAGE_SEND)
    current_user = make_current_user(role_id=role_id, permissions=permissions)
    service = object.__new__(OfferService)
    service._is_user_inside_current_department_scope = AsyncMock(return_value=same_department)
    service._staff_scope = SimpleNamespace(can_send_chat_for_request=AsyncMock(return_value=False))
    if same_department:
        await service._ensure_can_send_chat_message(current_user=current_user, offer_owner_user_id="contractor", request_owner_user_id="peer")
    else:
        with pytest.raises(Forbidden):
            await service._ensure_can_send_chat_message(current_user=current_user, offer_owner_user_id="contractor", request_owner_user_id="foreign")


@pytest.mark.asyncio
async def test_base_economist_send_permission_does_not_allow_peer_chat(make_current_user):
    current_user = make_current_user(role_id=6, permissions={PermissionCodes.CHAT_MESSAGE_SEND})
    service = object.__new__(OfferService)
    with pytest.raises(Forbidden):
        await service._ensure_can_send_chat_message(current_user=current_user, offer_owner_user_id="contractor", request_owner_user_id="peer")

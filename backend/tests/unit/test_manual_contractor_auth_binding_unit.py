from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.users import ManualContractorCreateInput, ManualContractorService


class _IamClient:
    async def put_account(self, *, account_id, login: str, role: str, auth_status: str):
        return SimpleNamespace(id=str(account_id))


@pytest.mark.asyncio
async def test_manual_contractor_creation_is_local_only() -> None:
    users = AsyncMock()
    users.exists = AsyncMock(return_value=False)
    service = ManualContractorService(
        users=users,
        profiles=AsyncMock(),
        company_contacts=AsyncMock(),
        user_auth_accounts=AsyncMock(),
        iam_client=_IamClient(),
    )

    login = await service._create_manual_contractor(
        data=ManualContractorCreateInput(
            company_name='ООО "Тест"',
            inn="7707083893",
            company_phone="+79991234567",
        )
    )

    assert login
    users.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_contractor_creation_creates_iam_binding() -> None:
    auth_accounts = AsyncMock()
    users = AsyncMock()
    users.exists = AsyncMock(return_value=False)
    service = ManualContractorService(
        users=users,
        profiles=AsyncMock(),
        company_contacts=AsyncMock(),
        user_auth_accounts=auth_accounts,
        iam_client=_IamClient(),
    )

    await service._create_manual_contractor(
        data=ManualContractorCreateInput(
            company_name='ООО "Локальный"',
            inn="2365485695",
            company_phone="+79999999999",
            company_mail="local@example.com",
        )
    )

    auth_accounts.add.assert_awaited_once()
    binding = auth_accounts.add.await_args.args[0]
    assert binding.provider == "iam"
    assert binding.id_user
    assert binding.external_subject_id

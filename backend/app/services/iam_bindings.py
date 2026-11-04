from app.domain.exceptions import Conflict, NotFound
from app.domain.iam_identity import stable_iam_account_id
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount


async def recover_existing_iam_binding(uow, *, user_id: str):
    """Repair a verified existing identity; never provision accounts or passwords."""
    binding = await uow.user_auth_accounts.get_by_user_provider(
        user_id=user_id, provider="iam", include_inactive=True,
    )
    subject = binding.external_subject_id if binding is not None else stable_iam_account_id(user_id)
    try:
        account = await IamClient().get_credential_state(account_id=subject)
    except NotFound:
        raise Conflict("Учётная запись IAM не найдена. Требуется восстановление привязки администратором") from None
    if account.login != user_id:
        raise Conflict("Привязка IAM не соответствует логину пользователя")
    conflict = await uow.user_auth_accounts.get_conflicting_subject(
        provider="iam", subject=str(account.id), exclude_user_id=user_id,
    )
    if conflict is not None:
        raise Conflict("Учётная запись IAM уже связана с другим пользователем")
    if binding is None:
        binding = UserAuthAccount(
            id_user=user_id, provider="iam", external_subject_id=str(account.id),
            external_username=account.login, is_active=True,
        )
        await uow.user_auth_accounts.add(binding)
    else:
        binding.is_active = True
    return binding

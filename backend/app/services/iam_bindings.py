from app.domain.exceptions import Conflict, NotFound
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.domain.iam_status import iam_auth_status_for_user_status
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount


async def ensure_user_iam_account(
    *, user_auth_accounts, user_id: str, role_id: int, user_status: str,
    email: str | None = None, initial_password: str | None = None,
    is_new_user: bool = False, iam_client: IamClient | None = None,
):
    """Synchronize identity only; existing passwords and account status are preserved."""
    role = technical_role_name(role_id)
    if role is None:
        raise Conflict("Роль недоступна для синхронизации с IAM")
    binding = await user_auth_accounts.get_by_user_provider(
        user_id=user_id, provider="iam", include_inactive=True,
    )
    subject = str(binding.external_subject_id if binding is not None else stable_iam_account_id(user_id))
    conflict = await user_auth_accounts.get_conflicting_subject(
        provider="iam", subject=subject, exclude_user_id=user_id,
    )
    if conflict is not None:
        raise Conflict("Учётная запись IAM уже связана с другим пользователем")
    client = iam_client or IamClient()
    if initial_password is not None:
        if not is_new_user:
            if binding is None or not binding.is_active or user_status != "active":
                raise Conflict("Создание не изменяет доступ существующего пользователя")
            state = await client.get_credential_state(account_id=subject)
            if state.login != user_id or state.role != role or not state.password_set:
                raise Conflict("Доступ существующего пользователя настраивается отдельно администратором")
        account = await client.provision_direct_credentials(
            account_id=subject, login=user_id, role=role, password=initial_password,
        )
    else:
        account = await client.put_account(
            account_id=subject, login=user_id, role=role,
            auth_status=("blocked" if binding is not None and not binding.is_active
                         else iam_auth_status_for_user_status(user_status)),
        )
    if str(account.id) != subject or account.login != user_id or account.role != role:
        raise Conflict("Учётная запись IAM не соответствует пользователю")
    if binding is None:
        binding = UserAuthAccount(
            id_user=user_id, provider="iam", external_subject_id=subject,
            external_username=user_id, external_email=email, is_active=True,
        )
        await user_auth_accounts.add(binding)
    # An inactive existing binding must not be reactivated by account creation.
    return binding


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

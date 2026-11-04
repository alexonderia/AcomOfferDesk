from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient


async def reset_user_password(uow, *, current_user: CurrentUser, user_id: str, new_password: str) -> None:
    if current_user.role_id != settings.superadmin_role_id or current_user.status != "active":
        raise Forbidden("Сброс пароля доступен только суперадминистратору")
    target = await uow.users.get_by_id(user_id)
    if target is None:
        raise NotFound("Пользователь не найден")
    if target.role_id == settings.superadmin_role_id or target.id == current_user.user_id:
        raise Forbidden("Сброс пароля суперадминистратора запрещён")
    binding = await uow.user_auth_accounts.get_by_user_provider(
        user_id=user_id, provider="iam", include_inactive=True,
    )
    if binding is None or not binding.is_active:
        raise Conflict("У пользователя нет активной учётной записи для входа")
    client = IamClient()
    state = await client.get_credential_state(account_id=binding.external_subject_id)
    if state.login != user_id or state.role != technical_role_name(target.role_id):
        raise Conflict("Привязка учётной записи не соответствует пользователю")
    await client.reset_user_password(
        account_id=binding.external_subject_id, new_password=new_password,
        actor_account_id=current_user.iam_account_id, actor_session_id=current_user.iam_session_id,
    )

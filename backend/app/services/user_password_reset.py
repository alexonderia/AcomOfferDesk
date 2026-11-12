from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.domain.policies import UserPolicy
from app.services.department_scope import DepartmentScopeService


async def resolve_password_reset_scope(users, *, current_user: CurrentUser) -> set[str] | None:
    """None is global superadmin scope; an empty set grants no targets."""
    if not UserPolicy.can_reset_passwords(current_user):
        return set()
    if current_user.role_id == settings.superadmin_role_id:
        return None
    return set(await DepartmentScopeService(users).resolve_department_owner_ids_for_current_user(
        current_user=current_user,
    ))


async def reset_user_password(uow, *, current_user: CurrentUser, user_id: str, new_password: str) -> None:
    if not UserPolicy.can_reset_passwords(current_user):
        raise Forbidden("Недостаточно прав для сброса пароля пользователя")
    target = await uow.users.get_by_id(user_id)
    if target is None:
        raise NotFound("Пользователь не найден")
    scope = await resolve_password_reset_scope(uow.users, current_user=current_user)
    if not UserPolicy.can_reset_user_password(
        current_user, target_user_id=target.id, target_role_id=target.id_role,
        is_in_department=scope is None or target.id in scope,
    ):
        raise Forbidden("Сброс пароля этого пользователя недоступен")
    binding = await uow.user_auth_accounts.get_by_user_provider(
        user_id=user_id, provider="iam", include_inactive=True,
    )
    if binding is None or not binding.is_active:
        raise Conflict("У пользователя нет активной учётной записи для входа")
    client = IamClient()
    state = await client.get_credential_state(account_id=binding.external_subject_id)
    if state.login != user_id or state.role != technical_role_name(target.id_role):
        raise Conflict("Привязка учётной записи не соответствует пользователю")
    await client.reset_user_password(
        account_id=binding.external_subject_id, new_password=new_password,
        actor_account_id=current_user.iam_account_id, actor_session_id=current_user.iam_session_id,
        **({"department_scope_verified": True} if current_user.role_id == settings.admin_role_id else {}),
    )

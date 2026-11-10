from dataclasses import dataclass

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Forbidden, NotFound
from app.domain.policies import UserPolicy
from app.repositories.users import UserRepository
from app.services.unit_hierarchy import UnitHierarchyService


@dataclass(frozen=True, slots=True)
class UserProfileView:
    user_id: str
    role_id: int
    status: str
    full_name: str | None
    phone: str | None
    mail: str | None


async def get_user_profile_view(
    *, users: UserRepository, current_user: CurrentUser, user_id: str,
) -> UserProfileView:
    UserPolicy.ensure_can_list_users(current_user)
    hierarchy = UnitHierarchyService(users)
    if not await hierarchy.can_view_user(current_user=current_user, target_user_id=user_id):
        raise Forbidden("Недостаточно прав для просмотра профиля сотрудника")
    row = await users.get_with_profile_and_company_contacts(user_id=user_id)
    if row is None:
        raise NotFound("Сотрудник не найден")
    user, profile, _company = row
    if user.id_role == settings.contractor_role_id:
        raise Forbidden("Профиль контрагента доступен в разделе контрагентов")
    return UserProfileView(
        user_id=user.id,
        role_id=user.id_role,
        status=user.status,
        full_name=profile.full_name if profile else None,
        phone=profile.phone if profile else None,
        mail=profile.mail if profile else None,
    )

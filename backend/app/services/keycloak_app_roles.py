from __future__ import annotations

from app.core.config import settings
from app.domain.exceptions import Conflict
from app.services.keycloak_admin import KeycloakAdminService


def role_mapping_by_local_role_id() -> dict[int, str]:
    return {
        settings.superadmin_role_id: "app.superadmin",
        settings.admin_role_id: "app.admin",
        settings.project_manager_role_id: "app.project_manager",
        settings.lead_economist_role_id: "app.lead_economist",
        settings.economist_role_id: "app.economist",
        settings.operator_role_id: "app.operator",
        settings.contractor_role_id: "app.contractor",
    }


async def sync_keycloak_app_role_for_user(
    keycloak_admin: KeycloakAdminService,
    *,
    keycloak_user_id: str,
    local_role_id: int,
) -> None:
    """Assign app.* client role in Keycloak to match users.id_role (IAM permissions source)."""
    if not settings.keycloak_enabled:
        return

    normalized_subject = (keycloak_user_id or "").strip()
    if not normalized_subject:
        raise Conflict("Не удалось синхронизировать роль: отсутствует идентификатор Keycloak")

    role_mapping = role_mapping_by_local_role_id()
    admin_token = await keycloak_admin.get_admin_token()
    api_client_uuid = await keycloak_admin.get_client_uuid_by_client_id(
        client_id=settings.keycloak_api_client_id,
        admin_token=admin_token,
    )
    synced, _removed = await keycloak_admin.sync_user_app_role_for_local_role(
        keycloak_user_id=normalized_subject,
        api_client_uuid=api_client_uuid,
        local_role_id=local_role_id,
        role_mapping=role_mapping,
        admin_token=admin_token,
    )
    if not synced:
        raise Conflict("Не удалось синхронизировать роль пользователя в Keycloak")

from __future__ import annotations

from dataclasses import dataclass

from app.domain.permissions import PermissionCodes

CONTRACTOR_STATUS_DELEGATION_ROLE = "delegation.contractors.profile.status.update"


CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS: dict[str, frozenset[str]] = {
    CONTRACTOR_STATUS_DELEGATION_ROLE: frozenset(
        {
            PermissionCodes.CONTRACTORS_READ,
            PermissionCodes.CONTRACTORS_PROFILE_READ,
            PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE,
        }
    ),
}


@dataclass(frozen=True, slots=True)
class ContractorDelegationDefinition:
    role_code: str
    permission_codes: frozenset[str]
    label: str
    description: str


CONTRACTOR_DELEGATIONS: tuple[ContractorDelegationDefinition, ...] = (
    ContractorDelegationDefinition(
        role_code=CONTRACTOR_STATUS_DELEGATION_ROLE,
        permission_codes=CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS[CONTRACTOR_STATUS_DELEGATION_ROLE],
        label="Управление статусом контрагентов",
        description="Позволяет открыть раздел контрагентов, просматривать данные контрагентов и менять статус их профиля.",
    ),
)


def get_contractor_delegation_role_codes() -> frozenset[str]:
    return frozenset(CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS.keys())


def get_contractor_delegation_permission_codes() -> frozenset[str]:
    return frozenset(
        permission
        for permissions in CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS.values()
        for permission in permissions
    )


def user_has_contractor_status_delegation(delegation_roles: frozenset[str]) -> bool:
    return CONTRACTOR_STATUS_DELEGATION_ROLE in delegation_roles

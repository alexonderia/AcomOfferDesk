from __future__ import annotations

from dataclasses import dataclass

from app.domain.permissions import PermissionCodes


CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS: dict[str, frozenset[str]] = {
    "delegation.contractors.profile.status.update": frozenset(
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
        role_code="delegation.contractors.profile.status.update",
        permission_codes=CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS["delegation.contractors.profile.status.update"],
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

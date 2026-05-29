from app.domain.contractor_delegations import (
    CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS,
    CONTRACTOR_DELEGATIONS,
    get_contractor_delegation_permission_codes,
    get_contractor_delegation_role_codes,
)
from app.domain.permissions import PermissionCodes


def test_contractor_delegation_role_maps_all_required_permissions():
    permissions = CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS["delegation.contractors.profile.status.update"]
    assert PermissionCodes.CONTRACTORS_READ in permissions
    assert PermissionCodes.CONTRACTORS_PROFILE_READ in permissions
    assert PermissionCodes.CONTRACTORS_PROFILE_STATUS_UPDATE in permissions


def test_contractor_delegations_definition_matches_role_mapping():
    assert len(CONTRACTOR_DELEGATIONS) == 1
    definition = CONTRACTOR_DELEGATIONS[0]
    assert definition.role_code == "delegation.contractors.profile.status.update"
    assert definition.permission_codes == CONTRACTOR_DELEGATION_ROLE_TO_PERMISSIONS[definition.role_code]


def test_contractor_delegation_codes_are_atomic_permissions_only():
    permission_codes = get_contractor_delegation_permission_codes()
    assert all("." in code and not code.startswith("delegation.") for code in permission_codes)
    assert get_contractor_delegation_role_codes() == frozenset({"delegation.contractors.profile.status.update"})

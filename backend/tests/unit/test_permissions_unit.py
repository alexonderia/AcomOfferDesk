from app.domain.permissions import PermissionCodes, get_known_permissions


def test_get_known_permissions_contains_atomic_codes_only():
    known_permissions = get_known_permissions()

    assert PermissionCodes.USERS_READ in known_permissions
    assert PermissionCodes.REQUESTS_READ in known_permissions
    assert PermissionCodes.OFFERS_CREATE in known_permissions
    assert "app.superadmin" not in known_permissions
    assert "delegation.request-reader" not in known_permissions


def test_get_known_permissions_is_not_empty():
    assert len(get_known_permissions()) > 0

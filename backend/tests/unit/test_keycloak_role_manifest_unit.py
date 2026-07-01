"""Unit tests for Keycloak bootstrap app-role manifest."""

from __future__ import annotations

from app.scripts.keycloak_role_manifest import load_app_role_members


def test_keycloak_bootstrap_app_roles_include_contractor_read_permissions() -> None:
    manifest = load_app_role_members()

    for app_role in ('app.project_manager', 'app.lead_economist', 'app.economist'):
        members = manifest[app_role]
        assert 'contractors.read' in members
        assert 'contractors.profile.read' in members
        assert 'contractors.profile.status.update' not in members


def test_keycloak_bootstrap_admin_app_role_does_not_gain_contractor_read_permissions() -> None:
    manifest = load_app_role_members()

    members = manifest['app.admin']
    assert 'contractors.read' not in members
    assert 'contractors.profile.read' not in members
    assert 'units.read' in members
    assert 'units.create' in members
    assert 'units.update' in members
    assert 'units.members.manage' in members


def test_keycloak_bootstrap_project_manager_app_role_gets_read_only_units_access() -> None:
    manifest = load_app_role_members()

    members = manifest["app.project_manager"]
    assert "units.read" in members
    assert "units.create" not in members
    assert "units.update" not in members
    assert "units.members.manage" not in members


def test_keycloak_bootstrap_security_officer_app_role_contains_only_expected_permissions() -> None:
    manifest = load_app_role_members()

    assert manifest["app.security_officer"] == frozenset(
        {
            "profile.manage_own",
            "feedback.create",
            "units.read",
            "contractors.read",
            "contractors.profile.read",
            "contractors.profile.status.update",
        }
    )

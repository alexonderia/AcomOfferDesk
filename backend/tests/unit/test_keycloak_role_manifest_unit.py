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

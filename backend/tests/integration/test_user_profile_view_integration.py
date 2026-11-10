from types import SimpleNamespace

import pytest


class _Users:
    def __init__(self):
        self.rows = {}
        for user_id, role_id in [("sa", 1), ("admin", 2), ("pm", 4), ("lead", 5), ("econ", 6), ("sibling", 6), ("outside", 6), ("unassigned", 6), ("contractor", 3)]:
            self.rows[user_id] = (
                SimpleNamespace(id=user_id, id_role=role_id, status="active"),
                SimpleNamespace(full_name=f"Сотрудник {user_id}", phone="+79991234567", mail=f"{user_id}@example.test"),
                None,
            )

    async def get_with_profile_and_company_contacts(self, *, user_id):
        return self.rows.get(user_id)

    async def list_active_units(self):
        return [(10, None), (11, 10), (12, 11), (13, 10), (20, None)]

    async def list_active_unit_memberships(self):
        return [("admin", 10), ("pm", 10), ("lead", 11), ("econ", 12), ("sibling", 13), ("outside", 20)]

    async def list_by_ids_with_profiles_and_roles(self, *, user_ids):
        return [(self.rows[key][0], self.rows[key][1], SimpleNamespace(role="Сотрудник")) for key in user_ids]


class _Uow:
    def __init__(self):
        self.users = _Users()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


@pytest.mark.parametrize("actor,role,target", [
    ("sa", 1, "unassigned"),
    ("sa", 1, "pm"),
    ("admin", 2, "pm"),
    ("pm", 4, "econ"),
    ("lead", 5, "econ"),
    ("econ", 6, "pm"),  # A visible ancestor is readable without management rights.
    ("econ", 6, "econ"),
])
def test_profile_view_allows_visible_staff_and_returns_only_profile_fields(
    test_client, set_current_user, make_current_user, set_uow, actor, role, target,
):
    set_uow(_Uow())
    set_current_user(make_current_user(user_id=actor, role_id=role, permissions={"users.read"}))
    response = test_client.get(f"/api/v1/users/{target}/details")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    data = response.json()["data"]
    assert set(data) == {"user_id", "role_id", "status", "full_name", "phone", "mail"}
    assert data["user_id"] == target
    assert data["phone"] == "+79991234567"


@pytest.mark.parametrize("actor,role,target,permissions", [
    ("admin", 2, "outside", {"users.read"}),
    ("admin", 2, "unassigned", {"users.read"}),
    ("admin", 2, "sa", {"users.read"}),
    ("lead", 5, "sibling", {"users.read"}),
    ("econ", 6, "outside", {"users.read"}),
    ("pm", 4, "econ", {"units.read"}),
    ("sa", 1, "contractor", {"users.read"}),
])
def test_profile_view_rejects_outside_scope_or_missing_read_permission(
    test_client, set_current_user, make_current_user, set_uow, actor, role, target, permissions,
):
    set_uow(_Uow())
    set_current_user(make_current_user(user_id=actor, role_id=role, permissions=permissions))
    response = test_client.get(f"/api/v1/users/{target}/details")
    assert response.status_code == 403
    assert "phone" not in response.json()


def test_profile_view_missing_user_is_404_for_superadmin(test_client, set_current_user, make_current_user, set_uow):
    set_uow(_Uow())
    set_current_user(make_current_user(user_id="sa", role_id=1, permissions={"users.read"}))
    assert test_client.get("/api/v1/users/missing/details").status_code == 404

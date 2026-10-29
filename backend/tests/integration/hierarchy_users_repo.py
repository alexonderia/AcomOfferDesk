"""Shared hierarchy fixtures for integration tests of staff access scope."""

from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings


class HierarchyUsersRepo:
    """PM -> two LE modules -> economists (eco-1/eco-2 under lead-1, eco-3 under lead-2)."""

    def __init__(self) -> None:
        self._units = [
            (1, None),
            (2, 1),
            (3, 1),
        ]
        self._unit_details = [
            (1, "Department A", None),
            (2, "Lead 1 Module", 1),
            (3, "Lead 2 Module", 1),
        ]
        self._memberships = [
            ("pm-1", 1),
            ("lead-1", 2),
            ("eco-1", 2),
            ("eco-2", 2),
            ("lead-2", 3),
            ("eco-3", 3),
        ]
        self._users = {
            "pm-1": SimpleNamespace(
                id="pm-1",
                id_role=settings.project_manager_role_id,
                id_parent=None,
            ),
            "lead-1": SimpleNamespace(
                id="lead-1",
                id_role=settings.lead_economist_role_id,
                id_parent="pm-1",
            ),
            "lead-2": SimpleNamespace(
                id="lead-2",
                id_role=settings.lead_economist_role_id,
                id_parent="pm-1",
            ),
            "eco-1": SimpleNamespace(
                id="eco-1",
                id_role=settings.economist_role_id,
                id_parent="lead-1",
            ),
            "eco-2": SimpleNamespace(
                id="eco-2",
                id_role=settings.economist_role_id,
                id_parent="lead-1",
            ),
            "eco-3": SimpleNamespace(
                id="eco-3",
                id_role=settings.economist_role_id,
                id_parent="lead-2",
            ),
            "operator-1": SimpleNamespace(
                id="operator-1",
                id_role=settings.operator_role_id,
                id_parent=None,
            ),
        }

    async def get_by_id(self, user_id: str):
        return self._users.get(user_id)

    async def list_active_user_parent_pairs(self):
        return [
            ("lead-1", "pm-1"),
            ("lead-2", "pm-1"),
            ("eco-1", "lead-1"),
            ("eco-2", "lead-1"),
            ("eco-3", "lead-2"),
        ]

    async def list_active_units(self):
        return list(self._units)

    async def list_active_unit_details(self):
        return list(self._unit_details)

    async def list_active_unit_memberships(self):
        return list(self._memberships)

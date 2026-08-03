from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings
from app.domain.auth_context import CurrentUser
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.domain.policies import UserPolicy
from app.models.orm_models import Unit, UnitMember
from app.repositories.units import UnitRepository
from app.repositories.users import UserRepository


def _utcnow_naive() -> datetime:
    return datetime.utcnow()


@dataclass(frozen=True, slots=True)
class ContractorRootUnitBindingState:
    unit_id: int
    unit_name: str
    is_bound: bool
    can_manage: bool


@dataclass(frozen=True, slots=True)
class ContractorRootUnitBindingsState:
    contractor_user_id: str
    can_manage: bool
    items: list[ContractorRootUnitBindingState]


class ContractorUnitService:
    def __init__(
        self,
        *,
        users: UserRepository,
        units: UnitRepository | None = None,
    ) -> None:
        self._users = users
        self._units = units
        self._root_unit_ids_by_user: dict[str, set[int]] | None = None

    def _require_units(self) -> UnitRepository:
        if self._units is None:
            raise RuntimeError("Contractor unit operation requires unit repository")
        return self._units

    async def _list_active_root_units(self) -> list[Unit]:
        return [
            unit
            for unit in await self._require_units().list_units(active_only=True)
            if unit.id_parent is None
        ]

    async def _load_root_memberships(self) -> dict[str, set[int]]:
        if self._root_unit_ids_by_user is not None:
            return self._root_unit_ids_by_user

        active_units = await self._users.list_active_units()
        parent_by_unit_id = {unit_id: parent_unit_id for unit_id, parent_unit_id in active_units}
        root_by_unit_id: dict[int, int] = {}

        def _resolve_root_unit_id(unit_id: int) -> int | None:
            cached = root_by_unit_id.get(unit_id)
            if cached is not None:
                return cached
            current_unit_id = unit_id
            visited: set[int] = set()
            while current_unit_id in parent_by_unit_id:
                if current_unit_id in visited:
                    raise Conflict("Обнаружен цикл в иерархии подразделений")
                visited.add(current_unit_id)
                parent_unit_id = parent_by_unit_id[current_unit_id]
                if parent_unit_id is None:
                    root_by_unit_id[unit_id] = current_unit_id
                    return current_unit_id
                current_unit_id = parent_unit_id
            return None

        root_unit_ids_by_user: dict[str, set[int]] = defaultdict(set)
        for user_id, unit_id in await self._users.list_active_unit_memberships():
            root_unit_id = _resolve_root_unit_id(unit_id)
            if root_unit_id is None:
                continue
            root_unit_ids_by_user[user_id].add(root_unit_id)

        self._root_unit_ids_by_user = dict(root_unit_ids_by_user)
        return self._root_unit_ids_by_user

    async def list_effective_root_unit_ids_for_user(self, *, user_id: str) -> set[int]:
        memberships = await self._load_root_memberships()
        return set(memberships.get(user_id, set()))

    async def list_direct_root_unit_ids_for_user(self, *, user_id: str) -> set[int]:
        return set(await self._require_units().list_user_root_unit_ids(user_id=user_id))

    def can_manage_bindings(self, current_user: CurrentUser) -> bool:
        return UserPolicy.can_manage_contractor_unit_bindings(current_user)

    async def list_manageable_root_unit_ids(self, *, current_user: CurrentUser) -> set[int]:
        if current_user.role_id == settings.superadmin_role_id:
            return {
                int(unit.id)
                for unit in await self._list_active_root_units()
            }
        if not self.can_manage_bindings(current_user):
            return set()
        return await self.list_direct_root_unit_ids_for_user(user_id=current_user.user_id)

    async def can_contractor_access_request_owner(
        self,
        *,
        contractor_user_id: str,
        request_owner_user_id: str,
    ) -> bool:
        contractor_root_ids = await self.list_effective_root_unit_ids_for_user(user_id=contractor_user_id)
        if not contractor_root_ids:
            return False
        owner_root_ids = await self.list_effective_root_unit_ids_for_user(user_id=request_owner_user_id)
        if not owner_root_ids:
            return False
        return bool(contractor_root_ids & owner_root_ids)

    async def filter_contractor_user_ids_for_request_owner(
        self,
        *,
        contractor_user_ids: list[str],
        request_owner_user_id: str,
    ) -> list[str]:
        owner_root_ids = await self.list_effective_root_unit_ids_for_user(user_id=request_owner_user_id)
        if not owner_root_ids:
            return []
        memberships = await self._load_root_memberships()
        return [
            contractor_user_id
            for contractor_user_id in contractor_user_ids
            if memberships.get(contractor_user_id, set()) & owner_root_ids
        ]

    async def filter_rows_by_request_owner_scope(
        self,
        *,
        contractor_user_id: str,
        rows: list[object],
        owner_user_id_getter,
    ) -> list[object]:
        contractor_root_ids = await self.list_effective_root_unit_ids_for_user(user_id=contractor_user_id)
        if not contractor_root_ids:
            return []
        memberships = await self._load_root_memberships()
        return [
            row
            for row in rows
            if memberships.get(owner_user_id_getter(row), set()) & contractor_root_ids
        ]

    async def _ensure_contractor_exists(self, *, contractor_user_id: str):
        contractor = await self._users.get_by_id(contractor_user_id)
        if contractor is None:
            raise NotFound("Контрагент не найден")
        if contractor.id_role != settings.contractor_role_id:
            raise Conflict("Пользователь не является контрагентом")
        return contractor

    async def list_bindings(
        self,
        *,
        current_user: CurrentUser,
        contractor_user_id: str,
    ) -> ContractorRootUnitBindingsState:
        if not (
            UserPolicy.can_read_contractor_profile(current_user)
            or self.can_manage_bindings(current_user)
        ):
            raise Forbidden("Недостаточно прав для просмотра привязок контрагента к подразделениям")
        await self._ensure_contractor_exists(contractor_user_id=contractor_user_id)

        direct_root_ids = await self.list_direct_root_unit_ids_for_user(user_id=contractor_user_id)
        manageable_root_ids = await self.list_manageable_root_unit_ids(current_user=current_user)
        can_manage = self.can_manage_bindings(current_user)
        items = [
            ContractorRootUnitBindingState(
                unit_id=int(unit.id),
                unit_name=unit.name,
                is_bound=int(unit.id) in direct_root_ids,
                can_manage=can_manage and int(unit.id) in manageable_root_ids,
            )
            for unit in await self._list_active_root_units()
        ]
        return ContractorRootUnitBindingsState(
            contractor_user_id=contractor_user_id,
            can_manage=can_manage and bool(manageable_root_ids),
            items=items,
        )

    async def list_bindings_for_users(
        self,
        *,
        current_user: CurrentUser,
        contractor_user_ids: list[str],
    ) -> dict[str, ContractorRootUnitBindingsState]:
        """Batch variant of ``list_bindings`` for list endpoints.

        Reuses a single cached membership load so the contractor list endpoint
        stays at O(1) queries regardless of page size, avoiding a per-row fetch.
        """
        if not (
            UserPolicy.can_read_contractor_profile(current_user)
            or self.can_manage_bindings(current_user)
        ):
            return {}
        if not contractor_user_ids:
            return {}

        active_root_units = await self._list_active_root_units()
        manageable_root_ids = await self.list_manageable_root_unit_ids(current_user=current_user)
        can_manage = self.can_manage_bindings(current_user)
        memberships = await self._load_root_memberships()

        result: dict[str, ContractorRootUnitBindingsState] = {}
        for contractor_user_id in contractor_user_ids:
            bound_root_ids = memberships.get(contractor_user_id, set())
            items = [
                ContractorRootUnitBindingState(
                    unit_id=int(unit.id),
                    unit_name=unit.name,
                    is_bound=int(unit.id) in bound_root_ids,
                    can_manage=can_manage and int(unit.id) in manageable_root_ids,
                )
                for unit in active_root_units
            ]
            result[contractor_user_id] = ContractorRootUnitBindingsState(
                contractor_user_id=contractor_user_id,
                can_manage=can_manage and bool(manageable_root_ids),
                items=items,
            )
        return result

    async def bind_user_to_root_units(
        self,
        *,
        user_id: str,
        root_unit_ids: set[int],
        assigned_by_user_id: str,
    ) -> None:
        if not root_unit_ids:
            return

        active_root_units = {
            int(unit.id): unit
            for unit in await self._list_active_root_units()
        }
        for root_unit_id in sorted(root_unit_ids):
            root_unit = active_root_units.get(root_unit_id)
            if root_unit is None:
                raise NotFound("Корневое подразделение не найдено")
            membership = await self._require_units().get_member(unit_id=root_unit_id, user_id=user_id)
            if membership is None:
                await self._require_units().add_member(
                    UnitMember(
                        id_unit=root_unit_id,
                        id_user=user_id,
                        id_assigned_by_user=assigned_by_user_id,
                        is_active=True,
                    )
                )
                continue
            if membership.is_active:
                continue
            membership.is_active = True
            membership.id_assigned_by_user = assigned_by_user_id
            membership.updated_at = _utcnow_naive()

        self._root_unit_ids_by_user = None

    async def update_bindings(
        self,
        *,
        current_user: CurrentUser,
        contractor_user_id: str,
        root_unit_ids: set[int],
    ) -> ContractorRootUnitBindingsState:
        if not self.can_manage_bindings(current_user):
            raise Forbidden("Недостаточно прав для изменения привязок контрагента к подразделениям")

        await self._ensure_contractor_exists(contractor_user_id=contractor_user_id)
        manageable_root_ids = await self.list_manageable_root_unit_ids(current_user=current_user)
        if not manageable_root_ids:
            raise Forbidden("Недостаточно прав для изменения привязок контрагента к подразделениям")

        unknown_root_ids = root_unit_ids - manageable_root_ids
        if unknown_root_ids:
            raise Forbidden("Недостаточно прав для выбора одного или нескольких подразделений")

        current_direct_root_ids = await self.list_direct_root_unit_ids_for_user(user_id=contractor_user_id)
        for root_unit_id in sorted(manageable_root_ids - root_unit_ids):
            membership = await self._require_units().get_member(unit_id=root_unit_id, user_id=contractor_user_id)
            if membership is None or not membership.is_active:
                continue
            membership.is_active = False
            membership.updated_at = _utcnow_naive()

        await self.bind_user_to_root_units(
            user_id=contractor_user_id,
            root_unit_ids=root_unit_ids - current_direct_root_ids,
            assigned_by_user_id=current_user.user_id,
        )

        self._root_unit_ids_by_user = None
        return await self.list_bindings(
            current_user=current_user,
            contractor_user_id=contractor_user_id,
        )

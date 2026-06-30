from __future__ import annotations

from sqlalchemy import func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm_models import Profile, Role, Unit, UnitMember, User


class UnitRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, unit: Unit) -> None:
        self._session.add(unit)

    async def add_member(self, member: UnitMember) -> None:
        self._session.add(member)

    async def flush(self) -> None:
        await self._session.flush()

    async def get_by_id(self, unit_id: int) -> Unit | None:
        result = await self._session.execute(select(Unit).where(Unit.id == unit_id))
        return result.scalar_one_or_none()

    async def get_member(self, *, unit_id: int, user_id: str) -> UnitMember | None:
        result = await self._session.execute(
            select(UnitMember).where(
                UnitMember.id_unit == unit_id,
                UnitMember.id_user == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_sibling_by_name(self, *, id_parent: int | None, name: str) -> Unit | None:
        stmt = select(Unit).where(Unit.name == name)
        if id_parent is None:
            stmt = stmt.where(Unit.id_parent.is_(None))
        else:
            stmt = stmt.where(Unit.id_parent == id_parent)
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none()

    async def list_units(self, *, active_only: bool = True) -> list[Unit]:
        stmt = select(Unit).order_by(Unit.id_parent.asc().nullsfirst(), Unit.name.asc(), Unit.id.asc())
        if active_only:
            stmt = stmt.where(Unit.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_children(self, *, unit_id: int, active_only: bool = True) -> list[Unit]:
        stmt = (
            select(Unit)
            .where(Unit.id_parent == unit_id)
            .order_by(Unit.name.asc(), Unit.id.asc())
        )
        if active_only:
            stmt = stmt.where(Unit.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_members(
        self,
        *,
        unit_id: int,
        active_only: bool = True,
    ) -> list[tuple[UnitMember, User, Profile | None, Role]]:
        stmt = (
            select(UnitMember, User, Profile, Role)
            .join(User, User.id == UnitMember.id_user)
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(UnitMember.id_unit == unit_id)
            .order_by(Role.id.asc(), Profile.full_name.asc().nullslast(), User.id.asc())
        )
        if active_only:
            stmt = stmt.where(UnitMember.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_members_for_units(
        self,
        *,
        unit_ids: list[int],
        active_only: bool = True,
    ) -> list[tuple[UnitMember, User, Profile | None, Role]]:
        if not unit_ids:
            return []
        stmt = (
            select(UnitMember, User, Profile, Role)
            .join(User, User.id == UnitMember.id_user)
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(UnitMember.id_unit.in_(unit_ids))
            .order_by(UnitMember.id_unit.asc(), Role.id.asc(), Profile.full_name.asc().nullslast(), User.id.asc())
        )
        if active_only:
            stmt = stmt.where(UnitMember.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_user_units(
        self,
        *,
        user_id: str,
        active_only: bool = True,
    ) -> list[tuple[UnitMember, Unit]]:
        stmt = (
            select(UnitMember, Unit)
            .join(Unit, Unit.id == UnitMember.id_unit)
            .where(UnitMember.id_user == user_id)
            .order_by(Unit.name.asc(), Unit.id.asc())
        )
        if active_only:
            stmt = stmt.where(UnitMember.is_active.is_(True), Unit.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.all())

    async def get_primary_department_name_for_user(self, *, user_id: str) -> str | None:
        memberships = await self.list_user_units(user_id=user_id, active_only=True)
        if not memberships:
            return None

        units = await self.list_units(active_only=True)
        by_id = {unit.id: unit for unit in units}

        _, start_unit = memberships[0]
        current = by_id.get(start_unit.id, start_unit)
        seen: set[int] = set()
        while (
            current.id_parent is not None
            and current.id_parent in by_id
            and current.id not in seen
        ):
            seen.add(current.id)
            current = by_id[current.id_parent]
        return current.name

    async def list_user_root_unit_ids(self, *, user_id: str) -> list[int]:
        stmt = (
            select(Unit.id)
            .join(UnitMember, UnitMember.id_unit == Unit.id)
            .where(
                Unit.id_parent.is_(None),
                Unit.is_active.is_(True),
                UnitMember.id_user == user_id,
                UnitMember.is_active.is_(True),
            )
            .order_by(Unit.id.asc())
        )
        result = await self._session.execute(stmt)
        return [int(value) for value in result.scalars().all()]

    async def list_available_users_for_unit(
        self,
        *,
        unit_id: int | None = None,
        search: str | None = None,
    ) -> list[tuple[User, Profile | None, Role]]:
        stmt = (
            select(User, Profile, Role)
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.status == "active")
            .order_by(Role.id.asc(), Profile.full_name.asc().nullslast(), User.id.asc())
        )
        if unit_id is not None:
            active_member_subquery = (
                select(UnitMember.id_user)
                .where(
                    UnitMember.id_unit == unit_id,
                    UnitMember.is_active.is_(True),
                )
            )
            stmt = stmt.where(not_(User.id.in_(active_member_subquery)))
        normalized_search = (search or "").strip().lower()
        if normalized_search:
            like_value = f"%{normalized_search}%"
            stmt = stmt.where(
                (func.lower(User.id).like(like_value))
                | (func.lower(func.coalesce(Profile.full_name, "")).like(like_value))
                | (func.lower(func.coalesce(Profile.mail, "")).like(like_value))
            )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_unassigned_users(
        self,
        *,
        contractor_role_id: int,
        search: str | None = None,
    ) -> list[tuple[User, Profile | None, Role]]:
        active_member_subquery = (
            select(UnitMember.id_user)
            .where(UnitMember.is_active.is_(True))
        )
        stmt = (
            select(User, Profile, Role)
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.status == "active")
            .where(User.id_role != contractor_role_id)
            .where(not_(User.id.in_(active_member_subquery)))
            .order_by(Role.id.asc(), Profile.full_name.asc().nullslast(), User.id.asc())
        )
        normalized_search = (search or "").strip().lower()
        if normalized_search:
            like_value = f"%{normalized_search}%"
            stmt = stmt.where(
                (func.lower(User.id).like(like_value))
                | (func.lower(func.coalesce(Profile.full_name, "")).like(like_value))
                | (func.lower(func.coalesce(Profile.mail, "")).like(like_value))
            )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_available_contractors_for_unit(
        self,
        *,
        unit_id: int,
        contractor_role_id: int,
        search: str | None = None,
    ) -> list[tuple[User, Profile | None, Role]]:
        active_member_subquery = (
            select(UnitMember.id_user)
            .where(
                UnitMember.id_unit == unit_id,
                UnitMember.is_active.is_(True),
            )
        )
        stmt = (
            select(User, Profile, Role)
            .join(Role, Role.id == User.id_role)
            .outerjoin(Profile, Profile.id == User.id)
            .where(User.id_role == contractor_role_id)
            .where(not_(User.id.in_(active_member_subquery)))
            .order_by(Profile.full_name.asc().nullslast(), User.id.asc())
        )
        normalized_search = (search or "").strip().lower()
        if normalized_search:
            like_value = f"%{normalized_search}%"
            stmt = stmt.where(
                (func.lower(User.id).like(like_value))
                | (func.lower(func.coalesce(Profile.full_name, "")).like(like_value))
                | (func.lower(func.coalesce(Profile.mail, "")).like(like_value))
            )
        result = await self._session.execute(stmt)
        return list(result.all())

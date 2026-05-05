from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import Select, bindparam, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.orm_models import (
    Chat,
    CompanyContact,
    File,
    Message,
    MessageReceipt,
    Offer,
    OfferFile,
    Profile,
    Request,
    RequestFile,
    RequestHiddenContractor,
    RequestOfferStats,
    User,
)

@dataclass(frozen=True)
class PlanRequestStatsRow:
    total_requests: int
    distributed_requests: int
    unallocated_requests: int
    request_fact_amount: Decimal
    unallocated_amount: Decimal


class RequestRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, request: Request) -> None:
        self._session.add(request)

    async def create(
        self,
        *,
        id_user: str,
        deadline_at: datetime,
        description: str | None,
        initial_amount: float | None = None,
        id_plan: int | None = None,
    ) -> Request:
        request = Request(
            id_user=id_user,
            deadline_at=deadline_at,
            description=description,
            initial_amount=initial_amount,
            id_plan=id_plan,
        )
        self._session.add(request)
        await self._session.flush()
        return request

    async def get_by_id(self, *, request_id: int) -> Request | None:
        stmt = select(Request).where(Request.id == request_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def economy_plan_exists(self, *, plan_id: int) -> bool:
        stmt = text("SELECT 1 FROM economy_plans WHERE id = :plan_id LIMIT 1")
        result = await self._session.execute(stmt, {"plan_id": plan_id})
        return result.scalar_one_or_none() is not None

    async def get_economy_plan_owner_user_id(self, *, plan_id: int) -> str | None:
        stmt = text("SELECT id_user FROM economy_plans WHERE id = :plan_id LIMIT 1")
        result = await self._session.execute(stmt, {"plan_id": plan_id})
        return result.scalar_one_or_none()
    
    async def list_files_by_request_id(self, *, request_id: int) -> list[File]:
        stmt = (
            select(File)
            .options(joinedload(File.storage_object))
            .join(RequestFile, RequestFile.id == File.id)
            .where(RequestFile.id_request == request_id)
            .order_by(File.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_latest_accepted_offer_id(self, *, request_id: int) -> int | None:
        stmt = (
            select(Offer.id)
            .where(Offer.id_request == request_id, Offer.status == "accepted")
            .order_by(Offer.created_at.desc(), Offer.id.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        *,
        request: Request,
        status: str,
        closed_at: datetime | None = None,
        chosen_offer_id: int | None = None,
    ) -> None:
        request.status = status
        request.closed_at = closed_at
        request.id_offer = chosen_offer_id

    async def update_deadline(self, *, request: Request, deadline_at: datetime) -> None:
        request.deadline_at = deadline_at

    async def update_owner(self, *, request: Request, user_id: str) -> None:
        request.id_user = user_id

    async def update_initial_amount(self, *, request: Request, initial_amount: float) -> None:
        request.initial_amount = initial_amount

    async def update_final_amount(self, *, request: Request, final_amount: float) -> None:
        request.final_amount = final_amount

    async def update_plan(self, *, request: Request, plan_id: int | None) -> None:
        request.id_plan = plan_id

    async def attach_file(self, *, request_id: int, file_id: int) -> None:
        self._session.add(RequestFile(id=file_id, id_request=request_id))

    async def hide_from_contractors(self, *, request_id: int, contractor_user_ids: list[str]) -> None:
        if not contractor_user_ids:
            return
        self._session.add_all(
            [
                RequestHiddenContractor(
                    request_id=request_id,
                    contractor_user_id=contractor_user_id,
                )
                for contractor_user_id in contractor_user_ids
            ]
        )

    async def detach_file(self, *, request_id: int, file_id: int) -> bool:
        stmt = delete(RequestFile).where(RequestFile.id_request == request_id, RequestFile.id == file_id)
        result = await self._session.execute(stmt)
        return bool(result.rowcount)
    
    async def get_open_by_id(self, *, request_id: int) -> Request | None:
        stmt = select(Request).where(Request.id == request_id, Request.status == "open")
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_visible_by_id_for_contractor(self, *, request_id: int, contractor_user_id: str) -> Request | None:
        stmt = (
            select(Request)
            .outerjoin(
                RequestHiddenContractor,
                (RequestHiddenContractor.request_id == Request.id)
                & (RequestHiddenContractor.contractor_user_id == contractor_user_id),
            )
            .where(Request.id == request_id, RequestHiddenContractor.request_id.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_visible_open_by_id_for_contractor(self, *, request_id: int, contractor_user_id: str) -> Request | None:
        stmt = (
            select(Request)
            .outerjoin(
                RequestHiddenContractor,
                (RequestHiddenContractor.request_id == Request.id)
                & (RequestHiddenContractor.contractor_user_id == contractor_user_id),
            )
            .where(
                Request.id == request_id,
                Request.status == "open",
                RequestHiddenContractor.request_id.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_hidden_contractor_ids(self, *, request_id: int) -> list[str]:
        stmt = (
            select(RequestHiddenContractor.contractor_user_id)
            .where(RequestHiddenContractor.request_id == request_id)
            .order_by(RequestHiddenContractor.contractor_user_id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def is_hidden_for_contractor(self, *, request_id: int, contractor_user_id: str) -> bool:
        stmt = (
            select(RequestHiddenContractor.request_id)
            .where(
                RequestHiddenContractor.request_id == request_id,
                RequestHiddenContractor.contractor_user_id == contractor_user_id,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_file_linked_to_open_request(self, *, file_id: int) -> bool:
        stmt = (
            select(RequestFile.id)
            .join(Request, Request.id == RequestFile.id_request)
            .where(RequestFile.id == file_id, Request.status == "open")
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_file_linked_to_visible_open_request(
        self,
        *,
        contractor_user_id: str,
        file_id: int,
    ) -> bool:
        stmt = (
            select(RequestFile.id)
            .join(Request, Request.id == RequestFile.id_request)
            .outerjoin(
                RequestHiddenContractor,
                (RequestHiddenContractor.request_id == Request.id)
                & (RequestHiddenContractor.contractor_user_id == contractor_user_id),
            )
            .where(
                RequestFile.id == file_id,
                Request.status == "open",
                RequestHiddenContractor.request_id.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_open(self) -> list[Request]:
        stmt = select(Request).where(Request.status == "open").order_by(Request.created_at.desc(), Request.id.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_open_for_contractor(self, *, contractor_user_id: str) -> list[Request]:
        stmt = (
            select(Request)
            .outerjoin(
                RequestHiddenContractor,
                (RequestHiddenContractor.request_id == Request.id)
                & (RequestHiddenContractor.contractor_user_id == contractor_user_id),
            )
            .where(Request.status == "open", RequestHiddenContractor.request_id.is_(None))
            .order_by(Request.created_at.desc(), Request.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def list_with_stats_and_files(
        self,
        *,
        current_user_id: str,
        owner_user_ids: list[str] | None = None,
    ) -> list[tuple[Request, RequestOfferStats | None, Profile | None, int]]:
        unread_messages_count = (
            select(func.count())
            .select_from(Message)
            .join(Chat, Chat.id == Message.id_chat)
            .join(Offer, Offer.id == Chat.id)
            .outerjoin(
                MessageReceipt,
                (MessageReceipt.id_message == Message.id)
                & (MessageReceipt.id_user == current_user_id),
            )
            .where(
                Offer.id_request == Request.id,
                Message.id_user != current_user_id,
                MessageReceipt.read_at.is_(None),
            )
            .correlate(Request)
            .scalar_subquery()
        )

        stmt = (
            select(Request, RequestOfferStats, Profile, unread_messages_count)
            .outerjoin(RequestOfferStats, RequestOfferStats.request_id == Request.id)
            .outerjoin(Profile, Profile.id == Request.id_user)
            .order_by(Request.created_at.desc(), Request.id.desc())
        )
        if owner_user_ids is not None:
            if not owner_user_ids:
                return []
            stmt = stmt.where(Request.id_user.in_(owner_user_ids))
        result = await self._session.execute(stmt)
        return list(result.all())
    
    async def list_open_with_files_for_contractor(
        self,
        *,
        contractor_user_id: str,
    ) -> list[tuple[Request, Profile | None]]:
        stmt = (
            select(Request, Profile)
            .outerjoin(Profile, Profile.id == Request.id_user)
            .outerjoin(
                RequestHiddenContractor,
                (RequestHiddenContractor.request_id == Request.id)
                & (RequestHiddenContractor.contractor_user_id == contractor_user_id),
            )
            .where(Request.status == "open", RequestHiddenContractor.request_id.is_(None))
            .order_by(Request.created_at.desc(), Request.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_with_offers_for_contractor(
        self, *, contractor_user_id: str
    ) -> list[tuple[Request, Offer, Profile | None, int]]:
        unread_messages_count = (
            select(func.count())
            .select_from(Message)
            .join(Chat, Chat.id == Message.id_chat)
            .outerjoin(
                MessageReceipt,
                (MessageReceipt.id_message == Message.id)
                & (MessageReceipt.id_user == contractor_user_id),
            )
            .where(
                Chat.id == Offer.id,
                Message.id_user != contractor_user_id,
                MessageReceipt.read_at.is_(None),
            )
            .correlate(Offer)
            .scalar_subquery()
        )
        stmt = (
            select(Request, Offer, Profile, unread_messages_count)
            .join(Offer, Offer.id_request == Request.id)
            .join(User, User.id == Offer.id_user)
            .outerjoin(Profile, Profile.id == Request.id_user)
            .outerjoin(
                RequestHiddenContractor,
                (RequestHiddenContractor.request_id == Request.id)
                & (RequestHiddenContractor.contractor_user_id == contractor_user_id),
            )
            .where(
                Offer.id_user == contractor_user_id,
                User.status == "active",
                RequestHiddenContractor.request_id.is_(None),
            )
            .order_by(Request.created_at.desc(), Request.id.desc(), Offer.created_at.desc(), Offer.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())
    
    async def list_open_with_stats_and_files(self) -> list[tuple[Request, RequestOfferStats | None, Profile | None]]:
        stmt = (
            select(Request, RequestOfferStats, Profile)
            .outerjoin(RequestOfferStats, RequestOfferStats.request_id == Request.id)
            .outerjoin(Profile, Profile.id == Request.id_user)
            .where(Request.status == "open")
            .order_by(Request.created_at.desc(), Request.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def list_open_with_stats_and_files_by_owner_ids(
        self,
        *,
        owner_ids: list[str],
    ) -> list[tuple[Request, RequestOfferStats | None, Profile | None]]:
        if not owner_ids:
            return []

        stmt = (
            select(Request, RequestOfferStats, Profile)
            .outerjoin(RequestOfferStats, RequestOfferStats.request_id == Request.id)
            .outerjoin(Profile, Profile.id == Request.id_user)
            .where(Request.status == "open", Request.id_user.in_(owner_ids))
            .order_by(Request.created_at.desc(), Request.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())
    
    async def count_in_progress_requests_by_owner(
        self,
        *,
        owner_ids: list[str],
    ) -> list[tuple[str, str, int]]:
        if not owner_ids:
            return []

        stmt = (
            select(Request.id_user, Request.status, func.count(Request.id))
            .where(Request.id_user.in_(owner_ids), Request.status.in_(["open", "review"]))
            .group_by(Request.id_user, Request.status)
            .order_by(Request.id_user.asc(), Request.status.asc())
        )
        result = await self._session.execute(stmt)
        return [
            (owner_id, status, count)
            for owner_id, status, count in result.all()
        ]

    async def list_unassigned_requests(
        self,
        *,
        operator_role_id: int,
        owner_ids: list[str] | None = None,
    ) -> list[Request]:
        stmt = (
            select(Request)
            .join(User, User.id == Request.id_user)
            .where(User.id_role == operator_role_id, Request.status.in_(["open", "review"]))
            .order_by(Request.created_at.desc(), Request.id.desc())
        )
        if owner_ids is not None:
            if not owner_ids:
                return []
            stmt = stmt.where(Request.id_user.in_(owner_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def list_in_progress_requests_by_owner_ids(
        self,
        *,
        owner_ids: list[str],
    ) -> list[Request]:
        if not owner_ids:
            return []

        stmt = (
            select(Request)
            .where(Request.id_user.in_(owner_ids), Request.status.in_(["open", "review"]))
            .order_by(Request.created_at.desc(), Request.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_closed_requests_with_chosen_offer_by_owner_ids(
        self,
        *,
        owner_ids: list[str],
    ) -> list[tuple[Request, Offer | None, Profile | None]]:
        if not owner_ids:
            return []

        stmt = (
            select(Request, Offer, Profile)
            .outerjoin(Offer, Offer.id == Request.id_offer)
            .outerjoin(Profile, Profile.id == Request.id_user)
            .where(Request.id_user.in_(owner_ids), Request.status == "closed")
            .order_by(Request.closed_at.desc(), Request.id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def aggregate_closed_economy_fact_by_owner_ids(
        self,
        *,
        owner_ids: list[str],
        period_start: date,
        period_end: date,
    ) -> dict[str, Decimal]:
        if not owner_ids:
            return {}

        start_dt = datetime.combine(period_start, time.min)
        end_dt = datetime.combine(period_end + timedelta(days=1), time.min)

        from_view = await self._aggregate_closed_economy_fact_from_view_by_owner_ids(
            owner_ids=owner_ids,
            start_dt=start_dt,
            end_dt=end_dt,
        )
        if from_view is not None:
            return from_view

        return await self._aggregate_closed_economy_fact_from_requests_by_owner_ids(
            owner_ids=owner_ids,
            start_dt=start_dt,
            end_dt=end_dt,
        )

    async def _aggregate_closed_economy_fact_from_view_by_owner_ids(
        self,
        *,
        owner_ids: list[str],
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict[str, Decimal] | None:
        columns_stmt = text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'v_request_economy'
            """
        )
        columns_result = await self._session.execute(columns_stmt)
        columns = {row[0] for row in columns_result.all()}
        if not columns:
            return None

        owner_candidates = ["id_user", "owner_user_id", "user_id", "responsible_user_id"]
        request_candidates = ["id_request", "request_id", "id"]
        amount_candidates = ["economy_amount", "savings_amount", "fact_amount", "amount", "economy_sum"]

        owner_column = next((item for item in owner_candidates if item in columns), None)
        request_column = next((item for item in request_candidates if item in columns), None)
        amount_column = next((item for item in amount_candidates if item in columns), None)
        if owner_column is None or request_column is None or amount_column is None:
            return None

        owner_ident = self._quote_identifier(owner_column)
        request_ident = self._quote_identifier(request_column)
        amount_ident = self._quote_identifier(amount_column)

        stmt = (
            text(
                f"""
                SELECT
                  COALESCE(v.{owner_ident}, r.id_user) AS owner_user_id,
                  COALESCE(SUM(v.{amount_ident}), 0) AS fact_amount
                FROM requests r
                LEFT JOIN v_request_economy v
                  ON v.{request_ident} = r.id
                WHERE r.status = 'closed'
                  AND r.closed_at >= :start_dt
                  AND r.closed_at < :end_dt
                  AND r.id_user IN :owner_ids
                GROUP BY COALESCE(v.{owner_ident}, r.id_user)
                """
            )
            .bindparams(bindparam("owner_ids", expanding=True))
        )

        try:
            result = await self._session.execute(
                stmt,
                {
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "owner_ids": owner_ids,
                },
            )
        except Exception:
            return None

        aggregated: dict[str, Decimal] = {}
        for owner_user_id, fact_amount in result.all():
            aggregated[owner_user_id] = Decimal(str(fact_amount or 0))
        return aggregated

    async def _aggregate_closed_economy_fact_from_requests_by_owner_ids(
        self,
        *,
        owner_ids: list[str],
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict[str, Decimal]:
        savings_amount = func.coalesce(Request.initial_amount - Request.final_amount, 0)
        stmt = (
            select(
                Request.id_user,
                func.coalesce(func.sum(savings_amount), 0),
            )
            .where(
                Request.status == "closed",
                Request.id_user.in_(owner_ids),
                Request.closed_at.is_not(None),
                Request.closed_at >= start_dt,
                Request.closed_at < end_dt,
            )
            .group_by(Request.id_user)
        )
        result = await self._session.execute(stmt)
        return {
            owner_user_id: Decimal(str(fact_amount or 0))
            for owner_user_id, fact_amount in result.all()
        }

    async def aggregate_plan_request_stats(
        self,
        *,
        owner_ids: list[str],
        plan_ids: list[int],
        period_start: date,
        period_end: date,
    ) -> PlanRequestStatsRow:
        if not owner_ids:
            return PlanRequestStatsRow(
                total_requests=0,
                distributed_requests=0,
                unallocated_requests=0,
                request_fact_amount=Decimal("0.00"),
                unallocated_amount=Decimal("0.00"),
            )

        start_dt = datetime.combine(period_start, time.min)
        end_dt = datetime.combine(period_end + timedelta(days=1), time.min)
        if not plan_ids:
            plan_ids = [-1]

        stmt = (
            text(
                """
                SELECT
                  COUNT(*) AS total_requests,
                  COUNT(*) FILTER (WHERE r.id_plan IN :plan_ids) AS distributed_requests,
                  COUNT(*) FILTER (WHERE r.id_plan IS NULL OR r.id_plan NOT IN :plan_ids) AS unallocated_requests,
                  COALESCE(SUM(
                    CASE WHEN r.id_plan IN :plan_ids
                      THEN COALESCE(r.initial_amount, 0) - COALESCE(r.final_amount, 0)
                      ELSE 0
                    END
                  ), 0) AS request_fact_amount,
                  COALESCE(SUM(
                    CASE WHEN r.id_plan IS NULL OR r.id_plan NOT IN :plan_ids
                      THEN COALESCE(r.initial_amount, 0) - COALESCE(r.final_amount, 0)
                      ELSE 0
                    END
                  ), 0) AS unallocated_amount
                FROM requests r
                WHERE r.status = 'closed'
                  AND r.id_user IN :owner_ids
                  AND r.closed_at IS NOT NULL
                  AND r.closed_at >= :start_dt
                  AND r.closed_at < :end_dt
                """
            )
            .bindparams(
                bindparam("owner_ids", expanding=True),
                bindparam("plan_ids", expanding=True),
            )
        )
        result = await self._session.execute(
            stmt,
            {
                "owner_ids": owner_ids,
                "plan_ids": plan_ids,
                "start_dt": start_dt,
                "end_dt": end_dt,
            },
        )
        row = result.one()
        return PlanRequestStatsRow(
            total_requests=int(row.total_requests or 0),
            distributed_requests=int(row.distributed_requests or 0),
            unallocated_requests=int(row.unallocated_requests or 0),
            request_fact_amount=Decimal(str(row.request_fact_amount or 0)).quantize(Decimal("0.01")),
            unallocated_amount=Decimal(str(row.unallocated_amount or 0)).quantize(Decimal("0.01")),
        )

    def _quote_identifier(self, value: str) -> str:
        escaped = value.replace('"', '""')
        return f'"{escaped}"'

    async def decrement_deleted_alert(self, *, request_id: int) -> RequestOfferStats | None:
        stmt = select(RequestOfferStats).where(RequestOfferStats.request_id == request_id)
        result = await self._session.execute(stmt)
        stats = result.scalar_one_or_none()
        if stats is None:
            return None

        if stats.count_deleted_alert > 0:
            stats.count_deleted_alert -= 1
        stats.updated_at = datetime.utcnow()
        await self._session.flush()
        return stats

    async def get_with_stats(self, *, request_id: int) -> tuple[Request, RequestOfferStats | None, Profile | None] | None:
        stmt = (
            select(Request, RequestOfferStats, Profile)
            .outerjoin(RequestOfferStats, RequestOfferStats.request_id == Request.id)
            .outerjoin(Profile, Profile.id == Request.id_user)
            .where(Request.id == request_id)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        return row

    async def list_files(self, *, request_id: int) -> list[File]:
        stmt: Select[tuple[File]] = (
            select(File)
            .options(joinedload(File.storage_object))
            .join(RequestFile, RequestFile.id == File.id)
            .where(RequestFile.id_request == request_id)
            .order_by(File.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_offers_with_files_and_contacts(
        self,
        *,
        request_id: int,
    current_user_id: str,
    ) -> list[tuple[Offer, File | None, Profile | None, CompanyContact | None, int]]:
        unread_messages_count = (
            select(func.count())
            .select_from(Message)
            .join(Chat, Chat.id == Message.id_chat)
            .outerjoin(
                MessageReceipt,
                (MessageReceipt.id_message == Message.id)
                & (MessageReceipt.id_user == current_user_id),
            )
            .where(
                Chat.id == Offer.id,
                Message.id_user != current_user_id,
                MessageReceipt.read_at.is_(None),
            )
            .correlate(Offer)
            .scalar_subquery()
        )

        stmt: Select[tuple[Offer, File | None, Profile | None, CompanyContact | None, int]] = (
            select(Offer, File, Profile, CompanyContact, unread_messages_count)
            .options(joinedload(File.storage_object))
            .outerjoin(OfferFile, OfferFile.id_offer == Offer.id)
            .outerjoin(File, File.id == OfferFile.id)
            .outerjoin(Profile, Profile.id == Offer.id_user)
            .outerjoin(CompanyContact, CompanyContact.id == Offer.id_user)
            .where(Offer.id_request == request_id)
            .order_by(Offer.created_at.desc(), Offer.id.desc(), File.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.all())

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Awaitable, Callable

from app.core.config import settings
from app.domain.contractor_validation import validate_inn, validate_optional_email, validate_ru_phone
from app.domain.authorization import has_permission, require_permission
from app.domain.exceptions import Conflict, Forbidden, NotFound
from app.domain.permissions import PermissionCodes
from app.domain.policies import CurrentUser, OfferPolicy, RequestPolicy, UserPolicy
from app.models.orm_models import CompanyContact, Profile, User
from app.repositories.chats import ChatRepository, ChatState
from app.repositories.company_contacts import CompanyContactRepository
from app.repositories.files import FileRepository
from app.repositories.messages import MessageReceiptRow, MessageRepository, strip_email_message_marker
from app.repositories.offers import OfferRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.requests import RequestRepository
from app.repositories.user_auth_accounts import UserAuthAccountRepository
from app.repositories.units import UnitRepository
from app.repositories.users import UserRepository
from app.infrastructure.notification_publisher import publish_process_notification_event
from app.services.files import FileService, PreparedUpload
from app.services.department_scope import DepartmentScopeService
from app.services.contractor_units import ContractorUnitService
from app.services.staff_access_scope import StaffAccessScopeService
from app.services.notifications import NotificationService
from app.services.requests import RequestFileItem, format_offer_status, format_request_status
from app.infrastructure.delayed_notification_publisher import schedule_unread_chat_email_notification
from app.services.contractor_outbound_notifications import notify_contractor_offer_updated
from shared.process_notifications import ProcessNotificationEvent, build_process_notification_event

DEFAULT_PARTNER_CARD_PATH = (
    "uploads/"
    "КАРТА_ПАРТНЕРА_"
    "01_04_2023_"
    "АКТУАЛЬНАЯ_1_4_2.pdf"
)
DEFAULT_PARTNER_CARD_NAME = (
    "КАРТА_ПАРТНЕРА_"
    "01_04_2023_"
    "АКТУАЛЬНАЯ_1_4_2.pdf"
)
EDITABLE_OFFER_STATUSES = {"submitted", "accepted", "rejected", "deleted"}
PLACEHOLDER_TEXT = "Не указано"
_LOGIN_CLEANUP_PATTERN = re.compile(r"[^a-z0-9_]+")
_LOGIN_COLLAPSE_PATTERN = re.compile(r"_+")
_CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


@dataclass(frozen=True)
class ExistingAttachmentFileInput:
    file_id: int


@dataclass(frozen=True)
class UploadedMessageAttachment:
    file_id: int
    path: str
    name: str


@dataclass(frozen=True)
class ContractorInfo:
    user_id: str
    full_name: str | None
    phone: str | None
    mail: str | None
    company_name: str | None
    inn: str | None
    company_phone: str | None
    company_mail: str | None
    address: str | None
    note: str | None


@dataclass(frozen=True)
class ExistingOfferPreview:
    offer_id: int
    status: str
    status_label: str
    files: list[RequestFileItem]


@dataclass(frozen=True)
class ContractorRequestView:
    request_id: str
    description: str | None
    status: str
    status_label: str
    deadline_at: datetime
    owner_user_id: str
    owner_full_name: str | None
    files: list[RequestFileItem]
    existing_offer: ExistingOfferPreview | None
    latest_offer_id: int | None


@dataclass(frozen=True)
class OfferWorkspaceRequest:
    request_id: str
    description: str | None
    status: str
    status_label: str
    initial_amount: float | None
    final_amount: float | None
    deadline_at: datetime
    owner_user_id: str
    owner_full_name: str | None
    owner_phone: str | None
    owner_mail: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    files: list[RequestFileItem] = field(default_factory=list)


@dataclass(frozen=True)
class OfferWorkspaceOffer:
    offer_id: int
    owner_user_id: str
    status: str
    status_label: str
    offer_amount: float | None
    created_at: datetime
    updated_at: datetime
    files: list[RequestFileItem] = field(default_factory=list)


@dataclass(frozen=True)
class OfferWorkspace:
    request: OfferWorkspaceRequest
    offer: OfferWorkspaceOffer
    offers: list[OfferWorkspaceOffer]
    contractor: ContractorInfo


@dataclass(frozen=True)
class OfferMessageItem:
    id: int
    user_id: str
    user_full_name: str | None
    text: str
    type: str
    status: str
    created_at: datetime
    updated_at: datetime
    read_by: list["OfferMessageReader"] = field(default_factory=list)
    attachments: list[RequestFileItem] = field(default_factory=list)


@dataclass(frozen=True)
class OfferMessageReader:
    user_id: str
    user_full_name: str | None
    read_at: datetime


@dataclass(frozen=True)
class OfferMessageMutationResult:
    offer_id: int
    chat_id: int
    request_id: str
    message_id: int


@dataclass(frozen=True)
class OfferMessageAckResult:
    offer_id: int
    chat_id: int
    updated_message_ids: list[int]
    last_read_message_id: int | None = None

    @property
    def updated_count(self) -> int:
        return len(self.updated_message_ids)


@dataclass(frozen=True)
class ManualContractorCreateInput:
    company_name: str
    inn: str
    company_phone: str
    company_mail: str | None
    address: str | None
    note: str | None = None


@dataclass(frozen=True)
class ManualOfferCreateResult:
    offer_id: int
    request_id: str
    contractor_user_id: str
    contractor_created: bool


@dataclass(frozen=True)
class ManualOfferEligibleContractor:
    user_id: str
    full_name: str | None
    company_name: str | None
    mail: str | None
    company_mail: str | None


class OfferService:
    def __init__(
        self,
        requests: RequestRepository,
        offers: OfferRepository,
        chats: ChatRepository,
        files: FileRepository,
        messages: MessageRepository,
        profiles: ProfileRepository,
        company_contacts: CompanyContactRepository,
        users: UserRepository,
        units: UnitRepository | None = None,
        user_auth_accounts: UserAuthAccountRepository | None = None,
        file_service: FileService | None = None,
        notifications: NotificationService | None = None,
        after_commit_hook_registrar: Callable[[Callable[[], Awaitable[None]]], None] | None = None,
        process_event_publisher: Callable[[ProcessNotificationEvent], Awaitable[bool]] | None = None,
    ):
        self._requests = requests
        self._offers = offers
        self._chats = chats
        self._files = files
        self._messages = messages
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._users = users
        self._units = units
        self._user_auth_accounts = user_auth_accounts
        self._file_service = file_service or FileService(files)
        self._notifications = notifications
        self._after_commit_hook_registrar = after_commit_hook_registrar
        self._process_event_publisher = process_event_publisher or publish_process_notification_event
        self._department_scope = DepartmentScopeService(users)
        self._staff_scope = StaffAccessScopeService(users)

    def _contractor_unit_service(self) -> ContractorUnitService:
        if self._units is None:
            raise RuntimeError("Offer service requires unit repository")
        return ContractorUnitService(users=self._users, units=self._units)

    def _schedule_process_notification_event(self, event: ProcessNotificationEvent) -> bool:
        if self._after_commit_hook_registrar is None:
            return False
        self._after_commit_hook_registrar(
            lambda: self._process_event_publisher(event)
        )
        return True

    def _schedule_contractor_offer_updated_outbound(
        self,
        *,
        contractor_user_id: str,
        request_id: str,
        offer_id: int,
        actor_user_id: str | None,
    ) -> None:
        if actor_user_id is not None and actor_user_id == contractor_user_id:
            return
        if self._after_commit_hook_registrar is None:
            return
        self._after_commit_hook_registrar(
            lambda: notify_contractor_offer_updated(
                contractor_user_id=contractor_user_id,
                request_id=request_id,
                offer_id=offer_id,
                actor_user_id=actor_user_id,
            )
        )

    def _schedule_unread_chat_email_notifications(
        self,
        *,
        message_id: int,
        recipient_user_ids: list[str],
        request_id: str,
        offer_id: int,
        author_user_id: str,
    ) -> None:
        if self._after_commit_hook_registrar is None:
            return
        delay_seconds = max(60, settings.chat_unread_email_delay_seconds)

        async def _schedule_all() -> None:
            for recipient_user_id in recipient_user_ids:
                if recipient_user_id == author_user_id:
                    continue
                await schedule_unread_chat_email_notification(
                    message_id=message_id,
                    recipient_user_id=recipient_user_id,
                    request_id=request_id,
                    offer_id=offer_id,
                    delay_seconds=delay_seconds,
                )

        self._after_commit_hook_registrar(_schedule_all)

    def _build_read_only_chat_state(self, *, chat_id: int, last_message_id: int | None, last_message_at) -> ChatState:
        return ChatState(
            chat_id=chat_id,
            last_message_id=last_message_id,
            last_message_at=last_message_at,
            participant_user_id="",
            last_read_message_id=None,
            last_read_at=last_message_at,
            is_muted=False,
            is_archived=False,
        )

    async def _ensure_request_visible_for_contractor(self, *, current_user: CurrentUser, request_id: str) -> None:
        """Authorize historical offer access without reapplying discovery eligibility."""
        if current_user.role_id != settings.contractor_role_id:
            return
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")
        is_hidden = await self._requests.is_hidden_for_contractor(
            request_id=request_id,
            contractor_user_id=current_user.user_id,
        )
        if is_hidden:
            raise NotFound("Request not found")
        if not await self._contractor_unit_service().can_contractor_access_request_owner(
            contractor_user_id=current_user.user_id,
            request_owner_user_id=request.id_user,
        ):
            raise NotFound("Request not found")

    async def _is_request_available_for_contractor_discovery(self, *, current_user: CurrentUser, request) -> bool:
        return await self._is_request_available_for_contractor_user(
            contractor_user_id=current_user.user_id,
            request=request,
        )

    async def _is_request_available_for_contractor_user(self, *, contractor_user_id: str, request) -> bool:
        """Return the BL-002 discovery eligibility for a concrete contractor.

        Manual offer creation acts on behalf of a contractor, therefore it must
        use exactly the same visibility/lifecycle/root-unit rule as the
        contractor's own request discovery flow.
        """
        owner = await self._users.get_by_id(request.id_user)
        if not RequestPolicy.is_contractor_request_lifecycle_eligible(
            request_owner_role_id=owner.id_role if owner is not None else None,
        ):
            return False
        return await self._contractor_unit_service().can_contractor_access_request_owner(
            contractor_user_id=contractor_user_id,
            request_owner_user_id=request.id_user,
        )

    async def _ensure_contractor_can_create_offer_for_request(
        self,
        *,
        contractor_user_id: str,
        request,
    ) -> None:
        contractor_user = await self._users.get_by_id(contractor_user_id)
        if contractor_user is None or contractor_user.id_role != settings.contractor_role_id:
            raise NotFound("Контрагент не найден")
        if getattr(contractor_user, "status", "active") != "active":
            raise Conflict("Контрагент неактивен и не может быть выбран для коммерческого предложения")
        if await self._requests.is_hidden_for_contractor(
            request_id=request.id,
            contractor_user_id=contractor_user_id,
        ) or not await self._is_request_available_for_contractor_user(
            contractor_user_id=contractor_user_id,
            request=request,
        ):
            raise Forbidden(
                "Контрагент не имеет доступа к данной заявке и не может быть выбран для коммерческого предложения"
            )

    @staticmethod
    def _ensure_request_is_open_for_offer_mutation(*, request_status: str) -> None:
        if request_status in {"closed", "cancelled"}:
            raise Conflict("КП нельзя изменить, если заявка уже закрыта или отклонена")

    async def _load_offer_and_request(self, *, offer_id: int, current_user: CurrentUser | None = None):
        offer = await self._offers.get_by_id(offer_id=offer_id)
        if offer is None:
            raise NotFound("Offer not found")

        request = await self._requests.get_by_id(request_id=offer.id_request)
        if request is None:
            raise NotFound("Request not found")
        if current_user is not None:
            await self._ensure_request_visible_for_contractor(current_user=current_user, request_id=request.id)
        return offer, request

    async def _is_manual_offer(self, *, offer_owner_user_id: str) -> bool:
        offer_owner = await self._users.get_by_id(user_id=offer_owner_user_id)
        if offer_owner is None:
            raise NotFound("Offer owner not found")
        return offer_owner.id_role == settings.contractor_role_id and not await self._users.has_legacy_messenger_account(
            user_id=offer_owner.id
        )

    async def _require_chat_context(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        require_send: bool = False,
    ):
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)
        if require_send:
            await self._ensure_can_send_chat_message(
                current_user=current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )
        else:
            await self._ensure_can_view_chat(
                current_user=current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )

        chat = await self._offers.get_chat(offer_id=offer.id)
        if chat is None:
            raise NotFound("Chat not found")

        chat_state = await self._chats.get_chat_state_for_user(chat_id=chat.id, user_id=current_user.user_id)
        if chat_state is None:
            if await self._can_access_chat_without_participation(
                current_user=current_user,
                request_owner_user_id=request.id_user,
                require_send=require_send,
            ):
                chat_state = self._build_read_only_chat_state(
                    chat_id=chat.id,
                    last_message_id=chat.last_message_id,
                    last_message_at=chat.last_message_at,
                )
            else:
                raise Forbidden("Insufficient permissions to view chat")

        return offer, request, chat, chat_state

    async def _can_access_chat_without_participation(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
        require_send: bool,
    ) -> bool:
        if current_user.role_id == settings.project_manager_role_id:
            return not require_send
        if require_send:
            return False
        has_department_chat_permission = has_permission(
            current_user,
            PermissionCodes.DEPARTMENT_CHATS_READ,
        )
        if not has_department_chat_permission:
            return False
        return await self._is_user_inside_current_department_scope(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        )

    def _normalize_required_text(self, value: str | None, *, field_name: str, max_length: int | None = None) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise Conflict(f"{field_name} is required")
        if max_length is not None and len(normalized) > max_length:
            raise Conflict(f"{field_name} is too long")
        return normalized

    def _normalize_optional_text(self, value: str | None, *, max_length: int | None = None) -> str | None:
        normalized = (value or "").strip()
        if not normalized:
            return None
        if max_length is not None and len(normalized) > max_length:
            raise Conflict("Value is too long")
        return normalized

    def _validate_manual_contractor_create_data(
        self,
        *,
        contractor_data: ManualContractorCreateInput,
    ) -> ManualContractorCreateInput:
        try:
            company_name = self._normalize_required_text(
                contractor_data.company_name,
                field_name="Company name",
                max_length=256,
            )
            inn = validate_inn(
                self._normalize_required_text(
                    contractor_data.inn,
                    field_name="INN",
                    max_length=32,
                )
            )
            company_phone = validate_ru_phone(
                self._normalize_required_text(
                    contractor_data.company_phone,
                    field_name="Company phone",
                    max_length=64,
                )
            )
            company_mail = validate_optional_email(
                self._normalize_optional_text(contractor_data.company_mail, max_length=256),
                allow_placeholder=True,
            )
            address = self._normalize_optional_text(contractor_data.address, max_length=256)
            note = self._normalize_optional_text(contractor_data.note, max_length=1024)
        except ValueError as exc:
            raise Conflict(str(exc)) from exc

        return ManualContractorCreateInput(
            company_name=company_name,
            inn=inn,
            company_phone=company_phone,
            company_mail=company_mail,
            address=address,
            note=note,
        )

    def _build_login_slug(self, company_name: str) -> str:
        normalized_name = unicodedata.normalize("NFKC", company_name.strip().lower())
        transliterated: list[str] = []
        for char in normalized_name:
            if char in _CYRILLIC_TO_LATIN:
                transliterated.append(_CYRILLIC_TO_LATIN[char])
                continue
            if char.isascii() and char.isalnum():
                transliterated.append(char)
                continue
            transliterated.append("_")

        candidate = "".join(transliterated)
        candidate = _LOGIN_CLEANUP_PATTERN.sub("_", candidate)
        candidate = _LOGIN_COLLAPSE_PATTERN.sub("_", candidate).strip("_")
        if candidate:
            return candidate
        return "contractor"

    async def _build_manual_login(self, *, company_name: str) -> str:
        date_suffix = datetime.now().strftime("%d_%m")
        base_slug = self._build_login_slug(company_name)
        base_candidate = f"{base_slug}_{date_suffix}"
        if len(base_candidate) > 120:
            base_candidate = base_candidate[:120].rstrip("_")
        if len(base_candidate) < 3:
            base_candidate = f"{base_candidate}xxx"[:3]

        if not await self._users.exists(base_candidate):
            return base_candidate

        index = 1
        while True:
            suffix = f"_{index}"
            login_candidate = f"{base_candidate[: max(0, 128 - len(suffix))]}{suffix}"
            if not await self._users.exists(login_candidate):
                return login_candidate
            index += 1
            if index > 1000:
                raise Conflict("Unable to generate unique login for manual contractor")

    async def _find_existing_manual_contractor_user_id(
        self,
        *,
        contractor_data: ManualContractorCreateInput,
    ) -> str | None:
        matched_user_ids = await self._users.find_matching_contractor_user_ids(
            contractor_role_id=settings.contractor_role_id,
            email=contractor_data.company_mail,
            inn=contractor_data.inn,
            company_name=contractor_data.company_name,
        )
        if not matched_user_ids:
            return None
        if len(matched_user_ids) > 1:
            raise Conflict("Найдено несколько похожих контрагентов. Уточните данные и повторите попытку.")
        return matched_user_ids[0]

    async def _bind_to_creator_root_units_if_needed(
        self,
        *,
        current_user: CurrentUser,
        contractor_user_id: str,
    ) -> None:
        if self._units is None or current_user.role_id == settings.contractor_role_id:
            return
        creator_root_unit_ids = await self._contractor_unit_service().list_direct_root_unit_ids_for_user(
            user_id=current_user.user_id,
        )
        if not creator_root_unit_ids:
            return
        await self._contractor_unit_service().bind_user_to_root_units(
            user_id=contractor_user_id,
            root_unit_ids=creator_root_unit_ids,
            assigned_by_user_id=current_user.user_id,
        )

    async def _create_manual_contractor(
        self,
        *,
        current_user: CurrentUser,
        contractor_data: ManualContractorCreateInput,
    ) -> tuple[str, bool]:
        existing_contractor_user_id = await self._find_existing_manual_contractor_user_id(
            contractor_data=contractor_data,
        )
        if existing_contractor_user_id is not None:
            await self._bind_to_creator_root_units_if_needed(
                current_user=current_user,
                contractor_user_id=existing_contractor_user_id,
            )
            return existing_contractor_user_id, False

        login = await self._build_manual_login(company_name=contractor_data.company_name)
        await self._users.add(
            User(
                id=login,
                id_role=settings.contractor_role_id,
                status="active",
            )
        )
        await self._profiles.add(
            Profile(
                id=login,
                full_name=PLACEHOLDER_TEXT,
                phone=PLACEHOLDER_TEXT,
                mail=PLACEHOLDER_TEXT,
            )
        )
        await self._company_contacts.add(
            CompanyContact(
                id=login,
                company_name=contractor_data.company_name,
                inn=contractor_data.inn,
                phone=contractor_data.company_phone,
                mail=contractor_data.company_mail or PLACEHOLDER_TEXT,
                address=contractor_data.address or PLACEHOLDER_TEXT,
                note=contractor_data.note or PLACEHOLDER_TEXT,
            )
        )
        await self._bind_to_creator_root_units_if_needed(
            current_user=current_user,
            contractor_user_id=login,
        )
        return login, True

    async def get_request_view(self, *, current_user: CurrentUser, request_id: str) -> ContractorRequestView:
        require_permission(
            current_user,
            PermissionCodes.REQUESTS_CONTRACTOR_VIEW_READ,
            message="Insufficient permissions to view contractor request details",
        )

        # A contractor may open a historical (closed/cancelled) request when
        # they already have an offer on it. Discovery and offer creation remain
        # restricted to open requests below.
        request = await self._requests.get_visible_by_id_for_contractor(
            request_id=request_id,
            contractor_user_id=current_user.user_id,
        )
        if request is None:
            raise NotFound("Request not found")
        owner_profile = await self._profiles.get_by_id(request.id_user)
        request_files = await self._requests.list_files(request_id=request.id)
        request_file_items = [RequestFileItem(id=f.id, path=f.path, name=f.name) for f in request_files]
        existing_offer = await self._offers.get_contractor_offer_for_request(
            request_id=request.id,
            contractor_user_id=current_user.user_id,
        )
        if request.status == "open":
            if not await self._is_request_available_for_contractor_discovery(
                current_user=current_user,
                request=request,
            ):
                raise NotFound("Request not found")
        elif existing_offer is None:
            # Closed requests without this contractor's offer must not become
            # a way to bypass the normal contractor discovery scope.
            raise NotFound("Request not found")
        existing_offer_preview: ExistingOfferPreview | None = None
        if existing_offer is not None:
            offer_files = await self._offers.list_offer_files(offer_id=existing_offer.id)
            existing_offer_preview = ExistingOfferPreview(
                offer_id=existing_offer.id,
                status=existing_offer.status,
                status_label=format_offer_status(existing_offer.status),
                files=[RequestFileItem(id=f.id, path=f.path, name=f.name) for f in offer_files],
            )

        return ContractorRequestView(
            request_id=request.id,
            description=request.description,
            status=request.status,
            status_label=format_request_status(request.status),
            deadline_at=request.deadline_at,
            owner_user_id=request.id_user,
            owner_full_name=(owner_profile.full_name if owner_profile else None),
            files=request_file_items,
            existing_offer=existing_offer_preview,
            latest_offer_id=existing_offer.id if existing_offer is not None else None,
        )

    async def create_offer(
        self,
        *,
        current_user: CurrentUser,
        request_id: str,
        offer_amount: float | None = None,
    ) -> int:
        UserPolicy.ensure_can_create_offer(current_user)
        self._validate_offer_amount(offer_amount)

        await self._requests.lock_offer_lifecycle(request_id=request_id)
        request = await self._requests.get_visible_open_by_id_for_contractor(
            request_id=request_id,
            contractor_user_id=current_user.user_id,
        )
        if request is None:
            raise NotFound("Open request not found")
        if not await self._is_request_available_for_contractor_discovery(
            current_user=current_user,
            request=request,
        ):
            raise NotFound("Open request not found")

        await self._offers.lock_contractor_offer_creation(
            request_id=request.id,
            contractor_user_id=current_user.user_id,
        )
        existing_offer = await self._offers.get_contractor_offer_for_request(
            request_id=request.id,
            contractor_user_id=current_user.user_id,
        )
        if existing_offer and existing_offer.status != "deleted":
            raise Conflict("Offer for this request already exists")

        offer = await self._offers.create(
            request_id=request.id,
            contractor_user_id=current_user.user_id,
            offer_amount=offer_amount,
        )
        event = build_process_notification_event(
            event_type="offer.created",
            actor_user_id=current_user.user_id,
            entity_type="offer",
            entity_id=offer.id,
            request_id=request.id,
            offer_id=offer.id,
            dedupe_key=f"offer.created:{offer.id}",
            payload={"recipient_user_id": request.id_user},
        )
        is_scheduled = self._schedule_process_notification_event(event)
        if not is_scheduled and self._notifications is not None:
            await self._notifications.notify_offer_created(
                actor_user_id=current_user.user_id,
                recipient_user_id=request.id_user,
                request_id=request.id,
                offer_id=offer.id,
            )
        return offer.id

    async def create_manual_offer(
        self,
        *,
        current_user: CurrentUser,
        request_id: str,
        contractor_user_id: str | None,
        contractor_data: ManualContractorCreateInput | None,
        offer_amount: float | None = None,
        files: list[PreparedUpload] | None = None,
    ) -> ManualOfferCreateResult:
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")

        RequestPolicy.ensure_can_create_manual_offer(
            current_user,
            request_owner_user_id=request.id_user,
        )

        if request.status != "open":
            raise Conflict("Manual offer can be created only for open request")

        self._validate_offer_amount(offer_amount)

        normalized_contractor_user_id = self._normalize_optional_text(contractor_user_id)
        if normalized_contractor_user_id and contractor_data is not None:
            raise Conflict("Select existing contractor or provide new contractor data")
        if not normalized_contractor_user_id and contractor_data is None:
            raise Conflict("Contractor is required")

        resolved_contractor_user_id: str
        contractor_created = False
        if contractor_data is not None:
            normalized_contractor_data = self._validate_manual_contractor_create_data(
                contractor_data=contractor_data,
            )
            resolved_contractor_user_id, contractor_created = await self._create_manual_contractor(
                current_user=current_user,
                contractor_data=normalized_contractor_data
            )
        else:
            assert normalized_contractor_user_id is not None
            resolved_contractor_user_id = normalized_contractor_user_id

        await self._ensure_contractor_can_create_offer_for_request(
            contractor_user_id=resolved_contractor_user_id,
            request=request,
        )

        existing_offer = await self._offers.get_contractor_offer_for_request(
            request_id=request.id,
            contractor_user_id=resolved_contractor_user_id,
        )
        if existing_offer is not None and existing_offer.status != "deleted":
            raise Conflict("Offer for this contractor already exists")

        offer = await self._offers.create(
            request_id=request.id,
            contractor_user_id=resolved_contractor_user_id,
            offer_amount=offer_amount,
        )

        for upload in files or []:
            db_file = await self._file_service.create_offer_file(
                offer_id=offer.id,
                upload=upload,
            )
            await self._offers.attach_file(offer_id=offer.id, file_id=db_file.id)

        # Notify the responsible staff user (request owner) that a manual offer was created,
        # matching the notification behaviour of the regular contractor-initiated create_offer flow.
        event = build_process_notification_event(
            event_type="offer.created",
            actor_user_id=current_user.user_id,
            entity_type="offer",
            entity_id=offer.id,
            request_id=request.id,
            offer_id=offer.id,
            dedupe_key=f"offer.created:{offer.id}",
            payload={"recipient_user_id": request.id_user},
        )
        is_scheduled = self._schedule_process_notification_event(event)
        if not is_scheduled and self._notifications is not None:
            await self._notifications.notify_offer_created(
                actor_user_id=current_user.user_id,
                recipient_user_id=request.id_user,
                request_id=request.id,
                offer_id=offer.id,
            )

        return ManualOfferCreateResult(
            offer_id=offer.id,
            request_id=request.id,
            contractor_user_id=resolved_contractor_user_id,
            contractor_created=contractor_created,
        )

    async def list_eligible_contractors_for_manual_offer(
        self,
        *,
        current_user: CurrentUser,
        request_id: str,
    ) -> list[ManualOfferEligibleContractor]:
        request = await self._requests.get_by_id(request_id=request_id)
        if request is None:
            raise NotFound("Request not found")
        RequestPolicy.ensure_can_create_manual_offer(
            current_user,
            request_owner_user_id=request.id_user,
        )
        if request.status != "open":
            return []

        rows = await self._users.list_contractors(contractor_role_id=settings.contractor_role_id)
        eligible: list[ManualOfferEligibleContractor] = []
        for contractor, profile, company, _tg_user, _legacy_account_id in rows:
            if contractor.status != "active":
                continue
            if await self._requests.is_hidden_for_contractor(
                request_id=request.id,
                contractor_user_id=contractor.id,
            ):
                continue
            if not await self._is_request_available_for_contractor_user(
                contractor_user_id=contractor.id,
                request=request,
            ):
                continue
            eligible.append(
                ManualOfferEligibleContractor(
                    user_id=contractor.id,
                    full_name=profile.full_name if profile else None,
                    company_name=company.company_name if company else None,
                    mail=profile.mail if profile else None,
                    company_mail=company.mail if company else None,
                )
            )
        return eligible

    async def get_workspace(self, *, current_user: CurrentUser, offer_id: int) -> OfferWorkspace:
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)
        await self._ensure_can_access_offer_workspace(
            current_user=current_user,
            offer_owner_user_id=offer.id_user,
            request_owner_user_id=request.id_user,
        )

        profile = await self._profiles.get_by_id(offer.id_user)
        company = await self._company_contacts.get_by_id(offer.id_user)
        request_profile = await self._profiles.get_by_id(request.id_user)
        request_files = await self._requests.list_files(request_id=request.id)
        request_file_items = [RequestFileItem(id=f.id, path=f.path, name=f.name) for f in request_files]
        request_offers = await self._offers.list_by_request(request_id=request.id)
        request_offers = [request_offer for request_offer in request_offers if request_offer.id_user == offer.id_user]
        offer_ids = [request_offer.id for request_offer in request_offers]
        offer_files_rows = await self._offers.list_offer_files_by_offer_ids(offer_ids=offer_ids)
        offer_files_by_offer_id: dict[int, list[RequestFileItem]] = {request_offer_id: [] for request_offer_id in offer_ids}
        for request_offer_id, db_file in offer_files_rows:
            offer_files_by_offer_id.setdefault(request_offer_id, []).append(
                RequestFileItem(id=db_file.id, path=db_file.path, name=db_file.name)
            )

        return OfferWorkspace(
            request=OfferWorkspaceRequest(
                request_id=request.id,
                description=request.description,
                status=request.status,
                status_label=format_request_status(request.status),
                initial_amount=request.initial_amount,
                final_amount=request.final_amount,
                deadline_at=request.deadline_at,
                owner_user_id=request.id_user,
                owner_full_name=(request_profile.full_name if request_profile else None),
                owner_phone=request_profile.phone if request_profile else None,
                owner_mail=request_profile.mail if request_profile else None,
                created_at=request.created_at,
                updated_at=request.updated_at,
                closed_at=request.closed_at,
                files=request_file_items,
            ),
            offer=OfferWorkspaceOffer(
                offer_id=offer.id,
                owner_user_id=offer.id_user,
                status=offer.status,
                status_label=format_offer_status(offer.status),
                offer_amount=offer.offer_amount,
                created_at=offer.created_at,
                updated_at=offer.updated_at,
                files=list(offer_files_by_offer_id.get(offer.id, [])),
            ),
            offers=[
                OfferWorkspaceOffer(
                    offer_id=request_offer.id,
                    owner_user_id=request_offer.id_user,
                    status=request_offer.status,
                    status_label=format_offer_status(request_offer.status),
                    offer_amount=request_offer.offer_amount,
                    created_at=request_offer.created_at,
                    updated_at=request_offer.updated_at,
                    files=list(offer_files_by_offer_id.get(request_offer.id, [])),
                )
                for request_offer in request_offers
            ],
            contractor=ContractorInfo(
                user_id=offer.id_user,
                full_name=profile.full_name if profile else None,
                phone=profile.phone if profile else None,
                mail=profile.mail if profile else None,
                company_name=company.company_name if company else None,
                inn=company.inn if company else None,
                company_phone=company.phone if company else None,
                company_mail=company.mail if company else None,
                address=company.address if company else None,
                note=company.note if company else None,
            ),
        )

    async def get_contractor_info(self, *, current_user: CurrentUser, contractor_user_id: str) -> ContractorInfo:
        OfferPolicy.ensure_can_view_contractor_info(current_user, contractor_user_id=contractor_user_id)

        profile = await self._profiles.get_by_id(contractor_user_id)
        company = await self._company_contacts.get_by_id(contractor_user_id)
        if profile is None and company is None:
            raise NotFound("Contractor not found")

        return ContractorInfo(
            user_id=contractor_user_id,
            full_name=profile.full_name if profile else None,
            phone=profile.phone if profile else None,
            mail=profile.mail if profile else None,
            company_name=company.company_name if company else None,
            inn=company.inn if company else None,
            company_phone=company.phone if company else None,
            company_mail=company.mail if company else None,
            address=company.address if company else None,
            note=company.note if company else None,
        )

    async def add_file(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        upload: PreparedUpload,
    ) -> int:
        offer = await self._offers.get_by_id(offer_id=offer_id)
        if offer is None:
            raise NotFound("Offer not found")
        await self._ensure_request_visible_for_contractor(current_user=current_user, request_id=offer.id_request)
        request = await self._requests.get_by_id(request_id=offer.id_request)
        if request is None:
            raise NotFound("Request not found")
        self._ensure_request_is_open_for_offer_mutation(request_status=request.status)
        has_department_offer_update_scope = await self._has_department_offer_update_scope(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )
        if current_user.role_id == settings.contractor_role_id:
            require_permission(
                current_user,
                PermissionCodes.OFFERS_FILES_UPLOAD,
                message="Insufficient permissions to upload offer files",
            )
            OfferPolicy.ensure_can_manage_offer(
                current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )
        elif not has_department_offer_update_scope:
            require_permission(
                current_user,
                PermissionCodes.OFFERS_UPDATE,
                message="Insufficient permissions to edit offer",
            )
        elif has_department_offer_update_scope:
            pass
        elif has_permission(current_user, PermissionCodes.OFFERS_DETAILS_UPDATE):
            await self._ensure_can_manage_offer_for_internal_user(
                current_user=current_user,
                request_owner_user_id=request.id_user,
                offer_owner_user_id=offer.id_user,
                allow_department_request_update=False,
            )
        else:
            raise Forbidden(
                "Insufficient permissions to upload offer files",
            )

        if (
            current_user.role_id == settings.contractor_role_id
            and current_user.user_id == offer.id_user
            and offer.status in {"accepted", "rejected"}
        ):
            raise Conflict("Cannot edit files for finalized offer")

        db_file = await self._file_service.create_offer_file(
            offer_id=offer.id,
            upload=upload,
        )
        await self._offers.attach_file(offer_id=offer.id, file_id=db_file.id)
        original_name = getattr(db_file, "original_name", None) or upload.original_name
        self._schedule_process_notification_event(
            build_process_notification_event(
                event_type="offer.updated",
                actor_user_id=current_user.user_id,
                entity_type="offer",
                entity_id=offer.id,
                request_id=request.id,
                offer_id=offer.id,
                dedupe_key=f"offer.updated:{offer.id}:{db_file.id}",
                payload={
                    "request_id": request.id,
                    "offer_id": offer.id,
                    "offer_author_user_id": offer.id_user,
                    "actor_user_id": current_user.user_id,
                    "file_ids": [db_file.id],
                    "changed_file_count": 1,
                    "original_names": [original_name],
                },
            )
        )
        self._schedule_contractor_offer_updated_outbound(
            contractor_user_id=offer.id_user,
            request_id=request.id,
            offer_id=offer.id,
            actor_user_id=current_user.user_id,
        )
        return db_file.id

    async def remove_file(self, *, current_user: CurrentUser, offer_id: int, file_id: int) -> None:
        offer = await self._offers.get_by_id(offer_id=offer_id)
        if offer is None:
            raise NotFound("Offer not found")
        await self._ensure_request_visible_for_contractor(current_user=current_user, request_id=offer.id_request)
        request = await self._requests.get_by_id(request_id=offer.id_request)
        if request is None:
            raise NotFound("Request not found")
        self._ensure_request_is_open_for_offer_mutation(request_status=request.status)
        has_department_offer_update_scope = await self._has_department_offer_update_scope(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )
        if current_user.role_id == settings.contractor_role_id:
            require_permission(
                current_user,
                PermissionCodes.OFFERS_FILES_DELETE,
                message="Insufficient permissions to delete offer files",
            )
            OfferPolicy.ensure_can_manage_offer(
                current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )
        elif not has_department_offer_update_scope:
            require_permission(
                current_user,
                PermissionCodes.OFFERS_UPDATE,
                message="Insufficient permissions to edit offer",
            )
        elif has_department_offer_update_scope:
            pass
        elif has_permission(current_user, PermissionCodes.OFFERS_DETAILS_UPDATE):
            await self._ensure_can_manage_offer_for_internal_user(
                current_user=current_user,
                request_owner_user_id=request.id_user,
                offer_owner_user_id=offer.id_user,
                allow_department_request_update=False,
            )
        else:
            raise Forbidden(
                "Insufficient permissions to delete offer files",
            )

        detached = await self._offers.detach_file(offer_id=offer.id, file_id=file_id)
        if not detached:
            raise NotFound("File is not attached to offer")

        await self._file_service.delete_file(file_id=file_id)
        self._schedule_process_notification_event(
            build_process_notification_event(
                event_type="offer.updated",
                actor_user_id=current_user.user_id,
                entity_type="offer",
                entity_id=offer.id,
                request_id=request.id,
                offer_id=offer.id,
                dedupe_key=f"offer.updated:{offer.id}:{file_id}:deleted",
                payload={
                    "request_id": request.id,
                    "offer_id": offer.id,
                    "offer_author_user_id": offer.id_user,
                    "actor_user_id": current_user.user_id,
                    "file_ids": [file_id],
                    "changed_file_count": 1,
                },
            )
        )
        self._schedule_contractor_offer_updated_outbound(
            contractor_user_id=offer.id_user,
            request_id=request.id,
            offer_id=offer.id,
            actor_user_id=current_user.user_id,
        )

    async def update_status(self, *, current_user: CurrentUser, offer_id: int, status: str) -> str:
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)
        await self._requests.lock_offer_lifecycle(request_id=request.id)
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)

        if status not in EDITABLE_OFFER_STATUSES:
            raise Conflict("Unsupported offer status")
        self._ensure_request_is_open_for_offer_mutation(request_status=request.status)
        has_department_status_scope = await self._ensure_can_update_offer_status(
            current_user=current_user,
            request_owner_user_id=request.id_user,
            status=status,
        )

        is_contractor_deleting_own_offer = (
            current_user.role_id == settings.contractor_role_id
            and current_user.user_id == offer.id_user
            and status == "deleted"
        )

        if not is_contractor_deleting_own_offer:
            if not has_department_status_scope:
                await self._ensure_can_update_offer_status_without_department_scope(
                    current_user=current_user,
                    request_owner_user_id=request.id_user,
                    offer_owner_user_id=offer.id_user,
                )
        status_changed = offer.status != status
        previous_status = offer.status
        if status == "accepted" and status_changed:
            if await self._requests.has_accepted_offer_for_request(
                request_id=request.id,
                exclude_offer_id=offer.id,
            ):
                raise Conflict("Для заявки уже выбрано принятое КП")
        await self._offers.update_status(offer=offer, status=status)

        if status_changed and status in {"accepted", "rejected", "deleted"}:
            event = build_process_notification_event(
                event_type="offer.status_changed",
                actor_user_id=current_user.user_id,
                entity_type="offer",
                entity_id=offer.id,
                request_id=request.id,
                offer_id=offer.id,
                dedupe_key=f"offer.status_changed:{offer.id}:{previous_status}->{status}",
                payload={
                    "recipient_user_ids": [offer.id_user, request.id_user],
                    "old_status": previous_status,
                    "new_status": status,
                },
            )
            self._schedule_process_notification_event(event)

        return offer.status

    async def update_amount(self, *, current_user: CurrentUser, offer_id: int, offer_amount: float) -> float:
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)
        await self._requests.lock_offer_lifecycle(request_id=request.id)
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)
        self._ensure_request_is_open_for_offer_mutation(request_status=request.status)
        self._validate_offer_amount(offer_amount)
        has_department_offer_update_scope = await self._has_department_offer_update_scope(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        )

        if current_user.role_id == settings.contractor_role_id:
            require_permission(
                current_user,
                PermissionCodes.OFFERS_AMOUNT_UPDATE,
                message="Insufficient permissions to update offer amount",
            )
            OfferPolicy.ensure_can_manage_offer(
                current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )
        elif not has_department_offer_update_scope:
            require_permission(
                current_user,
                PermissionCodes.OFFERS_UPDATE,
                message="Insufficient permissions to edit offer",
            )
        elif has_department_offer_update_scope:
            pass
        elif has_permission(current_user, PermissionCodes.OFFERS_AMOUNT_UPDATE):
            await self._ensure_can_manage_offer_for_internal_user(
                current_user=current_user,
                request_owner_user_id=request.id_user,
                offer_owner_user_id=offer.id_user,
                allow_department_request_update=False,
            )
        else:
            raise Forbidden("Insufficient permissions to update offer amount")
        if (
            current_user.role_id == settings.contractor_role_id
            and current_user.user_id == offer.id_user
            and offer.status in {"accepted", "rejected"}
        ):
            raise Conflict("Cannot edit amount for finalized offer")

        old_offer_amount = offer.offer_amount
        await self._offers.update_amount(offer=offer, offer_amount=offer_amount)
        if old_offer_amount != offer.offer_amount:
            self._schedule_process_notification_event(
                build_process_notification_event(
                    event_type="offer.updated",
                    actor_user_id=current_user.user_id,
                    entity_type="offer",
                    entity_id=offer.id,
                    request_id=request.id,
                    offer_id=offer.id,
                    dedupe_key=f"offer.updated:{offer.id}:amount:{old_offer_amount}->{offer.offer_amount}",
                    payload={
                        "request_id": request.id,
                        "offer_id": offer.id,
                        "offer_author_user_id": offer.id_user,
                        "actor_user_id": current_user.user_id,
                        "old_offer_amount": str(old_offer_amount) if old_offer_amount is not None else None,
                        "new_offer_amount": str(offer.offer_amount) if offer.offer_amount is not None else None,
                    },
                )
            )
            self._schedule_contractor_offer_updated_outbound(
                contractor_user_id=offer.id_user,
                request_id=request.id,
                offer_id=offer.id,
                actor_user_id=current_user.user_id,
            )
        return float(Decimal(str(offer.offer_amount)))

    async def list_messages(self, *, current_user: CurrentUser, offer_id: int) -> list[OfferMessageItem]:
        _, _, chat, _ = await self._require_chat_context(current_user=current_user, offer_id=offer_id, require_send=False)

        messages = await self._messages.list_by_chat(chat_id=chat.id)
        message_ids = [item.id for item in messages]
        files_map: dict[int, list[RequestFileItem]] = {msg_id: [] for msg_id in message_ids}
        for message_id, db_file in await self._messages.list_files_by_message_ids(message_ids=message_ids):
            files_map.setdefault(message_id, []).append(
                RequestFileItem(id=db_file.id, path=db_file.path, name=db_file.name)
            )

        message_user_ids = list({item.id_user for item in messages})
        profiles = await self._profiles.get_by_ids(message_user_ids)
        full_name_by_user_id = {profile.id: profile.full_name for profile in profiles}
        active_participant_user_ids = await self._chats.list_active_participant_user_ids(chat_id=chat.id)
        receipts = await self._messages.list_receipts_by_message_ids(
            message_ids=message_ids,
            recipient_user_ids=active_participant_user_ids,
        )
        receipts_by_message_id: dict[int, dict[str, MessageReceiptRow]] = {}
        for receipt in receipts:
            receipts_by_message_id.setdefault(receipt.message_id, {})[receipt.user_id] = receipt

        receipt_user_ids = list({receipt.user_id for receipt in receipts})
        if receipt_user_ids:
            receipt_profiles = await self._profiles.get_by_ids(receipt_user_ids)
            for profile in receipt_profiles:
                full_name_by_user_id.setdefault(profile.id, profile.full_name)

        return [
            OfferMessageItem(
                id=item.id,
                user_id=item.id_user,
                user_full_name=full_name_by_user_id.get(item.id_user),
                text=strip_email_message_marker(item.text),
                type=item.type,
                status=self._resolve_message_status(
                    message_user_id=item.id_user,
                    current_user_id=current_user.user_id,
                    active_participant_user_ids=active_participant_user_ids,
                    receipts_by_user=receipts_by_message_id.get(item.id, {}),
                ),
                created_at=item.created_at,
                updated_at=item.updated_at,
                read_by=self._build_read_by(
                    message_user_id=item.id_user,
                    current_user_id=current_user.user_id,
                    active_participant_user_ids=active_participant_user_ids,
                    receipts_by_user=receipts_by_message_id.get(item.id, {}),
                    full_name_by_user_id=full_name_by_user_id,
                ),
                attachments=files_map.get(item.id, []),
            )
            for item in messages
        ]

    async def create_message_upload(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        upload: PreparedUpload,
    ) -> UploadedMessageAttachment:
        offer, request, _chat, _ = await self._require_chat_context(
            current_user=current_user,
            offer_id=offer_id,
            require_send=True,
        )
        if not await self._can_attach_chat_files(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        ):
            raise Forbidden("Insufficient permissions to attach files to chat messages")
        db_file = await self._file_service.create_chat_temp_file(
            offer_id=offer.id,
            upload=upload,
        )
        return UploadedMessageAttachment(file_id=db_file.id, path=db_file.path, name=db_file.name)

    async def _filter_message_notification_recipients(
        self,
        *,
        chat_id: int,
        participant_user_ids: Sequence[str],
    ) -> list[str]:
        unique_participants: list[str] = []
        seen: set[str] = set()
        for user_id in participant_user_ids:
            normalized_user_id = user_id.strip()
            if not normalized_user_id or normalized_user_id in seen:
                continue
            seen.add(normalized_user_id)
            unique_participants.append(normalized_user_id)

        try:
            # Local import avoids circular dependency between realtime runtime and offer service modules.
            from app.realtime.runtime import get_chat_runtime

            runtime = get_chat_runtime()
        except Exception:
            return unique_participants

        recipients: list[str] = []
        for user_id in unique_participants:
            try:
                is_subscribed = await runtime.manager.is_user_subscribed(user_id=user_id, chat_id=chat_id)
            except Exception:
                recipients.append(user_id)
                continue

            if not is_subscribed:
                recipients.append(user_id)

        return recipients

    async def create_message(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        text: str,
        attachments: list[PreparedUpload] | None = None,
        existing_file_refs: list[ExistingAttachmentFileInput] | None = None,
    ) -> OfferMessageMutationResult:
        offer, request, chat, _ = await self._require_chat_context(
            current_user=current_user,
            offer_id=offer_id,
            require_send=True,
        )

        normalized_text = text.strip()
        new_attachments = attachments or []
        stored_file_refs = existing_file_refs or []
        has_file_payload = bool(new_attachments or stored_file_refs)
        if has_file_payload and not await self._can_attach_chat_files(
            current_user=current_user,
            request_owner_user_id=request.id_user,
        ):
            raise Forbidden("Insufficient permissions to attach files to chat messages")
        if not normalized_text and not new_attachments and not stored_file_refs:
            raise Conflict("Message text cannot be empty")

        message_type = self._resolve_message_type(
            has_text=bool(normalized_text),
            has_attachments=bool(new_attachments or stored_file_refs),
        )
        message = await self._messages.create(
            chat_id=chat.id,
            user_id=current_user.user_id,
            text=normalized_text,
            message_type=message_type,
        )
        for attachment in new_attachments:
            db_file = await self._file_service.create_chat_message_file(
                offer_id=offer.id,
                upload=attachment,
            )
            await self._messages.attach_file(message_id=message.id, file_id=db_file.id)
        for file_ref in stored_file_refs:
            db_file = await self._files.get_by_id(file_ref.file_id)
            if db_file is None:
                raise NotFound("File not found")
            await self._messages.attach_file(message_id=message.id, file_id=db_file.id)

        participant_user_ids = await self._chats.list_active_participant_user_ids(chat_id=chat.id)
        notification_recipients = await self._filter_message_notification_recipients(
            chat_id=chat.id,
            participant_user_ids=participant_user_ids,
        )
        event = build_process_notification_event(
            event_type="message.created",
            actor_user_id=current_user.user_id,
            entity_type="message",
            entity_id=message.id,
            request_id=request.id,
            offer_id=offer.id,
            chat_id=chat.id,
            message_id=message.id,
            dedupe_key=f"message.created:{message.id}",
            payload={
                "recipient_user_ids": notification_recipients,
                "has_files": bool(new_attachments or stored_file_refs),
                "file_count": len(new_attachments) + len(stored_file_refs),
            },
        )
        is_scheduled = self._schedule_process_notification_event(event)
        if not is_scheduled and self._notifications is not None:
            await self._notifications.notify_message_created(
                author_user_id=current_user.user_id,
                recipient_user_ids=notification_recipients,
                request_id=request.id,
                offer_id=offer.id,
                chat_id=chat.id,
                message_id=message.id,
            )

        self._schedule_unread_chat_email_notifications(
            message_id=message.id,
            recipient_user_ids=notification_recipients,
            request_id=request.id,
            offer_id=offer.id,
            author_user_id=current_user.user_id,
        )

        return OfferMessageMutationResult(
            offer_id=offer.id,
            chat_id=chat.id,
            request_id=request.id,
            message_id=message.id,
        )

    async def mark_messages_received(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        message_ids: list[int] | None = None,
        up_to_message_id: int | None = None,
    ) -> OfferMessageAckResult:
        require_permission(
            current_user,
            PermissionCodes.CHAT_RECEIPTS_MARK_RECEIVED,
            message="Insufficient permissions to acknowledge delivered chat messages",
        )
        _, _, chat, _ = await self._require_chat_context(
            current_user=current_user,
            offer_id=offer_id,
            require_send=False,
        )
        updated_message_ids = await self._messages.mark_delivered(
            chat_id=chat.id,
            recipient_user_id=current_user.user_id,
            message_ids=message_ids,
            up_to_message_id=up_to_message_id,
        )
        return OfferMessageAckResult(
            offer_id=offer_id,
            chat_id=chat.id,
            updated_message_ids=updated_message_ids,
        )

    async def mark_messages_read(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        message_ids: list[int] | None = None,
        up_to_message_id: int | None = None,
    ) -> OfferMessageAckResult:
        require_permission(
            current_user,
            PermissionCodes.CHAT_RECEIPTS_MARK_READ,
            message="Insufficient permissions to mark chat messages as read",
        )
        _, _, chat, _ = await self._require_chat_context(
            current_user=current_user,
            offer_id=offer_id,
            require_send=False,
        )
        updated_message_ids = await self._messages.mark_read(
            chat_id=chat.id,
            recipient_user_id=current_user.user_id,
            message_ids=message_ids,
            up_to_message_id=up_to_message_id,
        )

        last_read_message_id = await self._chats.get_message_read_boundary(
            chat_id=chat.id,
            user_id=current_user.user_id,
            up_to_message_id=up_to_message_id,
            message_ids=updated_message_ids,
        )
        if last_read_message_id is not None:
            await self._chats.advance_last_read(
                chat_id=chat.id,
                user_id=current_user.user_id,
                message_id=last_read_message_id,
            )

        return OfferMessageAckResult(
            offer_id=offer_id,
            chat_id=chat.id,
            updated_message_ids=updated_message_ids,
            last_read_message_id=last_read_message_id,
        )

    async def get_chat_state(self, *, current_user: CurrentUser, offer_id: int) -> ChatState:
        _, _, _, chat_state = await self._require_chat_context(current_user=current_user, offer_id=offer_id, require_send=False)
        return chat_state

    async def build_message_item(self, *, current_user: CurrentUser, offer_id: int, message_id: int) -> OfferMessageItem:
        items = await self.list_messages(current_user=current_user, offer_id=offer_id)
        for item in items:
            if item.id == message_id:
                return item
        raise NotFound("Message not found")

    async def _ensure_can_access_offer_workspace(
        self,
        *,
        current_user: CurrentUser,
        offer_owner_user_id: str,
        request_owner_user_id: str,
    ) -> None:
        if has_permission(current_user, PermissionCodes.OFFERS_WORKSPACE_READ):
            OfferPolicy.ensure_can_access_offer_workspace(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
            )
            if (
                current_user.role_id != settings.contractor_role_id
                and not await self._staff_scope.can_view_request_owner(
                    current_user=current_user,
                    request_owner_user_id=request_owner_user_id,
                )
            ):
                raise Forbidden("Insufficient permissions to view offer workspace")
            return
        has_department_offer_scope = (
            has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_UPDATE)
            or has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_ACCEPT)
            or has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_REJECT)
        )
        if has_department_offer_scope and await self._is_user_inside_current_department_scope(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        ):
            return
        raise Forbidden("Insufficient permissions to view offer workspace")

    async def _ensure_can_view_chat(
        self,
        *,
        current_user: CurrentUser,
        offer_owner_user_id: str,
        request_owner_user_id: str,
    ) -> None:
        if has_permission(current_user, PermissionCodes.CHAT_READ):
            OfferPolicy.ensure_can_view_chat(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
            )
            if (
                current_user.role_id != settings.contractor_role_id
                and not await self._staff_scope.can_view_chat_for_request(
                    current_user=current_user,
                    request_owner_user_id=request_owner_user_id,
                )
            ):
                raise Forbidden("Insufficient permissions to view chat")
            return
        if (
            has_permission(current_user, PermissionCodes.DEPARTMENT_CHATS_READ)
            and await self._is_user_inside_current_department_scope(
                current_user=current_user,
                target_user_id=request_owner_user_id,
            )
        ):
            return
        raise Forbidden("Insufficient permissions to view chat")

    async def _ensure_can_send_chat_message(
        self,
        *,
        current_user: CurrentUser,
        offer_owner_user_id: str,
        request_owner_user_id: str,
    ) -> None:
        if has_permission(current_user, PermissionCodes.CHAT_MESSAGE_SEND):
            OfferPolicy.ensure_can_send_chat_message(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
                request_owner_user_id=request_owner_user_id,
            )
            if (
                current_user.role_id != settings.contractor_role_id
                and not await self._staff_scope.can_send_chat_for_request(
                    current_user=current_user,
                    request_owner_user_id=request_owner_user_id,
                )
            ):
                raise Forbidden("Insufficient permissions to send chat message")
            return
        if (
            has_permission(
                current_user,
                PermissionCodes.DEPARTMENT_CHATS_SEND_MESSAGE,
            )
            and await self._is_user_inside_current_department_scope(
                current_user=current_user,
                target_user_id=request_owner_user_id,
            )
        ):
            return
        raise Forbidden("Insufficient permissions to send chat message")

    async def _can_attach_chat_files(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        if has_permission(current_user, PermissionCodes.CHAT_MESSAGE_ATTACH):
            return True
        return False

    async def _has_department_offer_update_scope(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        if not has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_UPDATE):
            return False
        return await self._is_user_inside_current_department_scope(
            current_user=current_user,
            target_user_id=request_owner_user_id,
        )

    async def _ensure_can_manage_offer_for_internal_user(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
        offer_owner_user_id: str | None = None,
        allow_department_request_update: bool = False,
    ) -> None:
        if current_user.role_id == settings.contractor_role_id:
            if offer_owner_user_id is None:
                raise Forbidden("Insufficient permissions to manage offer")
            OfferPolicy.ensure_can_manage_offer(
                current_user,
                offer_owner_user_id=offer_owner_user_id,
                request_owner_user_id=request_owner_user_id,
            )
            return

        if (
            allow_department_request_update
            and
            has_permission(current_user, PermissionCodes.DEPARTMENT_REQUESTS_UPDATE)
            and await self._is_user_inside_current_department_scope(
                current_user=current_user,
                target_user_id=request_owner_user_id,
            )
        ):
            return

        if (
            current_user.role_id in {
                settings.project_manager_role_id,
                settings.lead_economist_role_id,
                settings.economist_role_id,
            }
        ):
            # When department-request delegation should not apply, use strict
            # hierarchy scope to avoid implicit escalation from
            # `department.requests.update` to offer-level edits.
            if allow_department_request_update:
                can_manage_scope = await self._staff_scope.can_manage_request_owner(
                    current_user=current_user,
                    request_owner_user_id=request_owner_user_id,
                )
            else:
                can_manage_scope = await self._is_inside_hierarchy_management_scope(
                    current_user=current_user,
                    request_owner_user_id=request_owner_user_id,
                )
            if not can_manage_scope:
                raise Forbidden("Insufficient permissions to manage offer")

        if offer_owner_user_id is None:
            offer_owner_user_id = current_user.user_id
        OfferPolicy.ensure_can_manage_offer(
            current_user,
            offer_owner_user_id=offer_owner_user_id,
            request_owner_user_id=request_owner_user_id,
        )

    async def _ensure_can_update_offer_status(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
        status: str,
    ) -> bool:
        if status == "accepted":
            if (
                has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_ACCEPT)
                and await self._is_user_inside_current_department_scope(
                    current_user=current_user,
                    target_user_id=request_owner_user_id,
                )
            ):
                return True
        if status == "rejected":
            if (
                has_permission(current_user, PermissionCodes.DEPARTMENT_OFFERS_REJECT)
                and await self._is_user_inside_current_department_scope(
                    current_user=current_user,
                    target_user_id=request_owner_user_id,
                )
            ):
                return True

        require_permission(
            current_user,
            PermissionCodes.OFFERS_STATUS_UPDATE,
            message="Insufficient permissions to update offer status",
        )
        return False

    async def _ensure_can_update_offer_status_without_department_scope(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
        offer_owner_user_id: str,
    ) -> None:
        if current_user.role_id in {
            settings.project_manager_role_id,
            settings.lead_economist_role_id,
            settings.economist_role_id,
        }:
            if not await self._is_inside_hierarchy_management_scope(
                current_user=current_user,
                request_owner_user_id=request_owner_user_id,
            ):
                raise Forbidden("Offer is outside your management scope")

        OfferPolicy.ensure_can_manage_offer(
            current_user,
            offer_owner_user_id=offer_owner_user_id,
            request_owner_user_id=request_owner_user_id,
        )

    async def _is_user_inside_current_department_scope(
        self,
        *,
        current_user: CurrentUser,
        target_user_id: str,
    ) -> bool:
        owner_ids = await self._department_scope.resolve_department_owner_ids_for_current_user(
            current_user=current_user,
        )
        return target_user_id in set(owner_ids)

    async def _is_inside_hierarchy_management_scope(
        self,
        *,
        current_user: CurrentUser,
        request_owner_user_id: str,
    ) -> bool:
        return await self._staff_scope.is_hierarchy_manager_of(
            current_user=current_user,
            request_owner_user_id=request_owner_user_id,
        )

    def _resolve_message_type(self, *, has_text: bool, has_attachments: bool) -> str:
        if has_text and has_attachments:
            return "mixed"
        if has_attachments:
            return "file"
        return "text"

    def _validate_offer_amount(self, value: float | None) -> None:
        if value is None:
            return
        if value < 0:
            raise Conflict("Offer amount cannot be negative")

    def _resolve_message_status(
        self,
        *,
        message_user_id: str,
        current_user_id: str,
        active_participant_user_ids: Sequence[str],
        receipts_by_user: dict[str, MessageReceiptRow],
    ) -> str:
        if message_user_id != current_user_id:
            current_user_receipt = receipts_by_user.get(current_user_id)
            if current_user_receipt is None:
                return "send"
            if current_user_receipt.read_at is not None:
                return "read"
            if current_user_receipt.delivered_at is not None:
                return "received"
            return "send"

        recipient_ids = [user_id for user_id in active_participant_user_ids if user_id != current_user_id]
        if not recipient_ids:
            return "read"
        if any(
            receipts_by_user.get(user_id) and receipts_by_user[user_id].read_at is not None
            for user_id in recipient_ids
        ):
            return "read"
        if any(
            receipts_by_user.get(user_id) and receipts_by_user[user_id].delivered_at is not None
            for user_id in recipient_ids
        ):
            return "received"
        return "send"

    def _build_read_by(
        self,
        *,
        message_user_id: str,
        current_user_id: str,
        active_participant_user_ids: Sequence[str],
        receipts_by_user: dict[str, MessageReceiptRow],
        full_name_by_user_id: dict[str, str | None],
    ) -> list[OfferMessageReader]:
        if message_user_id != current_user_id:
            return []

        readers: list[OfferMessageReader] = []
        for user_id in active_participant_user_ids:
            if user_id == current_user_id:
                continue
            receipt = receipts_by_user.get(user_id)
            if receipt is None or receipt.read_at is None:
                continue
            read_at = receipt.read_at
            if not isinstance(read_at, datetime):
                continue
            readers.append(
                OfferMessageReader(
                    user_id=user_id,
                    user_full_name=full_name_by_user_id.get(user_id),
                    read_at=read_at,
                )
            )

        readers.sort(key=lambda item: item.read_at)
        return readers

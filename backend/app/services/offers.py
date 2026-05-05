from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

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
from app.repositories.users import UserRepository
from app.services.files import FileService
from app.services.keycloak_admin import KeycloakAdminService
from app.services.requests import RequestFileItem, format_offer_status, format_request_status
from app.services.tg_notifications import notify_new_message, notify_offer_status_finalized

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


def _normalize_keycloak_email_value(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized or normalized == PLACEHOLDER_TEXT:
        return None
    return normalized

@dataclass(frozen=True)
class AttachmentFileInput:
    original_name: str
    content_bytes: bytes
    mime_type: str


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
    request_id: int
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
    request_id: int
    description: str | None
    status: str
    status_label: str
    initial_amount: float | None
    final_amount: float | None
    deadline_at: datetime
    owner_user_id: str
    owner_full_name: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    files: list[RequestFileItem] = field(default_factory=list)


@dataclass(frozen=True)
class OfferWorkspaceOffer:
    offer_id: int
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
    request_id: int
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
    request_id: int
    contractor_user_id: str
    contractor_created: bool


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
        file_service: FileService | None = None,
        keycloak_admin: KeycloakAdminService | None = None,
    ):
        self._requests = requests
        self._offers = offers
        self._chats = chats
        self._files = files
        self._messages = messages
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._users = users
        self._file_service = file_service or FileService(files)
        self._keycloak_admin = keycloak_admin or KeycloakAdminService()

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

    async def _ensure_request_visible_for_contractor(self, *, current_user: CurrentUser, request_id: int) -> None:
        if current_user.role_id != settings.contractor_role_id:
            return
        is_hidden = await self._requests.is_hidden_for_contractor(
            request_id=request_id,
            contractor_user_id=current_user.user_id,
        )
        if is_hidden:
            raise NotFound("Request not found")

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
        return (
            offer_owner.id_role == settings.contractor_role_id
            and offer_owner.tg_user_id is None
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
            OfferPolicy.ensure_can_send_chat_message(
                current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )
        else:
            OfferPolicy.ensure_can_view_chat(current_user, offer_owner_user_id=offer.id_user)

        chat = await self._offers.get_chat(offer_id=offer.id)
        if chat is None:
            raise NotFound("Chat not found")

        chat_state = await self._chats.get_chat_state_for_user(chat_id=chat.id, user_id=current_user.user_id)
        if chat_state is None:
            if not require_send and current_user.role_id == settings.project_manager_role_id:
                chat_state = self._build_read_only_chat_state(
                    chat_id=chat.id,
                    last_message_id=chat.last_message_id,
                    last_message_at=chat.last_message_at,
                )
            else:
                raise Forbidden("Insufficient permissions to view chat")

        return offer, request, chat, chat_state

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

    def _build_manual_password(self) -> str:
        return datetime.now().strftime("%d%m%Y%H%M%S%f")[:-3]

    async def _create_manual_contractor(
        self,
        *,
        contractor_data: ManualContractorCreateInput,
    ) -> str:
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
        await self._keycloak_admin.ensure_user(
            username=login,
            email=_normalize_keycloak_email_value(contractor_data.company_mail),
            email_verified=False,
        )
        return login

    async def get_request_view(self, *, current_user: CurrentUser, request_id: int) -> ContractorRequestView:
        UserPolicy.ensure_can_create_offer(current_user)

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
        existing_offer_preview: ExistingOfferPreview | None = None
        if existing_offer is not None and existing_offer.status != "deleted":
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
        request_id: int,
        offer_amount: float | None = None,
    ) -> int:
        UserPolicy.ensure_can_create_offer(current_user)
        self._validate_offer_amount(offer_amount)

        request = await self._requests.get_visible_open_by_id_for_contractor(
            request_id=request_id,
            contractor_user_id=current_user.user_id,
        )
        if request is None:
            raise NotFound("Open request not found")

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
        return offer.id

    async def create_manual_offer(
        self,
        *,
        current_user: CurrentUser,
        request_id: int,
        contractor_user_id: str | None,
        contractor_data: ManualContractorCreateInput | None,
        offer_amount: float | None = None,
        files: list[AttachmentFileInput] | None = None,
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
            resolved_contractor_user_id = await self._create_manual_contractor(
                contractor_data=normalized_contractor_data
            )
            contractor_created = True
        else:
            assert normalized_contractor_user_id is not None
            contractor_user = await self._users.get_by_id(normalized_contractor_user_id)
            if contractor_user is None:
                raise NotFound("Contractor not found")
            if contractor_user.id_role != settings.contractor_role_id:
                raise Conflict("Selected user is not contractor")
            if contractor_user.status != "active":
                raise Conflict("Selected contractor must be active")
            is_hidden = await self._requests.is_hidden_for_contractor(
                request_id=request.id,
                contractor_user_id=normalized_contractor_user_id,
            )
            if is_hidden:
                raise Conflict("Selected contractor is hidden for this request")
            resolved_contractor_user_id = normalized_contractor_user_id

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
            prepared = await self._file_service.prepare_bytes(
                original_name=upload.original_name,
                content_bytes=upload.content_bytes,
                mime_type=upload.mime_type,
            )
            db_file = await self._file_service.create_offer_file(
                offer_id=offer.id,
                upload=prepared,
            )
            await self._offers.attach_file(offer_id=offer.id, file_id=db_file.id)

        return ManualOfferCreateResult(
            offer_id=offer.id,
            request_id=request.id,
            contractor_user_id=resolved_contractor_user_id,
            contractor_created=contractor_created,
        )

    async def get_workspace(self, *, current_user: CurrentUser, offer_id: int) -> OfferWorkspace:
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)
        OfferPolicy.ensure_can_access_offer_workspace(current_user, offer_owner_user_id=offer.id_user)

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
                created_at=request.created_at,
                updated_at=request.updated_at,
                closed_at=request.closed_at,
                files=request_file_items,
            ),
            offer=OfferWorkspaceOffer(
                offer_id=offer.id,
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
        upload: AttachmentFileInput,
    ) -> int:
        offer = await self._offers.get_by_id(offer_id=offer_id)
        if offer is None:
            raise NotFound("Offer not found")
        await self._ensure_request_visible_for_contractor(current_user=current_user, request_id=offer.id_request)
        request = await self._requests.get_by_id(request_id=offer.id_request)
        if request is None:
            raise NotFound("Request not found")
        offer_is_manual = await self._is_manual_offer(offer_owner_user_id=offer.id_user)

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
        elif has_permission(current_user, PermissionCodes.OFFERS_FILES_UPLOAD):
            OfferPolicy.ensure_can_manage_offer(
                current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )
        else:
            OfferPolicy.ensure_can_manage_manual_offer_files(
                current_user,
                request_owner_user_id=request.id_user,
                offer_is_manual=offer_is_manual,
            )

        if (
            current_user.role_id == settings.contractor_role_id
            and current_user.user_id == offer.id_user
            and offer.status in {"accepted", "rejected"}
        ):
            raise Conflict("Cannot edit files for finalized offer")

        prepared = await self._file_service.prepare_bytes(
            original_name=upload.original_name,
            content_bytes=upload.content_bytes,
            mime_type=upload.mime_type,
        )
        db_file = await self._file_service.create_offer_file(
            offer_id=offer.id,
            upload=prepared,
        )
        await self._offers.attach_file(offer_id=offer.id, file_id=db_file.id)
        return db_file.id

    async def remove_file(self, *, current_user: CurrentUser, offer_id: int, file_id: int) -> None:
        offer = await self._offers.get_by_id(offer_id=offer_id)
        if offer is None:
            raise NotFound("Offer not found")
        await self._ensure_request_visible_for_contractor(current_user=current_user, request_id=offer.id_request)
        request = await self._requests.get_by_id(request_id=offer.id_request)
        if request is None:
            raise NotFound("Request not found")
        offer_is_manual = await self._is_manual_offer(offer_owner_user_id=offer.id_user)

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
        elif has_permission(current_user, PermissionCodes.OFFERS_FILES_DELETE):
            OfferPolicy.ensure_can_manage_offer(
                current_user,
                offer_owner_user_id=offer.id_user,
                request_owner_user_id=request.id_user,
            )
        else:
            OfferPolicy.ensure_can_manage_manual_offer_files(
                current_user,
                request_owner_user_id=request.id_user,
                offer_is_manual=offer_is_manual,
            )

        detached = await self._offers.detach_file(offer_id=offer.id, file_id=file_id)
        if not detached:
            raise NotFound("File is not attached to offer")

        await self._file_service.delete_file(file_id=file_id)

    async def update_status(self, *, current_user: CurrentUser, offer_id: int, status: str) -> str:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_STATUS_UPDATE,
            message="Insufficient permissions to update offer status",
        )
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)

        if status not in EDITABLE_OFFER_STATUSES:
            raise Conflict("Unsupported offer status")

        is_contractor_deleting_own_offer = (
            current_user.role_id == settings.contractor_role_id
            and current_user.user_id == offer.id_user
            and status == "deleted"
        )

        if not is_contractor_deleting_own_offer:
            RequestPolicy.ensure_can_edit(current_user, request_owner_user_id=request.id_user)

        status_changed = offer.status != status
        await self._offers.update_status(offer=offer, status=status)

        if status_changed and status in {"accepted", "rejected"} and settings.telegram_legacy_enabled:
            tg_id = await self._users.get_active_approved_contractor_tg_id(
                user_id=offer.id_user,
                contractor_role_id=settings.contractor_role_id,
            )
            if tg_id is not None:
                await notify_offer_status_finalized(tg_id=tg_id)

        return offer.status

    async def update_amount(self, *, current_user: CurrentUser, offer_id: int, offer_amount: float) -> float:
        require_permission(
            current_user,
            PermissionCodes.OFFERS_UPDATE,
            message="Insufficient permissions to update offer",
        )
        offer, request = await self._load_offer_and_request(offer_id=offer_id, current_user=current_user)
        self._validate_offer_amount(offer_amount)

        OfferPolicy.ensure_can_manage_offer(
            current_user,
            offer_owner_user_id=offer.id_user,
            request_owner_user_id=request.id_user,
        )
        if (
            current_user.role_id == settings.contractor_role_id
            and current_user.user_id == offer.id_user
            and offer.status in {"accepted", "rejected"}
        ):
            raise Conflict("Cannot edit amount for finalized offer")

        await self._offers.update_amount(offer=offer, offer_amount=offer_amount)
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
        upload: AttachmentFileInput,
    ) -> UploadedMessageAttachment:
        require_permission(
            current_user,
            PermissionCodes.CHAT_MESSAGE_ATTACH,
            message="Insufficient permissions to attach files to chat messages",
        )
        await self._require_chat_context(current_user=current_user, offer_id=offer_id, require_send=True)
        prepared = await self._file_service.prepare_bytes(
            original_name=upload.original_name,
            content_bytes=upload.content_bytes,
            mime_type=upload.mime_type,
        )
        db_file = await self._file_service.create_chat_temp_file(
            offer_id=offer_id,
            upload=prepared,
        )
        return UploadedMessageAttachment(file_id=db_file.id, path=db_file.path, name=db_file.name)

    async def create_message(
        self,
        *,
        current_user: CurrentUser,
        offer_id: int,
        text: str,
        attachments: list[AttachmentFileInput] | None = None,
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
        if new_attachments or stored_file_refs:
            require_permission(
                current_user,
                PermissionCodes.CHAT_MESSAGE_ATTACH,
                message="Insufficient permissions to attach files to chat messages",
            )
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
            prepared = await self._file_service.prepare_bytes(
                original_name=attachment.original_name,
                content_bytes=attachment.content_bytes,
                mime_type=attachment.mime_type,
            )
            db_file = await self._file_service.create_chat_message_file(
                offer_id=offer.id,
                upload=prepared,
            )
            await self._messages.attach_file(message_id=message.id, file_id=db_file.id)
        for file_ref in stored_file_refs:
            db_file = await self._files.get_by_id(file_ref.file_id)
            if db_file is None:
                raise NotFound("File not found")
            await self._messages.attach_file(message_id=message.id, file_id=db_file.id)

        if current_user.user_id != offer.id_user and settings.telegram_legacy_enabled:
            tg_id = await self._users.get_active_approved_contractor_tg_id(
                user_id=offer.id_user,
                contractor_role_id=settings.contractor_role_id,
            )
            if tg_id is not None:
                await notify_new_message(tg_id=tg_id, request_id=request.id)

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

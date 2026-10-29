from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import Conflict
from app.models.auth_models import UserContactChannel
from app.repositories.profiles import ProfileRepository
from app.repositories.user_contact_channels import UserContactChannelRepository
from app.repositories.user_notification_preferences import UserNotificationPreferenceRepository

NOTIFICATION_CHANNEL_EMAIL = "email"
NOTIFICATION_MODE_CUSTOM = "custom"
NOTIFICATION_MODE_EMAIL_ONLY = "email_only"
NOTIFICATION_MODE_NONE = "none"
NOTIFICATION_MODES = frozenset({NOTIFICATION_MODE_EMAIL_ONLY, NOTIFICATION_MODE_NONE})
NOTIFICATION_TYPES = ("chat", "request", "offer", "system")
_INVALID_NOTIFICATION_VALUES = frozenset({"не указано", "none", "null"})
_EMAIL_REQUIRED_MESSAGE = "Добавьте email, чтобы включить email-уведомления"
_UNSUPPORTED_MODE_MESSAGE = "Неподдерживаемый режим уведомлений"
_UNSUPPORTED_TYPE_MESSAGE = "Неподдерживаемый тип уведомлений"
_UNSUPPORTED_CHANNEL_MESSAGE = "Неподдерживаемый канал уведомлений"


@dataclass(frozen=True, slots=True)
class NotificationTypePreferenceState:
    email: bool


@dataclass(frozen=True, slots=True)
class UserNotificationPreferencesState:
    mode: str
    email_available: bool
    email: str | None
    preferences: dict[str, NotificationTypePreferenceState]


@dataclass(frozen=True, slots=True)
class _PreferenceContext:
    email_channel: UserContactChannel | None
    email_available: bool
    email_value: str | None
    preferences_by_type: dict[str, NotificationTypePreferenceState]


class UserNotificationPreferencesService:
    def __init__(
        self,
        user_contact_channels: UserContactChannelRepository,
        user_notification_preferences: UserNotificationPreferenceRepository,
        *,
        profiles: ProfileRepository | None = None,
    ) -> None:
        self._user_contact_channels = user_contact_channels
        self._user_notification_preferences = user_notification_preferences
        self._profiles = profiles

    async def get_state(self, *, user_id: str) -> UserNotificationPreferencesState:
        return self._build_state_from_context(await self._load_context(user_id=user_id))

    async def update_mode(self, *, user_id: str, mode: str) -> UserNotificationPreferencesState:
        normalized_mode = self._normalize_mode(mode)
        context = await self._ensure_email_channel_for_preferences(
            context=await self._load_context(user_id=user_id),
            user_id=user_id,
        )
        email_enabled = normalized_mode == NOTIFICATION_MODE_EMAIL_ONLY
        self._ensure_email_available(context=context, required=email_enabled)
        await self._persist_preferences(
            context=context,
            preferences_by_type={
                notification_type: NotificationTypePreferenceState(email=email_enabled)
                for notification_type in NOTIFICATION_TYPES
            },
        )
        return self._build_state_from_context(
            await self._load_context(user_id=user_id),
            mode_override=normalized_mode,
        )

    async def update_preferences(
        self,
        *,
        user_id: str,
        preferences: dict[str, dict[str, bool | None]],
    ) -> UserNotificationPreferencesState:
        context = await self._load_context(user_id=user_id)
        normalized_preferences = self._normalize_preferences_payload(
            preferences=preferences,
            current_preferences=context.preferences_by_type,
        )
        if any(item.email for item in normalized_preferences.values()) or any(
            NOTIFICATION_CHANNEL_EMAIL in channel_values for channel_values in preferences.values()
        ):
            context = await self._ensure_email_channel_for_preferences(context=context, user_id=user_id)
        self._ensure_email_available(
            context=context,
            required=any(item.email for item in normalized_preferences.values()),
        )
        await self._persist_preferences(context=context, preferences_by_type=normalized_preferences)
        return self._build_state_from_context(await self._load_context(user_id=user_id))

    async def is_channel_enabled(
        self,
        *,
        user_id: str,
        channel_type: str,
        notification_type: str,
    ) -> bool:
        if channel_type.strip().lower() != NOTIFICATION_CHANNEL_EMAIL:
            return False
        normalized_notification_type = notification_type.strip().lower()
        if normalized_notification_type not in NOTIFICATION_TYPES:
            return False

        channel = await self._user_contact_channels.get_primary_by_type(
            user_id=user_id,
            channel_type=NOTIFICATION_CHANNEL_EMAIL,
            include_inactive=False,
        )
        if channel is None:
            return await self._has_profile_email(user_id=user_id)
        preference = await self._user_notification_preferences.get_by_channel_id_and_type(
            channel_id=channel.id,
            notification_type=normalized_notification_type,
        )
        return True if preference is None else preference.is_enabled

    async def _has_profile_email(self, *, user_id: str) -> bool:
        if self._profiles is None:
            return False
        profile = await self._profiles.get_by_id(user_id)
        return self._normalize_contact_value(profile.mail if profile is not None else None) is not None

    async def _ensure_email_channel_for_preferences(
        self,
        *,
        context: _PreferenceContext,
        user_id: str,
    ) -> _PreferenceContext:
        if context.email_channel is not None or context.email_value is None:
            return context
        email_channel = await self._user_contact_channels.upsert_channel(
            user_id=user_id,
            channel_type=NOTIFICATION_CHANNEL_EMAIL,
            channel_value=context.email_value,
            is_verified=False,
            is_primary=True,
        )
        if getattr(email_channel, "id", None) is None:
            await self._user_contact_channels.flush()
        return await self._load_context(user_id=user_id)

    async def _load_context(self, *, user_id: str) -> _PreferenceContext:
        channels = await self._user_contact_channels.list_by_user(
            user_id=user_id,
            channel_types=[NOTIFICATION_CHANNEL_EMAIL],
            include_inactive=True,
        )
        email_channel = next((item for item in channels if item.channel_type == NOTIFICATION_CHANNEL_EMAIL), None)

        profile_email: str | None = None
        if self._profiles is not None:
            profile = await self._profiles.get_by_id(user_id)
            profile_email = self._normalize_contact_value(profile.mail if profile is not None else None)
        channel_email = email_channel.channel_value if email_channel is not None and email_channel.is_active else None
        email_value = self._normalize_contact_value(profile_email or channel_email)
        email_available = email_value is not None

        channel_ids = [email_channel.id] if email_channel is not None and getattr(email_channel, "id", None) is not None else []
        stored_preferences = await self._user_notification_preferences.list_by_channel_ids(channel_ids=channel_ids)
        preference_map = {
            preference.notification_type: preference.is_enabled
            for preference in stored_preferences
            if email_channel is not None and preference.id_contact_channel == email_channel.id
        }
        preferences_by_type = {
            notification_type: NotificationTypePreferenceState(
                email=email_available and preference_map.get(notification_type, True)
            )
            for notification_type in NOTIFICATION_TYPES
        }
        return _PreferenceContext(
            email_channel=email_channel,
            email_available=email_available,
            email_value=email_value,
            preferences_by_type=preferences_by_type,
        )

    def _build_state_from_context(
        self,
        context: _PreferenceContext,
        *,
        mode_override: str | None = None,
    ) -> UserNotificationPreferencesState:
        return UserNotificationPreferencesState(
            mode=mode_override or self._resolve_mode(context=context),
            email_available=context.email_available,
            email=context.email_value,
            preferences=context.preferences_by_type,
        )

    def _normalize_mode(self, mode: str) -> str:
        normalized_mode = mode.strip().lower()
        if normalized_mode not in NOTIFICATION_MODES:
            raise Conflict(_UNSUPPORTED_MODE_MESSAGE)
        return normalized_mode

    def _resolve_mode(self, *, context: _PreferenceContext) -> str:
        values = {item.email for item in context.preferences_by_type.values()}
        if len(values) > 1:
            return NOTIFICATION_MODE_CUSTOM
        return NOTIFICATION_MODE_EMAIL_ONLY if context.email_available and next(iter(values), False) else NOTIFICATION_MODE_NONE

    def _normalize_preferences_payload(
        self,
        *,
        preferences: dict[str, dict[str, bool | None]],
        current_preferences: dict[str, NotificationTypePreferenceState],
    ) -> dict[str, NotificationTypePreferenceState]:
        if set(preferences) - set(NOTIFICATION_TYPES):
            raise Conflict(_UNSUPPORTED_TYPE_MESSAGE)
        normalized = dict(current_preferences)
        for notification_type, channel_values in preferences.items():
            if set(channel_values) - {NOTIFICATION_CHANNEL_EMAIL}:
                raise Conflict(_UNSUPPORTED_CHANNEL_MESSAGE)
            current_value = current_preferences[notification_type]
            normalized[notification_type] = NotificationTypePreferenceState(
                email=current_value.email
                if channel_values.get(NOTIFICATION_CHANNEL_EMAIL) is None
                else bool(channel_values[NOTIFICATION_CHANNEL_EMAIL])
            )
        return normalized

    async def _persist_preferences(
        self,
        *,
        context: _PreferenceContext,
        preferences_by_type: dict[str, NotificationTypePreferenceState],
    ) -> None:
        if context.email_channel is None:
            return
        for notification_type, notification_state in preferences_by_type.items():
            await self._user_notification_preferences.upsert(
                channel_id=context.email_channel.id,
                notification_type=notification_type,
                is_enabled=notification_state.email,
            )

    def _ensure_email_available(self, *, context: _PreferenceContext, required: bool) -> None:
        if required and not context.email_available:
            raise Conflict(_EMAIL_REQUIRED_MESSAGE)

    @staticmethod
    def _normalize_contact_value(value: str | None) -> str | None:
        normalized = (value or "").strip()
        if not normalized or normalized.lower() in _INVALID_NOTIFICATION_VALUES:
            return None
        return normalized

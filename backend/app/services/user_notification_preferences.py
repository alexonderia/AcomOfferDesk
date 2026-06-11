from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import Conflict
from app.models.auth_models import UserContactChannel
from app.repositories.profiles import ProfileRepository
from app.repositories.user_contact_channels import UserContactChannelRepository
from app.repositories.user_notification_preferences import UserNotificationPreferenceRepository

NOTIFICATION_CHANNEL_EMAIL = "email"
NOTIFICATION_CHANNEL_MAX = "max"
NOTIFICATION_MODE_ALL = "all"
NOTIFICATION_MODE_EMAIL_ONLY = "email_only"
NOTIFICATION_MODE_MAX_ONLY = "max_only"
NOTIFICATION_MODE_NONE = "none"
NOTIFICATION_MODES = frozenset(
    {
        NOTIFICATION_MODE_ALL,
        NOTIFICATION_MODE_EMAIL_ONLY,
        NOTIFICATION_MODE_MAX_ONLY,
        NOTIFICATION_MODE_NONE,
    }
)
NOTIFICATION_TYPES = ("chat", "request", "offer", "system")
_INVALID_NOTIFICATION_VALUES = frozenset({"не указано", "none", "null"})


@dataclass(frozen=True, slots=True)
class UserNotificationPreferencesState:
    mode: str
    email_available: bool
    max_available: bool
    email: str | None
    max_user_id: str | None


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
        context = await self._load_context(user_id=user_id)
        return self._build_state_from_context(context)

    async def update_mode(self, *, user_id: str, mode: str) -> UserNotificationPreferencesState:
        normalized_mode = self._normalize_mode(mode)
        context = await self._load_context(user_id=user_id)
        context = await self._ensure_email_channel_for_preferences(context=context, user_id=user_id)

        email_enabled = normalized_mode in {NOTIFICATION_MODE_ALL, NOTIFICATION_MODE_EMAIL_ONLY}
        max_enabled = normalized_mode in {NOTIFICATION_MODE_ALL, NOTIFICATION_MODE_MAX_ONLY}

        if email_enabled and not context.email_available:
            raise Conflict("Добавьте email, чтобы включить email-уведомления")
        if max_enabled and not context.max_available:
            raise Conflict("Сначала привяжите подтверждённый MAX, чтобы включить MAX-уведомления")

        for channel in filter(None, (context.email_channel, context.max_channel)):
            channel_enabled = (
                email_enabled if channel.channel_type == NOTIFICATION_CHANNEL_EMAIL else max_enabled
            )
            for notification_type in NOTIFICATION_TYPES:
                await self._user_notification_preferences.upsert(
                    channel_id=channel.id,
                    notification_type=notification_type,
                    is_enabled=channel_enabled,
                )

        return self._build_state_from_context(context, mode_override=normalized_mode)

    async def is_channel_enabled(
        self,
        *,
        user_id: str,
        channel_type: str,
        notification_type: str,
    ) -> bool:
        normalized_channel_type = channel_type.strip().lower()
        normalized_notification_type = notification_type.strip().lower()
        if normalized_channel_type not in {NOTIFICATION_CHANNEL_EMAIL, NOTIFICATION_CHANNEL_MAX}:
            return False
        if normalized_notification_type not in NOTIFICATION_TYPES:
            return False

        if normalized_channel_type == NOTIFICATION_CHANNEL_EMAIL:
            channel = await self._user_contact_channels.get_primary_by_type(
                user_id=user_id,
                channel_type=NOTIFICATION_CHANNEL_EMAIL,
                include_inactive=False,
            )
            if channel is None:
                return await self._has_profile_email(user_id=user_id)
        else:
            channel = await self._user_contact_channels.get_primary_by_type(
                user_id=user_id,
                channel_type=NOTIFICATION_CHANNEL_MAX,
                include_inactive=False,
            )
            if channel is None or not channel.is_verified:
                return False

        preference = await self._user_notification_preferences.get_by_channel_id_and_type(
            channel_id=channel.id,
            notification_type=normalized_notification_type,
        )
        if preference is None:
            return True
        return preference.is_enabled

    async def _has_profile_email(self, *, user_id: str) -> bool:
        if self._profiles is None:
            return False
        profile = await self._profiles.get_by_id(user_id)
        return self._normalize_contact_value(profile.mail if profile is not None else None) is not None

    async def _ensure_email_channel_for_preferences(
        self,
        *,
        context: "_PreferenceContext",
        user_id: str,
    ) -> "_PreferenceContext":
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

    async def _load_context(self, *, user_id: str) -> "_PreferenceContext":
        channels = await self._user_contact_channels.list_by_user(
            user_id=user_id,
            channel_types=[NOTIFICATION_CHANNEL_EMAIL, NOTIFICATION_CHANNEL_MAX],
            include_inactive=True,
        )
        email_channel = next((item for item in channels if item.channel_type == NOTIFICATION_CHANNEL_EMAIL), None)
        max_channel = next((item for item in channels if item.channel_type == NOTIFICATION_CHANNEL_MAX), None)

        profile_email: str | None = None
        if self._profiles is not None:
            profile = await self._profiles.get_by_id(user_id)
            profile_email = self._normalize_contact_value(profile.mail if profile is not None else None)

        email_channel_value = (
            email_channel.channel_value
            if email_channel is not None and email_channel.is_active
            else None
        )
        email_value = self._normalize_contact_value(profile_email or email_channel_value)
        max_value = self._normalize_contact_value(max_channel.channel_value if max_channel is not None else None)

        email_available = email_value is not None
        max_available = bool(
            max_channel is not None
            and max_channel.is_active
            and max_channel.is_verified
            and max_value is not None
        )

        channel_ids = [
            channel.id
            for channel in (email_channel, max_channel)
            if channel is not None and getattr(channel, "id", None) is not None
        ]
        preferences = await self._user_notification_preferences.list_by_channel_ids(channel_ids=channel_ids)
        preference_map = {
            (preference.id_contact_channel, preference.notification_type): preference.is_enabled
            for preference in preferences
        }

        email_enabled = self._resolve_channel_enabled(
            channel=email_channel,
            available=email_available,
            preference_map=preference_map,
        )
        max_enabled = self._resolve_channel_enabled(
            channel=max_channel,
            available=max_available,
            preference_map=preference_map,
        )

        return _PreferenceContext(
            email_channel=email_channel,
            max_channel=max_channel,
            email_available=email_available,
            max_available=max_available,
            email_value=email_value,
            max_value=max_value,
            email_enabled=email_enabled,
            max_enabled=max_enabled,
        )

    def _build_state_from_context(
        self,
        context: "_PreferenceContext",
        *,
        mode_override: str | None = None,
    ) -> UserNotificationPreferencesState:
        mode = mode_override or self._resolve_mode(
            email_available=context.email_available,
            email_enabled=context.email_enabled,
            max_available=context.max_available,
            max_enabled=context.max_enabled,
        )
        return UserNotificationPreferencesState(
            mode=mode,
            email_available=context.email_available,
            max_available=context.max_available,
            email=context.email_value,
            max_user_id=context.max_value,
        )

    def _normalize_mode(self, mode: str) -> str:
        normalized_mode = mode.strip().lower()
        if normalized_mode not in NOTIFICATION_MODES:
            raise Conflict("Неподдерживаемый режим уведомлений")
        return normalized_mode

    def _resolve_mode(
        self,
        *,
        email_available: bool,
        email_enabled: bool,
        max_available: bool,
        max_enabled: bool,
    ) -> str:
        if email_available and email_enabled and max_available and max_enabled:
            return NOTIFICATION_MODE_ALL
        if email_available and email_enabled and not (max_available and max_enabled):
            return NOTIFICATION_MODE_EMAIL_ONLY
        if max_available and max_enabled and not (email_available and email_enabled):
            return NOTIFICATION_MODE_MAX_ONLY
        return NOTIFICATION_MODE_NONE

    def _resolve_channel_enabled(
        self,
        *,
        channel: UserContactChannel | None,
        available: bool,
        preference_map: dict[tuple[int, str], bool],
    ) -> bool:
        if not available:
            return False
        if channel is None or getattr(channel, "id", None) is None:
            return True

        values = [
            preference_map[(channel.id, notification_type)]
            for notification_type in NOTIFICATION_TYPES
            if (channel.id, notification_type) in preference_map
        ]
        if not values:
            return True
        return any(values)

    def _normalize_contact_value(self, value: str | None) -> str | None:
        normalized = (value or "").strip()
        if not normalized or normalized.lower() in _INVALID_NOTIFICATION_VALUES:
            return None
        return normalized


@dataclass(frozen=True, slots=True)
class _PreferenceContext:
    email_channel: UserContactChannel | None
    max_channel: UserContactChannel | None
    email_available: bool
    max_available: bool
    email_value: str | None
    max_value: str | None
    email_enabled: bool
    max_enabled: bool

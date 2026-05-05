from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserAuthAccount(Base):
    __tablename__ = "user_auth_accounts"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('keycloak', 'telegram', 'max', 'phone', 'email')",
            name="user_auth_accounts_provider_chk",
        ),
        CheckConstraint(
            "btrim(external_subject_id) <> ''",
            name="user_auth_accounts_subject_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_user: Mapped[str] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    external_subject_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    linked_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    last_login_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)


class UserContactChannel(Base):
    __tablename__ = "user_contact_channels"
    __table_args__ = (
        CheckConstraint(
            "channel_type IN ('email', 'phone', 'telegram', 'max')",
            name="user_contact_channels_type_chk",
        ),
        CheckConstraint(
            "btrim(channel_value) <> ''",
            name="user_contact_channels_value_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_user: Mapped[str] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel_type: Mapped[str] = mapped_column(Text, nullable=False)
    channel_value: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    verified_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"
    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('chat', 'request', 'offer', 'system')",
            name="user_notification_preferences_type_chk",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_contact_channel: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_contact_channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(Text, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

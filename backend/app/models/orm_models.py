from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    TIMESTAMP,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, query_expression, relationship

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    role: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


@dataclass(slots=True)
class TgUser:
    id: int
    status: str



class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active','inactive','review','blacklist')",
            name="users_status_check",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    password_hash: Mapped[Optional[str]] = query_expression()
    id_role: Mapped[int] = mapped_column(SmallInteger, ForeignKey("roles.id"), nullable=False)
    id_parent: Mapped[Optional[str]] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="review")
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    tg_user_id: Mapped[Optional[int]] = query_expression()
    profile: Mapped[Optional[Profile]] = relationship(
        "Profile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    company_contact: Mapped[Optional[CompanyContact]] = relationship(
        "CompanyContact",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="profile")


class CompanyContact(Base):
    __tablename__ = "company_contacts"

    id: Mapped[str] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    inn: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="company_contact")


class StorageObject(Base):
    __tablename__ = "storage_objects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    storage_bucket: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    content_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    files: Mapped[list["File"]] = relationship("File", back_populates="storage_object")


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_storage_object: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("storage_objects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    storage_object: Mapped[StorageObject] = relationship("StorageObject", back_populates="files", lazy="joined")

    @property
    def path(self) -> str:
        return self.storage_object.storage_key

    @property
    def name(self) -> str:
        return self.original_name

    @property
    def storage_bucket(self) -> str:
        return self.storage_object.storage_bucket

    @property
    def storage_key(self) -> str:
        return self.storage_object.storage_key

    @property
    def content_sha256(self) -> str:
        return self.storage_object.content_sha256

    @property
    def mime_type(self) -> str:
        return self.storage_object.mime_type

    @property
    def size_bytes(self) -> int:
        return self.storage_object.size_bytes


class Request(Base):
    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','review','closed','cancelled')",
            name="requests_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="open")
    deadline_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    closed_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)
    
    id_offer: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    id_plan: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("economy_plans.id", ondelete="SET NULL"),
        nullable=True,
    )

    id_user: Mapped[str] = mapped_column(Text, ForeignKey("users.id"), nullable=False)
    initial_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    final_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    offers: Mapped[list["Offer"]] = relationship(
        "Offer",
        back_populates="request",
        foreign_keys="Offer.id_request",
        cascade="all, delete-orphan",
    )

    chosen_offer: Mapped[Optional["Offer"]] = relationship(
        "Offer",
        foreign_keys=[id_offer],
        post_update=True,
    )
    hidden_contractors: Mapped[list["RequestHiddenContractor"]] = relationship(
        "RequestHiddenContractor",
        back_populates="request",
        cascade="all, delete-orphan",
    )


class RequestHiddenContractor(Base):
    __tablename__ = "request_hidden_contractors"

    request_id: Mapped[int] = mapped_column(
        "id_request",
        BigInteger,
        ForeignKey("requests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    contractor_user_id: Mapped[str] = mapped_column(
        "id_user",
        Text,
        ForeignKey("users.id"),
        primary_key=True,
    )

    request: Mapped["Request"] = relationship("Request", back_populates="hidden_contractors")


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('submitted','deleted','accepted','rejected')",
            name="offers_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_request: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="CASCADE"),
    )
    id_user: Mapped[str] = mapped_column(Text, ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="submitted")
    offer_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    request: Mapped["Request"] = relationship(
        "Request",
        back_populates="offers",
        foreign_keys=[id_request],
    )
    chat: Mapped[Optional[Chat]] = relationship("Chat", back_populates="offer", uselist=False)


class RequestOfferStats(Base):
    __tablename__ = "request_offer_stats"

    request_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    count_submitted: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    count_deleted_alert: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    count_accepted_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    count_rejected_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("offers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_message_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_message_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    offer: Mapped[Offer] = relationship("Offer", back_populates="chat")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="chat",
        foreign_keys="Message.id_chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    last_message: Mapped[Optional["Message"]] = relationship(
        "Message",
        foreign_keys=[last_message_id],
        post_update=True,
        uselist=False,
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "type IN ('text', 'system', 'file', 'mixed', 'email')",
            name="messages_type_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_chat: Mapped[int] = mapped_column(BigInteger, ForeignKey("chats.id", ondelete="CASCADE"))
    id_user: Mapped[str] = mapped_column(Text, ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False, default="text")
    reply_to_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages",
        foreign_keys=[id_chat],
    )


class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id_chat: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chats.id", ondelete="CASCADE"),
        primary_key=True,
    )
    id_user: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    left_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)
    last_read_message_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_read_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    is_muted: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    is_archived: Mapped[bool] = mapped_column(nullable=False, server_default="false")


class MessageReceipt(Base):
    __tablename__ = "message_receipts"

    id_message: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("messages.id", ondelete="CASCADE"),
        primary_key=True,
    )
    id_user: Mapped[str] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    delivered_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)
    read_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)


class RequestFile(Base):
    __tablename__ = "request_files"

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey("files.id", ondelete="RESTRICT"), primary_key=True)
    id_request: Mapped[int] = mapped_column(BigInteger, ForeignKey("requests.id", ondelete="CASCADE"))


class OfferFile(Base):
    __tablename__ = "offer_files"

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey("files.id", ondelete="RESTRICT"), primary_key=True)
    id_offer: Mapped[int] = mapped_column(BigInteger, ForeignKey("offers.id", ondelete="CASCADE"))


class MessageFile(Base):
    __tablename__ = "message_files"

    id: Mapped[int] = mapped_column(BigInteger, ForeignKey("files.id", ondelete="RESTRICT"), primary_key=True)
    id_message: Mapped[int] = mapped_column(BigInteger, ForeignKey("messages.id", ondelete="CASCADE"))


class NormativeFile(Base):
    __tablename__ = "normative_files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_file: Mapped[int] = mapped_column(BigInteger, ForeignKey("files.id", ondelete="RESTRICT"), nullable=False)


class FeedBack(Base):
    __tablename__ = "feed_back"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class UserStatusPeriod(Base):
    __tablename__ = "user_status_periods"
    __table_args__ = (
        CheckConstraint(
            "status IN ('sick', 'vacation', 'fired', 'maternity', 'business_trip', 'unavailable')",
            name="user_status_periods_status_check",
        ),
        CheckConstraint("ended_at >= started_at", name="user_status_periods_period_chk"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_user: Mapped[str] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    ended_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)


class EconomyPlan(Base):
    __tablename__ = "economy_plans"
    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="economy_plans_period_chk"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_parent_plan: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("economy_plans.id", ondelete="RESTRICT"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    id_user: Mapped[str] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    id_parent_user_snapshot: Mapped[str | None] = mapped_column(
        Text,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    plan_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    fact_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

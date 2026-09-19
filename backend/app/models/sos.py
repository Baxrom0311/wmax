from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

SosSourceEnum = ENUM(
    "watch_button", "phone_app", "relative_portal", "auto_critical",
    name="sos_source", create_type=False
)

SosStatusEnum = ENUM(
    "raised", "acknowledged", "dispatched", "resolved", "false_alarm", "cancelled",
    name="sos_status", create_type=False
)

ActorKindEnum = ENUM(
    "patient", "relative", "doctor", "nurse", "admin", "dispatcher", "system",
    name="actor_kind", create_type=False
)


class SosEvent(Base):
    __tablename__ = "sos_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[Literal["watch_button", "phone_app", "relative_portal", "auto_critical"]] = mapped_column(
        SosSourceEnum, nullable=False
    )
    status: Mapped[Literal["raised", "acknowledged", "dispatched", "resolved", "false_alarm", "cancelled"]] = mapped_column(
        SosStatusEnum, nullable=False, default="raised"
    )
    raised_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    address_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    clinical_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    vitals_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    device_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatch_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispatch_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient = relationship("Patient", back_populates="sos_events")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by], lazy="selectin")
    resolver = relationship("User", foreign_keys=[resolved_by], lazy="selectin")
    notifications = relationship("SosNotification", back_populates="sos_event", cascade="all, delete-orphan")


class SosNotification(Base):
    __tablename__ = "sos_notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sos_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False
    )
    recipient_kind: Mapped[str] = mapped_column(ActorKindEnum, nullable=False)
    recipient_ref: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    sos_event = relationship("SosEvent", back_populates="notifications")

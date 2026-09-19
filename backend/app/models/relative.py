from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, SmallInteger, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.models.base import Base


class Relative(Base):
    __tablename__ = "relatives"
    __table_args__ = (
        UniqueConstraint("phone", "patient_id", name="uq_relative_patient"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    relationship: Mapped[str] = mapped_column(
        Text, nullable=False, default="qarindoshi"
    )
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    pin_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    is_emergency_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contact_priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=10)
    can_edit_profile: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient = orm_relationship("Patient", back_populates="relatives", lazy="selectin")

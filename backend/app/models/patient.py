from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import CHAR, Date, DateTime, ForeignKey, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

PatientPhaseEnum = ENUM(
    "calib", "learning", "full", name="patient_phase", create_type=False
)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    sex: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[str] = mapped_column(Text, nullable=False)
    discharge_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phase: Mapped[Literal["calib", "learning", "full"]] = mapped_column(
        PatientPhaseEnum, nullable=False, default="calib"
    )
    phase_since: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    baseline_approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    baseline_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    nurse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    device_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    doctor = relationship("User", foreign_keys=[doctor_id], lazy="selectin")
    nurse = relationship("User", foreign_keys=[nurse_id], lazy="selectin")

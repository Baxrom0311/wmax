from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

ConditionKindEnum = ENUM(
    "primary", "comorbidity", "past",
    name="condition_kind", create_type=False
)


class PatientCondition(Base):
    __tablename__ = "patient_conditions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    icd10: Mapped[str] = mapped_column(Text, nullable=False)
    name_uz: Mapped[str] = mapped_column(Text, nullable=False)
    name_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[Literal["primary", "comorbidity", "past"]] = mapped_column(
        ConditionKindEnum, nullable=False, default="comorbidity"
    )
    severity_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient = relationship("Patient", back_populates="conditions")
    doctor = relationship("User", foreign_keys=[recorded_by], lazy="selectin")

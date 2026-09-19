from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

AllergySeverityEnum = ENUM(
    "mild", "moderate", "severe", "anaphylaxis",
    name="allergy_severity", create_type=False
)


class PatientAllergy(Base):
    __tablename__ = "patient_allergies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    substance: Mapped[str] = mapped_column(Text, nullable=False)
    reaction: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[Literal["mild", "moderate", "severe", "anaphylaxis"]] = mapped_column(
        AllergySeverityEnum, nullable=False, default="moderate"
    )
    noted_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient = relationship("Patient", back_populates="allergies")

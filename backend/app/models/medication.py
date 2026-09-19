from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PatientMedication(Base):
    __tablename__ = "patient_medications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    atc_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    dose: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[str] = mapped_column(Text, nullable=False)
    route: Mapped[str | None] = mapped_column(Text, nullable=True, default="oral")
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    stopped_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    stop_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescribed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    affects_params: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    patient = relationship("Patient", back_populates="medications")
    prescriber = relationship("User", foreign_keys=[prescribed_by], lazy="selectin")

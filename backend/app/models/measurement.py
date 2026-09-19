from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

ActorKindEnum = ENUM(
    "patient", "relative", "doctor", "nurse", "admin", "dispatcher", "system",
    name="actor_kind", create_type=False
)


class PatientMeasurement(Base):
    __tablename__ = "patient_measurements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    sbp_mmhg: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    dbp_mmhg: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    glucose_mmol: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(ActorKindEnum, nullable=False, default="patient")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient = relationship("Patient", back_populates="measurements")

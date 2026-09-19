from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PatientRiskFactor(Base):
    __tablename__ = "patient_risk_factors"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True
    )
    smoking: Mapped[str | None] = mapped_column(Text, nullable=True)
    smoking_pack_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    alcohol: Mapped[str | None] = mapped_column(Text, nullable=True)
    diabetes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hypertension: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ckd: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    physical_activity: Mapped[str | None] = mapped_column(Text, nullable=True)
    lives_alone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mobility: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    patient = relationship("Patient", back_populates="risk_factors")

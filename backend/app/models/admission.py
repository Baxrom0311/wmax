from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

AdmissionOutcomeEnum = ENUM(
    "discharged", "transferred", "deceased", "ongoing",
    name="admission_outcome", create_type=False
)


class PatientAdmission(Base):
    __tablename__ = "patient_admissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    hospital_name: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str | None] = mapped_column(Text, nullable=True)
    admitted_at: Mapped[date] = mapped_column(Date, nullable=False)
    discharged_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reason_icd10: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[Literal["discharged", "transferred", "deceased", "ongoing"]] = mapped_column(
        AdmissionOutcomeEnum, nullable=False, default="discharged"
    )
    was_readmission: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    predicted_by_alert_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True
    )
    discharge_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient = relationship("Patient", back_populates="admissions")
    predicted_by_alert = relationship("Alert", foreign_keys=[predicted_by_alert_id], lazy="selectin")

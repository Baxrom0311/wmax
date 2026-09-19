from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import BigInteger, CHAR, Date, DateTime, ForeignKey, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

PatientPhaseEnum = ENUM(
    "calib", "learning", "full", name="patient_phase", create_type=False
)
BloodGroupEnum = ENUM(
    "O", "A", "B", "AB", name="blood_group", create_type=False
)
RhFactorEnum = ENUM(
    "pos", "neg", name="rh_factor", create_type=False
)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    device_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    # V2 profile and credentials
    phone: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    pin_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    primary_icd10: Mapped[str | None] = mapped_column(Text, nullable=True)
    # patients <-> patient_addresses is a genuine FK cycle (a patient points at
    # its primary address; every address points back at its patient). use_alter
    # emits this constraint as a separate ALTER after both tables exist, which
    # is also what lets Alembic order the initial migration at all.
    primary_address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "patient_addresses.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_patients_primary_address",
        ),
        nullable=True,
    )
    blood_group: Mapped[Literal["O", "A", "B", "AB"] | None] = mapped_column(
        BloodGroupEnum, nullable=True
    )
    rh: Mapped[Literal["pos", "neg"] | None] = mapped_column(
        RhFactorEnum, nullable=True
    )
    preferred_lang: Mapped[str] = mapped_column(Text, nullable=False, server_default="uz", default="uz")
    profile_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    doctor = relationship("User", foreign_keys=[doctor_id], lazy="selectin")
    nurse = relationship("User", foreign_keys=[nurse_id], lazy="selectin")
    primary_address = relationship("PatientAddress", foreign_keys=[primary_address_id], lazy="selectin", post_update=True)
    addresses = relationship("PatientAddress", back_populates="patient", cascade="all, delete-orphan", foreign_keys="PatientAddress.patient_id")
    conditions = relationship("PatientCondition", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("PatientMedication", back_populates="patient", cascade="all, delete-orphan")
    allergies = relationship("PatientAllergy", back_populates="patient", cascade="all, delete-orphan")
    measurements = relationship("PatientMeasurement", back_populates="patient", cascade="all, delete-orphan")
    risk_factors = relationship("PatientRiskFactor", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    admissions = relationship("PatientAdmission", back_populates="patient", cascade="all, delete-orphan")
    sos_events = relationship("SosEvent", back_populates="patient", cascade="all, delete-orphan")
    relatives = relationship("Relative", back_populates="patient", cascade="all, delete-orphan")

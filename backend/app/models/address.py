from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

AddressKindEnum = ENUM(
    "home", "temporary", "work", "other",
    name="address_kind", create_type=False
)


class PatientAddress(Base):
    __tablename__ = "patient_addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[Literal["home", "temporary", "work", "other"]] = mapped_column(
        AddressKindEnum, nullable=False, default="home"
    )
    region: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[str] = mapped_column(Text, nullable=False)
    mahalla: Mapped[str | None] = mapped_column(Text, nullable=True)
    street: Mapped[str | None] = mapped_column(Text, nullable=True)
    house: Mapped[str | None] = mapped_column(Text, nullable=True)
    flat: Mapped[str | None] = mapped_column(Text, nullable=True)
    landmark: Mapped[str | None] = mapped_column(Text, nullable=True)
    entrance_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    geo_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    geo_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    patient = relationship("Patient", back_populates="addresses", foreign_keys=[patient_id])

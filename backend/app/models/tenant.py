from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import Boolean, DateTime, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.invoice import Invoice
    from app.models.subscription import Subscription

TenantKindEnum = ENUM(
    "household", "clinic", "ovabmu", "polyclinic", "network",
    name="tenant_kind",
    create_type=False,
)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kind: Mapped[Literal["household", "clinic", "ovabmu", "polyclinic", "network"]] = mapped_column(
        TenantKindEnum, nullable=False, default="household"
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    legal_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    tax_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str] = mapped_column(Text, nullable=False, default="Xorazm")
    district: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    subscription: Mapped[Subscription | None] = relationship(
        "Subscription", back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )
    invoices: Mapped[list[Invoice]] = relationship(
        "Invoice", back_populates="tenant", cascade="all, delete-orphan"
    )
    devices: Mapped[list[Device]] = relationship(
        "Device", back_populates="tenant"
    )

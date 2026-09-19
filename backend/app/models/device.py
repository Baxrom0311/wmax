from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import DateTime, ForeignKey, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.device_assignment import DeviceAssignment
    from app.models.tenant import Tenant

DeviceTierEnum = ENUM(
    "tier1_wearos", "tier2_wearos_budget", "tier3_ble_band",
    name="device_tier",
    create_type=False,
)
DeviceStatusEnum = ENUM(
    "in_stock", "assigned", "active", "returning", "maintenance", "lost", "retired",
    name="device_status",
    create_type=False,
)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    serial_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[Literal["tier1_wearos", "tier2_wearos_budget", "tier3_ble_band"]] = mapped_column(
        DeviceTierEnum, nullable=False, default="tier1_wearos"
    )
    status: Mapped[Literal["in_stock", "assigned", "active", "returning", "maintenance", "lost", "retired"]] = mapped_column(
        DeviceStatusEnum, nullable=False, default="in_stock"
    )
    ownership: Mapped[str] = mapped_column(Text, nullable=False, default="owned")
    battery_health_pct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tenant: Mapped[Tenant | None] = relationship("Tenant", back_populates="devices")
    assignments: Mapped[list[DeviceAssignment]] = relationship(
        "DeviceAssignment", back_populates="device", cascade="all, delete-orphan"
    )

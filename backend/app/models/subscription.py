from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant

PlanCodeEnum = ENUM(
    "free", "premium", "premium_doc", "clinic",
    name="plan_code",
    create_type=False,
)
SubStatusEnum = ENUM(
    "trialing", "active", "past_due", "canceled", "free",
    name="sub_status",
    create_type=False,
)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    plan: Mapped[Literal["free", "premium", "premium_doc", "clinic"]] = mapped_column(
        PlanCodeEnum, nullable=False, default="free"
    )
    status: Mapped[Literal["trialing", "active", "past_due", "canceled", "free"]] = mapped_column(
        SubStatusEnum, nullable=False, default="trialing"
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seats_included: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    card_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="subscription")

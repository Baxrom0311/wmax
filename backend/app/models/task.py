from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

TaskTypeEnum = ENUM("active_call", "red_alert", name="task_type", create_type=False)
TaskStatusEnum = ENUM(
    "created", "sent", "seen", "done", "overdue", name="task_status", create_type=False
)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    type: Mapped[Literal["active_call", "red_alert"]] = mapped_column(
        TaskTypeEnum, nullable=False
    )
    status: Mapped[Literal["created", "sent", "seen", "done", "overdue"]] = (
        mapped_column(TaskStatusEnum, nullable=False, default="created")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reminded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("alerts.id"), nullable=True
    )

    patient = relationship("Patient", lazy="selectin")
    doctor = relationship("User", lazy="selectin")
    alert = relationship("Alert", lazy="selectin")

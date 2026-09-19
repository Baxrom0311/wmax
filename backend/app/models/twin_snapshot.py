from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TwinSnapshot(Base):
    __tablename__ = "twin_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ai_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])

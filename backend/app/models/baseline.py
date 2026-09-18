from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

BaselineParamEnum = ENUM(
    "hr_mean",
    "rmssd",
    "spo2",
    "skin_temp",
    "sleep_frag",
    "steps",
    "rr_est",
    name="baseline_param",
    create_type=False,
)


class Baseline(Base):
    __tablename__ = "baselines"
    __table_args__ = (
        UniqueConstraint("patient_id", "param", "time_window", name="uq_baseline"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    param: Mapped[
        Literal[
            "hr_mean",
            "rmssd",
            "spo2",
            "skin_temp",
            "sleep_frag",
            "steps",
            "rr_est",
        ]
    ] = mapped_column(BaselineParamEnum, nullable=False)
    time_window: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    median: Mapped[float] = mapped_column(Float, nullable=False)
    mad: Mapped[float] = mapped_column(Float, nullable=False)
    n_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    patient = relationship("Patient", lazy="selectin")

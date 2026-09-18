from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AlertLevel


class Alert(BaseModel):
    id: int
    ts: datetime
    level: AlertLevel
    composite_score: float
    triggered_params: dict[str, float] = {}
    anomaly_score: float | None = None
    reason: str | None = None

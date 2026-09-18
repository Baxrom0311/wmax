from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import TrendDirection


class Trend(BaseModel):
    slope: float
    direction: TrendDirection
    recommendation_key: str
    days_used: int

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SeriesPoint(BaseModel):
    ts: datetime
    value: float | None = None


class DeviatedRange(BaseModel):
    from_ts: datetime = Field(..., alias="from")
    to_ts: datetime = Field(..., alias="to")

    model_config = {"populate_by_name": True}


class ParamSeries(BaseModel):
    param: str
    points: list[SeriesPoint]
    baseline_median: float | None = None
    baseline_low: float | None = None
    baseline_high: float | None = None
    deviated_ranges: list[dict[str, datetime]] = []

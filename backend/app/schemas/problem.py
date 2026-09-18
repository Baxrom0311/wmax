from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ProblemItem(BaseModel):
    param: str
    label: str
    deviation: str
    current_value: float
    baseline_range: str
    severity: Literal["mild", "moderate", "severe"]
    explanation: str


class PrognosisInfo(BaseModel):
    risk_level: Literal["low", "moderate", "high"]
    risk_probability_pct: int
    early_warning_hours: int
    summary: str
    recommendation: str

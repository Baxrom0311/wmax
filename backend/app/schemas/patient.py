from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.alert import Alert
from app.schemas.common import AlertLevel, Phase
from app.schemas.problem import ProblemItem, PrognosisInfo
from app.schemas.series import ParamSeries
from app.schemas.task import Task
from app.schemas.trend import Trend


class PatientSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    age: int
    sex: Literal["m", "f"]
    diagnosis: str
    district: str
    phase: Phase
    level: AlertLevel
    composite_score: float
    triggered_params: dict[str, float] = {}
    trend: Trend
    last_reading_at: datetime | None = None
    open_task: Task | None = None


class PatientDetail(PatientSummary):
    series: list[ParamSeries] = []
    alerts: list[Alert] = []
    tasks: list[Task] = []
    baseline_approved: bool = False
    prognosis: PrognosisInfo | None = None
    problems: list[ProblemItem] | None = None

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.alert import Alert
from app.schemas.common import AlertLevel, Role
from app.schemas.problem import ProblemItem, PrognosisInfo
from app.schemas.series import ParamSeries
from app.schemas.task import Task
from app.schemas.trend import Trend


class RelativePatientItem(BaseModel):
    id: uuid.UUID
    full_name: str
    relationship: str
    access_token: str
    level: AlertLevel
    diagnosis: str
    age: int
    last_reading_at: datetime | None = None


class DoctorContact(BaseModel):
    name: str
    phone: str


class RelativeVitals(BaseModel):
    hr: float | None = None
    spo2: float | None = None
    sleep_hours: float | None = None
    skin_temp: float | None = None
    rr: float | None = None
    steps: int | None = None


class RelativeView(BaseModel):
    patient_id: uuid.UUID
    patient_name: str
    relationship: str | None = None
    level: AlertLevel
    level_word_key: str
    composite_score: float
    last_reading_at: datetime | None = None
    trend: Trend
    prognosis: PrognosisInfo
    problems: list[ProblemItem] = []
    series: list[ParamSeries] = []
    alerts: list[Alert] = []
    tasks: list[Task] = []
    sparkline: list[float] = []
    vitals: RelativeVitals
    doctor_contact: DoctorContact | None = None


class RelativeLoginRequest(BaseModel):
    phone: str
    pin: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    role: Role
    full_name: str


class RelativeLoginResponse(TokenPair):
    patients: list[RelativePatientItem] = []

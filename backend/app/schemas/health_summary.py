from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class MetricPoint(BaseModel):
    value: float
    at: datetime
    source: str


class DailyVital(BaseModel):
    day: date
    avg: float | None = None
    min: float | None = None
    max: float | None = None
    n: int = 0


class VitalSummary(BaseModel):
    latest: MetricPoint | None = None
    daily: list[DailyVital]
    samples_n: int = 0
    today: DailyVital | None = None


class Freshness(BaseModel):
    status: Literal["fresh", "stale", "no_data"]
    last_sample_at: datetime | None = None
    stale_after_minutes: int
    excluded_samples: int = 0


class BloodPressure(BaseModel):
    systolic: int
    diastolic: int
    at: datetime
    source: str


class DailyActivity(BaseModel):
    day: date
    steps: float | None = None
    distance_m: float | None = None
    active_calories_kcal: float | None = None
    total_calories_kcal: float | None = None
    floors: float | None = None
    elevation_gain_m: float | None = None


class ActivitySummary(BaseModel):
    today: DailyActivity | None = None
    daily: list[DailyActivity]
    goal_steps: int


class SleepStagesMinutes(BaseModel):
    deep: int
    light: int
    rem: int
    awake: int
    unspecified: int


class SleepNight(BaseModel):
    day: date
    start_time: datetime
    end_time: datetime
    source: str
    in_bed_minutes: int
    asleep_minutes: int
    efficiency_pct: int | None = None
    stages_minutes: SleepStagesMinutes | None = None


class DailySleep(BaseModel):
    day: date
    asleep_minutes: int | None = None
    in_bed_minutes: int | None = None


class SleepSummary(BaseModel):
    last_night: SleepNight | None = None
    daily: list[DailySleep]


class StressPoint(BaseModel):
    score: int
    level: Literal["low", "medium", "high"]
    at: datetime


class DailyStress(BaseModel):
    day: date
    score: int | None = None


class StressSummary(BaseModel):
    method: str
    is_estimate: bool = True
    status: Literal["ok", "insufficient_baseline", "no_recent_hrv"]
    baseline_hrv_ms: float | None = None
    latest: StressPoint | None = None
    daily: list[DailyStress]


class ExerciseItem(BaseModel):
    exercise_type: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    source: str


class FallEvent(BaseModel):
    at: datetime
    source: str


class HealthEvents(BaseModel):
    falls: list[FallEvent]


class HealthInsight(BaseModel):
    key: str
    severity: Literal["attention", "info", "positive"]
    params: dict


class HealthSummary(BaseModel):
    """Measured health data for one patient, grouped by local (Tashkent) day."""

    patient_id: str
    generated_at: datetime
    window_days: int
    timezone: str
    freshness: Freshness
    metrics: dict[str, VitalSummary]
    latest_measurements: dict[str, MetricPoint | None]
    blood_pressure: BloodPressure | None = None
    activity: ActivitySummary
    sleep: SleepSummary
    stress: StressSummary
    exercise_sessions: list[ExerciseItem]
    events: HealthEvents
    insights: list[HealthInsight]

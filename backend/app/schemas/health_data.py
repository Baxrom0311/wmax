from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


HealthSource = Literal[
    "wear_health_services",
    "health_connect",
    "healthkit",
    "wear_data_layer",
    "manual",
]

HealthMetric = Literal[
    "heart_rate_bpm",
    "resting_heart_rate_bpm",
    "heart_rate_variability_rmssd_ms",
    "heart_rate_variability_sdnn_ms",
    "blood_pressure_systolic_mmhg",
    "blood_pressure_diastolic_mmhg",
    "blood_glucose_mmol_l",
    "weight_kg",
    "body_fat_pct",
    "vo2_max_ml_kg_min",
    "oxygen_saturation_pct",
    "respiratory_rate_bpm",
    "skin_temperature_c",
    "skin_temperature_baseline_c",
    "skin_temperature_delta_c",
    "body_temperature_c",
    "steps",
    "daily_steps",
    "distance_m",
    "speed_mps",
    "pace_mps",
    "active_calories_kcal",
    "total_calories_kcal",
    "basal_calories_kcal",
    "elevation_gain_m",
    "floors",
    "worn_state",
    "battery_pct",
    "charging_state",
    "sleep_stage",
    "activity_state",
    "fall_detected",
]


class HealthSampleIn(BaseModel):
    metric: HealthMetric
    recorded_at: datetime
    value_num: float | None = Field(None, allow_inf_nan=False)
    value_text: str | None = None
    unit: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    source_record_id: str | None = None
    quality: float | None = Field(None, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_value(self) -> "HealthSampleIn":
        if self.value_num is None and self.value_text is None:
            raise ValueError("value_num yoki value_text talab qilinadi")
        if self.ended_at is not None and self.started_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at started_at dan oldin bo'lishi mumkin emas")
        if (
            self.started_at is not None
            and self.recorded_at < self.started_at
        ) or (
            self.ended_at is not None
            and self.recorded_at > self.ended_at
        ):
            raise ValueError("recorded_at interval chegarasidan tashqarida")
        return self

    @field_validator("recorded_at", "started_at", "ended_at")
    @classmethod
    def normalize_ts(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class SleepStageIn(BaseModel):
    stage: str
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_window(self) -> "SleepStageIn":
        if self.end_time <= self.start_time:
            raise ValueError("Uyqu bosqichi end_time start_time dan keyin bo'lishi kerak")
        return self

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_ts(cls, value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class SleepSessionIn(BaseModel):
    start_time: datetime
    end_time: datetime
    source_record_id: str | None = None
    stages: list[SleepStageIn] = Field(default_factory=list, max_length=200)
    metrics: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_window(self) -> "SleepSessionIn":
        if self.end_time <= self.start_time:
            raise ValueError("Uyqu sessiyasi end_time start_time dan keyin bo'lishi kerak")
        if any(
            stage.start_time < self.start_time or stage.end_time > self.end_time
            for stage in self.stages
        ):
            raise ValueError("Uyqu bosqichlari sessiya vaqt oralig'idan tashqariga chiqmasligi kerak")
        ordered = sorted(self.stages, key=lambda stage: stage.start_time)
        if any(left.end_time > right.start_time for left, right in zip(ordered, ordered[1:])):
            raise ValueError("Uyqu bosqichlari ustma-ust kelmasligi kerak")
        return self

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_ts(cls, value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class ExerciseSessionIn(BaseModel):
    exercise_type: str
    start_time: datetime
    end_time: datetime
    source_record_id: str | None = None
    metrics: dict = Field(default_factory=dict)
    route: list[dict] | None = Field(default=None, max_length=5000)
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_window(self) -> "ExerciseSessionIn":
        if self.end_time <= self.start_time:
            raise ValueError("Mashq sessiyasi end_time start_time dan keyin bo'lishi kerak")
        return self

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_ts(cls, value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class HealthDataBatch(BaseModel):
    batch_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    sequence: int | None = Field(None, ge=0)
    source: HealthSource
    samples: list[HealthSampleIn] = Field(default_factory=list, max_length=2000)
    sleep_sessions: list[SleepSessionIn] = Field(default_factory=list, max_length=50)
    exercise_sessions: list[ExerciseSessionIn] = Field(default_factory=list, max_length=100)
    metadata: dict = Field(default_factory=dict)


class HealthDataIngestResult(BaseModel):
    server_time: datetime
    batch_id: uuid.UUID
    accepted: int = 0
    duplicate: int = 0
    rejected: list[dict[str, str]] = Field(default_factory=list)

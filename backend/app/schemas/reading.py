from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, field_validator, model_validator


class ReadingIn(BaseModel):
    window_start: datetime | None = None
    window_end: datetime | None = None
    ts: datetime | None = None
    hr_mean: float | None = Field(None, ge=20.0, le=260.0, description="O'rtacha puls (bpm)")
    hr_min: float | None = Field(None, ge=20.0, le=260.0, description="Minimal puls (bpm)")
    hr_max: float | None = Field(None, ge=20.0, le=260.0, description="Maksimal puls (bpm)")
    rmssd: float | None = Field(None, ge=0.0, le=600.0, description="HRV RMSSD (ms)")
    sdnn: float | None = Field(None, ge=0.0, le=600.0, description="HRV SDNN (ms)")
    spo2: float | None = Field(None, ge=40.0, le=100.0, description="Kislorod to'yinishi (%)")
    skin_temp: float | None = Field(None, ge=25.0, le=45.0, description="Teri harorati (°C)")
    steps: int | None = Field(None, ge=0, le=10000, description="5 daqiqalik qadamlar soni")
    rr_est: float | None = Field(None, ge=4.0, le=65.0, description="Nafas olish tezligi (nafas/daq)")
    sleep_frag: float | None = Field(None, ge=0.0, le=30.0, description="Uyqu uzilishi indeksi")
    worn_pct: int | None = Field(None, ge=0, le=100)
    samples_n: int = Field(0, ge=0, le=300)
    worn: bool = Field(True, description="Soat taqilganmi")
    battery: int | None = Field(None, ge=0, le=100, description="Batareya quvvati (%)")

    @model_validator(mode="after")
    def normalize_window(self) -> "ReadingIn":
        if self.window_start is None and self.ts is not None:
            self.window_start = self.ts
        if self.window_start is None:
            raise ValueError("window_start talab qilinadi")
        if self.window_end is None:
            self.window_end = self.window_start + timedelta(minutes=5)
        return self

    @field_validator("window_start", "window_end", "ts")
    @classmethod
    def validate_timestamp(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        now = datetime.now(timezone.utc)
        # Ensure timezone-aware
        ts = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if ts > now + timedelta(minutes=10):
            raise ValueError("O'lchov vaqti kelajakda bo'lishi mumkin emas")
        return ts


IngestItem = ReadingIn


class IngestBatch(BaseModel):
    batch_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    sequence: int | None = Field(None, ge=0, description="Device-local monotonic batch sequence")
    patient_id: uuid.UUID | None = None
    device_clock_utc: datetime | None = None
    readings: list[ReadingIn] = Field(default_factory=list, max_length=500)


class IngestAck(BaseModel):
    window_start: datetime
    reason: str | None = None


class IngestResult(BaseModel):
    server_time: datetime
    batch_id: uuid.UUID | None = None
    sequence: int | None = None
    idempotency_key: str | None = None
    accepted: list[datetime] = Field(default_factory=list)
    duplicate: list[datetime] = Field(default_factory=list)
    orphaned: list[datetime] = Field(default_factory=list)
    rejected: list[IngestAck] = Field(default_factory=list)

    @property
    def accepted_count(self) -> int:
        return len(self.accepted)

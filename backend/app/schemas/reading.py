from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import AlertLevel


class ReadingIn(BaseModel):
    ts: datetime
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
    worn: bool = Field(True, description="Soat taqilganmi")
    battery: int | None = Field(None, ge=0, le=100, description="Batareya quvvati (%)")

    @field_validator("ts")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        # Ensure timezone-aware
        ts = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if ts > now + timedelta(minutes=10):
            raise ValueError("O'lchov vaqti kelajakda bo'lishi mumkin emas")
        if ts < now - timedelta(days=90):
            raise ValueError("O'lchov vaqti 90 kundan eski bo'lishi mumkin emas")
        return ts


class IngestBatch(BaseModel):
    patient_id: uuid.UUID
    device_id: str | None = None
    readings: list[ReadingIn] = Field(..., min_length=1, max_length=500)


class IngestResult(BaseModel):
    accepted: int
    duplicates: int
    latest_level: AlertLevel

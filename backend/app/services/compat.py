from __future__ import annotations

from datetime import datetime
from typing import Any

from algo_interface import ReadingVec
from app.domain.health_quality import is_worn_window


def reading_ts(reading: Any) -> datetime:
    return getattr(reading, "window_start", None) or getattr(reading, "ts")


def reading_value(reading: Any, name: str) -> Any:
    return getattr(reading, name, None)


def to_reading_vec(reading: Any) -> ReadingVec:
    return ReadingVec(
        ts=reading_ts(reading),
        hr_mean=reading_value(reading, "hr_mean"),
        hr_min=reading_value(reading, "hr_min"),
        hr_max=reading_value(reading, "hr_max"),
        rmssd=reading_value(reading, "rmssd"),
        sdnn=reading_value(reading, "sdnn"),
        spo2=reading_value(reading, "spo2"),
        skin_temp=reading_value(reading, "skin_temp"),
        steps=reading_value(reading, "steps"),
        rr_est=reading_value(reading, "rr_est"),
        sleep_frag=reading_value(reading, "sleep_frag"),
        worn=is_worn_window(
            reading_value(reading, "worn"), reading_value(reading, "worn_pct")
        ),
    )


def task_type(task: Any) -> str:
    return getattr(task, "type", None) or getattr(task, "kind", "clinical")


def task_done_at(task: Any) -> datetime | None:
    return getattr(task, "confirmed_at", None) or getattr(task, "done_at", None)

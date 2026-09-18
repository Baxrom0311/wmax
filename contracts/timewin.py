"""Shared time-window logic. FROZEN — used by both A1 (backend-core) and A2 (algo).

All timestamps in the system are stored and transmitted as UTC.
Every clinical decision, however, is made in LOCAL time (Asia/Tashkent),
because a personal baseline built on UTC hours is silently shifted by +5h.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Tashkent")

# 0 = night 00-06, 1 = morning 06-12, 2 = day 12-18, 3 = evening 18-24
WINDOW_LABELS: dict[int, str] = {0: "night", 1: "morning", 2: "day", 3: "evening"}

# A reading every 5 minutes; a deviation must persist this many consecutive
# windows before it is allowed to raise an alert (3 * 5min = 15min).
WINDOW_MINUTES = 5
CONSECUTIVE_WINDOWS = 3

# Silence is a state, not "green".
NO_DATA_MINUTES = 45


def to_local(ts: datetime) -> datetime:
    """UTC (or naive-as-UTC) -> Asia/Tashkent aware datetime."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(LOCAL_TZ)


def window_of(ts: datetime) -> int:
    """Time-of-day window index 0..3, computed in LOCAL time."""
    return to_local(ts).hour // 6


def local_day(ts: datetime) -> date:
    """Calendar day in LOCAL time — used for daily trend aggregation."""
    return to_local(ts).date()


def is_no_data(last_reading_ts: datetime | None, now: datetime) -> bool:
    """True when the watch has been silent long enough to stop claiming 'green'."""
    if last_reading_ts is None:
        return True
    if last_reading_ts.tzinfo is None:
        last_reading_ts = last_reading_ts.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - last_reading_ts) > timedelta(minutes=NO_DATA_MINUTES)

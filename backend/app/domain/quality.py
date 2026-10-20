from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from app.domain.types import AlertLevel, DataQuality, TaskKind

MIN_CLINICAL_SCORE = 0.70
MIN_DATA_COVERAGE = 0.50


def task_kind(quality: DataQuality, level: AlertLevel) -> TaskKind:
    """F2: poor data changes the requested action, not patient visibility."""
    if level == "no_data":
        return "technical"
    if quality.days_total <= 0:
        return "technical"
    coverage = quality.days_with_data / quality.days_total
    if quality.score >= MIN_CLINICAL_SCORE and coverage >= MIN_DATA_COVERAGE:
        return "clinical"
    return "technical"


QUALITY_LOOKBACK = timedelta(hours=1)
WINDOW = timedelta(minutes=5)


def assess(windows: Sequence[tuple[datetime, bool]], now: datetime, *, days: int = 7) -> DataQuality:
    """Heuristic data quality from (window_start, usable) pairs.

    `score` is the share of expected 5-minute windows in the last hour that
    carried usable, worn measurements (capped by how long data has existed);
    coverage counts calendar days with any usable window in the lookback.
    This is a reliability gate for task routing, not a clinical probability.
    """
    if not windows:
        return DataQuality(score=0.0, days_with_data=0, days_total=0)
    first = min(ts for ts, _usable in windows)
    since = max(first, now - QUALITY_LOOKBACK)
    expected = max(1, min(int(QUALITY_LOOKBACK / WINDOW), int((now - since) / WINDOW) + 1))
    recent_usable = {ts for ts, usable in windows if usable and ts >= since}
    score = min(1.0, len(recent_usable) / expected)

    start_day = max(first.date(), (now - timedelta(days=days - 1)).date())
    days_total = (now.date() - start_day).days + 1
    days_with_data = len({ts.date() for ts, usable in windows if usable and ts.date() >= start_day})
    return DataQuality(score=round(score, 2), days_with_data=days_with_data, days_total=days_total)

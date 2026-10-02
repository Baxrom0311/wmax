from __future__ import annotations

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

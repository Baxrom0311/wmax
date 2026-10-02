from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.health_data import HealthSampleIn

FUTURE_TIMESTAMP_TOLERANCE = timedelta(minutes=5)


def is_worn_window(worn: bool, worn_pct: int | None) -> bool:
    """Treat an explicitly zero wear fraction as unworn; keep legacy nulls unchanged."""
    return worn and worn_pct != 0


def sample_quality_flags(
    sample: HealthSampleIn,
    *,
    received_at: datetime | None = None,
) -> tuple[str, ...]:
    """Return explainable ingestion-quality warnings without judging clinical values."""
    flags: list[str] = []
    if sample.source_record_id is None:
        flags.append("missing_source_record_id")
    if sample.value_num is not None and not sample.unit:
        flags.append("missing_unit")

    now = received_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if sample.recorded_at > now + FUTURE_TIMESTAMP_TOLERANCE:
        flags.append("recorded_at_in_future")
    if sample.started_at is not None and sample.recorded_at < sample.started_at:
        flags.append("recorded_before_interval_start")
    if sample.ended_at is not None and sample.recorded_at > sample.ended_at:
        flags.append("recorded_after_interval_end")
    return tuple(flags)

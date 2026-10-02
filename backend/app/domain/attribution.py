from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.domain.types import AssignmentWindow


def attribute_reading(
    reading_ts: datetime,
    device_id: str,
    windows: tuple[AssignmentWindow, ...],
) -> UUID | None:
    """F4: attribution uses the assignment window, not the current owner."""
    matches = [
        window
        for window in windows
        if window.device_id == device_id
        and window.assigned_at <= reading_ts
        and (window.released_at is None or reading_ts < window.released_at)
    ]
    if not matches:
        return None
    return max(matches, key=lambda window: window.assigned_at).patient_id


def orphan_candidates(
    device_id: str,
    ts_range: tuple[datetime, datetime],
    windows: tuple[AssignmentWindow, ...],
) -> tuple[UUID, ...]:
    """F4: candidates are limited to patients tied to the same device and period."""
    start, end = ts_range
    patient_ids: list[UUID] = []
    seen: set[UUID] = set()
    for window in sorted(windows, key=lambda item: item.assigned_at):
        window_end = window.released_at or end
        overlaps = window.device_id == device_id and window.assigned_at < end and window_end > start
        if overlaps and window.patient_id not in seen:
            seen.add(window.patient_id)
            patient_ids.append(window.patient_id)
    return tuple(patient_ids)

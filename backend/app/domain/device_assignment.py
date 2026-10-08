from __future__ import annotations

from datetime import datetime
from typing import Any


def assignment_covers_interval(
    assignment: Any, start: datetime, end: datetime
) -> bool:
    """Check ownership of a full half-open measurement interval."""
    if assignment.assigned_at > start:
        return False
    released_at = assignment.released_at
    if released_at is None:
        return True
    return end <= released_at and (end > start or start < released_at)

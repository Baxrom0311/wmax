from __future__ import annotations

from datetime import datetime
from typing import Any

import timewin
from app.domain.types import AlertLevel


def current_level(last_usable_at: datetime | None, latest_alert: Any | None, now: datetime) -> AlertLevel:
    """Displayed patient status.

    Silence, empty or unworn windows, and "nothing evaluated yet" are all
    `no_data`. Missing or unreliable data never implies a healthy patient.
    """
    if timewin.is_no_data(last_usable_at, now) or latest_alert is None:
        return "no_data"
    return latest_alert.level

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

AlertLevel = Literal["green", "amber", "red", "no_data"]
Phase = Literal["calib", "learning", "full"]
TrendDirection = Literal["improving", "stable", "worsening"]
TaskStatus = Literal["created", "sent", "seen", "done", "overdue"]
Role = Literal["doctor", "nurse", "admin"]


class ErrorResponse(BaseModel):
    detail: str

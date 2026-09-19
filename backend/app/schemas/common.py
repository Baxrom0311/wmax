from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

AlertLevel = Literal["green", "amber", "red", "no_data"]
Phase = Literal["calib", "learning", "full"]
TrendDirection = Literal["improving", "stable", "worsening"]
TaskStatus = Literal["created", "sent", "seen", "done", "overdue"]
Role = Literal["doctor", "nurse", "admin", "dispatcher"]
# Caregivers and patients authenticate too, but they are not staff and must never be
# handed a clinician role. Tokens carry AuthRole; RBAC checks use Role/CLINICIAN_ROLES.
AuthRole = Literal["doctor", "nurse", "admin", "dispatcher", "relative", "patient"]
CLINICIAN_ROLES: frozenset[str] = frozenset({"doctor", "nurse", "admin", "dispatcher"})


class ErrorResponse(BaseModel):
    detail: str

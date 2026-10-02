from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import TaskStatus


class Task(BaseModel):
    id: int
    patient_id: uuid.UUID
    type: Literal["active_call", "red_alert", "clinical", "technical"]
    status: TaskStatus
    created_at: datetime
    due_at: datetime | None = None
    confirmed_at: datetime | None = None
    acknowledged_at: datetime | None = None
    assignee_account_id: uuid.UUID | None = None
    note: str | None = None


class TaskConfirmRequest(BaseModel):
    note: str | None = None


class TaskReassignRequest(BaseModel):
    assignee_account_id: uuid.UUID
    note: str | None = None

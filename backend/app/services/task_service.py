from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.task import Task
from app.repositories.task_repo import TaskRepository
from app.schemas.common import TaskStatus
from app.schemas.task import Task as TaskSchema, TaskConfirmRequest


class TaskService:
    """Service handling clinical task workflows and active-call confirmations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)

    async def list_tasks(self, status: TaskStatus | None = None) -> list[TaskSchema]:
        """Lists tasks ordered chronologically by due_at."""
        tasks = await self.task_repo.get_tasks(status=status)
        return [
            TaskSchema(
                id=t.id,
                patient_id=t.patient_id,
                type=t.type,
                status=t.status,
                created_at=t.created_at,
                due_at=t.due_at,
                confirmed_at=t.confirmed_at,
                note=t.note,
            )
            for t in tasks
        ]

    async def confirm_task(self, task_id: int, request: TaskConfirmRequest) -> TaskSchema:
        """Confirms completion of a task, recording confirmed_at timestamp and clinical note."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundException(message="Topshiriq topilmadi", resource_name="Task")

        now = datetime.now(timezone.utc)
        updated = await self.task_repo.confirm_task(
            task_id=task_id,
            confirmed_at=now,
            note=request.note,
        )
        if not updated:
            raise NotFoundException(message="Topshiriq topilmadi", resource_name="Task")

        return TaskSchema(
            id=updated.id,
            patient_id=updated.patient_id,
            type=updated.type,
            status=updated.status,
            created_at=updated.created_at,
            due_at=updated.due_at,
            confirmed_at=updated.confirmed_at,
            note=updated.note,
        )

    async def create_active_call_task(
        self, patient_id: uuid.UUID, due_at: datetime, note: str | None = None
    ) -> TaskSchema:
        """Creates a new active call task for discharge follow-up."""
        task = await self.task_repo.create_task(
            patient_id=patient_id,
            task_type="active_call",
            due_at=due_at,
            note=note,
        )
        return TaskSchema(
            id=task.id,
            patient_id=task.patient_id,
            type=task.type,
            status=task.status,
            created_at=task.created_at,
            due_at=task.due_at,
            confirmed_at=task.confirmed_at,
            note=task.note,
        )

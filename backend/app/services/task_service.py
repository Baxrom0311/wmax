from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.task import Task
from app.repositories.task_repo import TaskRepository
from app.schemas.common import TaskStatus
from app.schemas.task import Task as TaskSchema, TaskConfirmRequest, TaskReassignRequest
from app.services.live_event_service import LiveEventService


class TaskService:
    """Service handling clinical task workflows and active-call confirmations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.task_repo = TaskRepository(session)

    def _to_schema(self, task: Task) -> TaskSchema:
        return TaskSchema(
            id=task.id,
            patient_id=task.patient_id,
            type=getattr(task, "type", None) or getattr(task, "kind", "clinical"),
            status=task.status,
            created_at=task.created_at,
            due_at=task.due_at,
            confirmed_at=getattr(task, "confirmed_at", None) or getattr(task, "done_at", None),
            acknowledged_at=getattr(task, "acknowledged_at", None),
            assignee_account_id=getattr(task, "assignee_account_id", None),
            note=task.note,
        )

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> list[TaskSchema]:
        """Lists tasks ordered chronologically by due_at."""
        tasks = await self.task_repo.get_tasks(status=status, tenant_ids=tenant_ids)
        return [self._to_schema(t) for t in tasks]

    async def confirm_task(
        self,
        task_id: int,
        request: TaskConfirmRequest,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> TaskSchema:
        """Confirms completion of a task, recording confirmed_at timestamp and clinical note."""
        task = await self.task_repo.get_by_id_in_scope(task_id, tenant_ids=tenant_ids)
        if not task:
            raise NotFoundException(message="Topshiriq topilmadi", resource_name="Task")

        now = datetime.now(timezone.utc)
        updated = await self.task_repo.confirm_task(
            task_id=task_id,
            confirmed_at=now,
            note=request.note,
            tenant_ids=tenant_ids,
        )
        if not updated:
            raise NotFoundException(message="Topshiriq topilmadi", resource_name="Task")

        await LiveEventService(self.session).publish_task(updated, action="done")
        return self._to_schema(updated)

    async def acknowledge_task(
        self,
        task_id: int,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> TaskSchema:
        updated = await self.task_repo.update_status(task_id, "acknowledged", tenant_ids=tenant_ids)
        if not updated:
            raise NotFoundException(message="Topshiriq topilmadi", resource_name="Task")
        await LiveEventService(self.session).publish_task(updated, action="acknowledged")
        return self._to_schema(updated)

    async def complete_task(
        self,
        task_id: int,
        request: TaskConfirmRequest,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> TaskSchema:
        updated = await self.task_repo.update_status(task_id, "done", note=request.note, tenant_ids=tenant_ids)
        if not updated:
            raise NotFoundException(message="Topshiriq topilmadi", resource_name="Task")
        await LiveEventService(self.session).publish_task(updated, action="done")
        return self._to_schema(updated)

    async def reassign_task(
        self,
        task_id: int,
        request: TaskReassignRequest,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> TaskSchema:
        updated = await self.task_repo.update_status(
            task_id,
            "open",
            note=request.note,
            assignee_account_id=request.assignee_account_id,
            tenant_ids=tenant_ids,
        )
        if not updated:
            raise NotFoundException(message="Topshiriq topilmadi", resource_name="Task")
        await LiveEventService(self.session).publish_task(updated, action="reassigned")
        return self._to_schema(updated)

    async def create_active_call_task(
        self,
        patient_id: uuid.UUID,
        tenant_id: uuid.UUID,
        assignee_account_id: uuid.UUID,
        due_at: datetime,
        note: str | None = None,
    ) -> TaskSchema:
        """Creates a new active call task for discharge follow-up."""
        task = await self.task_repo.create_task(
            patient_id=patient_id,
            tenant_id=tenant_id,
            assignee_account_id=assignee_account_id,
            kind="clinical",
            due_at=due_at,
            note=note,
        )
        await LiveEventService(self.session).publish_task(task, action="created")
        return self._to_schema(task)

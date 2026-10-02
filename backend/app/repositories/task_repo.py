from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task

OPEN_TASK_STATUSES = ("open", "acknowledged")


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id_in_scope(
        self,
        task_id: int,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        if tenant_ids is not None:
            if not tenant_ids:
                return None
            stmt = stmt.where(Task.tenant_id.in_(list(tenant_ids)))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_open_task(self, patient_id: uuid.UUID) -> Task | None:
        stmt = (
            select(Task)
            .where(
                Task.patient_id == patient_id,
                Task.status.in_(OPEN_TASK_STATUSES),
            )
            .order_by(Task.due_at.asc())
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_tasks(
        self,
        patient_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int | None = None,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> Sequence[Task]:
        stmt = select(Task).order_by(Task.due_at.asc().nullslast())
        if tenant_ids is not None:
            if not tenant_ids:
                return []
            stmt = stmt.where(Task.tenant_id.in_(list(tenant_ids)))
        if patient_id:
            stmt = stmt.where(Task.patient_id == patient_id)
        if status:
            stmt = stmt.where(Task.status == status)
        if limit:
            stmt = stmt.limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def create_task(
        self,
        patient_id: uuid.UUID,
        tenant_id: uuid.UUID,
        assignee_account_id: uuid.UUID,
        due_at: datetime,
        kind: str = "clinical",
        alert_id: int | None = None,
        note: str | None = None,
    ) -> Task:
        if kind not in {"clinical", "technical"}:
            kind = "clinical"
        task = Task(
            patient_id=patient_id,
            tenant_id=tenant_id,
            assignee_account_id=assignee_account_id,
            kind=kind,
            status="open",
            due_at=due_at,
            alert_id=alert_id,
            note=note,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def confirm_task(
        self,
        task_id: int,
        confirmed_at: datetime | None = None,
        note: str | None = None,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> Task | None:
        task = await self.get_by_id_in_scope(task_id, tenant_ids=tenant_ids)
        if task:
            task.status = "done"
            task.done_at = confirmed_at or datetime.now(timezone.utc)
            if note:
                task.note = note
            await self.session.flush()
        return task

    async def update_status(
        self,
        task_id: int,
        status: str,
        *,
        note: str | None = None,
        assignee_account_id: uuid.UUID | None = None,
        tenant_ids: Sequence[uuid.UUID] | None = None,
    ) -> Task | None:
        task = await self.get_by_id_in_scope(task_id, tenant_ids=tenant_ids)
        if not task:
            return None
        now = datetime.now(timezone.utc)
        task.status = status
        if status == "acknowledged":
            task.acknowledged_at = now
        if status == "done":
            task.done_at = now
            task.confirmed_at = now
        if assignee_account_id is not None:
            task.assignee_account_id = assignee_account_id
        if note:
            task.note = note
        await self.session.flush()
        return task

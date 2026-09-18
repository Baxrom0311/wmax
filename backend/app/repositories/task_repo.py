from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_open_task(self, patient_id: uuid.UUID) -> Task | None:
        stmt = (
            select(Task)
            .where(
                Task.patient_id == patient_id,
                Task.status.in_(["created", "sent", "seen"]),
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
    ) -> Sequence[Task]:
        stmt = select(Task).order_by(Task.due_at.asc())
        if patient_id:
            stmt = stmt.where(Task.patient_id == patient_id)
        if status:
            stmt = stmt.where(Task.status == status)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def create_task(
        self,
        patient_id: uuid.UUID,
        task_type: str,
        due_at: datetime,
        doctor_id: uuid.UUID | None = None,
        alert_id: int | None = None,
    ) -> Task:
        task = Task(
            patient_id=patient_id,
            doctor_id=doctor_id,
            type=task_type,  # type: ignore
            status="created",
            due_at=due_at,
            alert_id=alert_id,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def confirm_task(
        self, task_id: int, note: str | None = None
    ) -> Task | None:
        task = await self.get_by_id(task_id)
        if task:
            task.status = "done"
            task.confirmed_at = datetime.now(timezone.utc)
            if note:
                task.note = note
            await self.session.flush()
        return task

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.deps import CurrentUser, get_current_user
from app.core.db import get_session
from app.models import Task
from app.schemas.common import TaskStatus
from app.schemas.task import Task as TaskSchema, TaskConfirmRequest

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get(
    "",
    response_model=list[TaskSchema],
    summary="List active-call and alert tasks.",
)
async def list_tasks(
    status: TaskStatus | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[TaskSchema]:
    stmt = select(Task).order_by(Task.due_at.asc())
    if status:
        stmt = stmt.where(Task.status == status)
    res = await session.execute(stmt)
    tasks = res.scalars().all()

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


@router.post(
    "/{id}/confirm",
    response_model=TaskSchema,
    summary="Confirm active call / task completion.",
)
async def confirm_task(
    id: int,
    body: TaskConfirmRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskSchema:
    stmt = select(Task).where(Task.id == id)
    res = await session.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Topshiriq topilmadi")

    now = datetime.now(timezone.utc)
    task.status = "done"
    task.confirmed_at = now
    if body.note:
        task.note = body.note

    await session.commit()
    await session.refresh(task)

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

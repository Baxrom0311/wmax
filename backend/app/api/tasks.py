from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user
from app.core.db import get_session
from app.schemas.common import TaskStatus
from app.schemas.task import Task as TaskSchema, TaskConfirmRequest
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get(
    "",
    response_model=list[TaskSchema],
    summary="List active-call and alert tasks ordered by due date.",
)
async def list_tasks(
    status: TaskStatus | None = Query(None, description="Filter by task status"),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[TaskSchema]:
    service = TaskService(session)
    return await service.list_tasks(status=status)


@router.post(
    "/{id}/confirm",
    response_model=TaskSchema,
    summary="Confirm completion of an active-call or alert task.",
)
async def confirm_task(
    id: int,
    body: TaskConfirmRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskSchema:
    service = TaskService(session)
    return await service.confirm_task(task_id=id, request=body)

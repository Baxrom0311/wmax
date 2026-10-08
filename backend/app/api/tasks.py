from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician
from app.core.db import get_session
from app.schemas.common import TaskStatus
from app.schemas.task import Task as TaskSchema, TaskConfirmRequest, TaskReassignRequest
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _tenant_scope(current_user: CurrentUser):
    return current_user.tenant_ids


@router.get(
    "",
    response_model=list[TaskSchema],
    summary="List active-call and alert tasks ordered by due date.",
)
async def list_tasks(
    status: TaskStatus | None = Query(None, description="Filter by task status"),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[TaskSchema]:
    service = TaskService(session)
    return await service.list_tasks(status=status, tenant_ids=_tenant_scope(current_user))


@router.post(
    "/{id}/confirm",
    response_model=TaskSchema,
    summary="Confirm completion of an active-call or alert task.",
)
async def confirm_task(
    id: int,
    body: TaskConfirmRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> TaskSchema:
    service = TaskService(session)
    return await service.confirm_task(task_id=id, request=body, tenant_ids=_tenant_scope(current_user))


@router.post(
    "/{id}/acknowledge",
    response_model=TaskSchema,
    summary="Mark task as seen by the assignee.",
)
async def acknowledge_task(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> TaskSchema:
    service = TaskService(session)
    return await service.acknowledge_task(task_id=id, tenant_ids=_tenant_scope(current_user))


@router.post(
    "/{id}/complete",
    response_model=TaskSchema,
    summary="Complete a task with optional note.",
)
async def complete_task(
    id: int,
    body: TaskConfirmRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> TaskSchema:
    service = TaskService(session)
    return await service.complete_task(task_id=id, request=body, tenant_ids=_tenant_scope(current_user))


@router.post(
    "/{id}/reassign",
    response_model=TaskSchema,
    summary="Reassign a task to another account.",
)
async def reassign_task(
    id: int,
    body: TaskReassignRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> TaskSchema:
    service = TaskService(session)
    return await service.reassign_task(task_id=id, request=body, tenant_ids=_tenant_scope(current_user))

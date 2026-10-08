from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, require_clinician
from app.core.db import get_session
from app.services.orphan_service import OrphanReadingService

router = APIRouter(prefix="/api/v1/orphans", tags=["orphans"])


class ResolveOrphanRequest(BaseModel):
    patient_id: uuid.UUID


def _tenant_scope(current_user: CurrentUser) -> list[uuid.UUID] | None:
    return current_user.tenant_ids


@router.get("", summary="List unresolved orphan readings")
async def list_orphans(
    device_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    service = OrphanReadingService(session)
    return await service.list_unresolved(
        device_id=device_id,
        limit=limit,
        tenant_ids=_tenant_scope(current_user),
    )


@router.get("/{id}/candidates", summary="List candidate patients for an orphan reading")
async def orphan_candidates_endpoint(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> list[dict[str, Any]]:
    service = OrphanReadingService(session)
    try:
        return await service.candidates(id, tenant_ids=_tenant_scope(current_user))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))


@router.post("/{id}/resolve", summary="Attach orphan reading to a patient")
async def resolve_orphan(
    id: int,
    body: ResolveOrphanRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    service = OrphanReadingService(session)
    try:
        result = await service.resolve(
            id,
            body.patient_id,
            resolved_by=current_user.id,
            tenant_ids=_tenant_scope(current_user),
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yetim o'lchov topilmadi")
    await session.commit()
    return result


@router.post("/{id}/discard", summary="Discard orphan reading without deleting it")
async def discard_orphan(
    id: int,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(require_clinician),
) -> dict[str, Any]:
    service = OrphanReadingService(session)
    try:
        result = await service.discard(
            id,
            resolved_by=current_user.id,
            tenant_ids=_tenant_scope(current_user),
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yetim o'lchov topilmadi")
    await session.commit()
    return result

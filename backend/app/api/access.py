from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_principal
from app.core.db import get_session
from app.services.access_service import AccessService

router = APIRouter(prefix="/api/v1/access", tags=["access"])


class AccessAcceptRequest(BaseModel):
    access_id: uuid.UUID


@router.post("/accept", summary="Accept a caregiver access invitation")
async def accept_access(
    req: AccessAcceptRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    service = AccessService(session)
    return await service.accept_invitation(access_id=req.access_id, account_id=current_user.id)

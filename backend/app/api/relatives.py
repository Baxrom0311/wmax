from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.schemas.relative import RelativeView
from app.services.relative_service import RelativeService

router = APIRouter(prefix="/api/v1/relatives", tags=["relative"])


@router.get(
    "/{token}/view",
    response_model=RelativeView,
    summary="Caregiver view: prognosis, vital signs, problems, sparkline, and baseline corridors.",
)
async def get_relative_view(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> RelativeView:
    """
    Public endpoint accessed by caregiver using their unique access token.
    Returns a rich patient status view with clinical prognosis and vital trends.
    No authentication header required — token IS the credential.
    """
    service = RelativeService(session)
    return await service.get_relative_view(token)

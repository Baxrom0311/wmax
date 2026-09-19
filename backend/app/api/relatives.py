from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_relative
from app.core.db import get_session
from app.schemas.auth import CurrentUser
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
    caregiver: CurrentUser = Depends(get_current_relative),
) -> RelativeView:
    """
    Returns a patient status view for an authenticated caregiver.

    The URL token selects which linked patient to show; the Bearer token proves
    who is asking. Both must agree — the link on its own is not a credential,
    because it travels through Telegram messages and proxy access logs.
    """
    service = RelativeService(session)
    return await service.get_relative_view(token, caregiver_phone=caregiver.phone)

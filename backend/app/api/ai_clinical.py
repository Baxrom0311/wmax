from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.cache import ai_cache
from app.ai.clinical_ai import ClinicalAIService
from app.auth.deps import CurrentUser, require_clinician, require_doctor
from app.core.db import get_session
from app.core.exceptions import NotFoundException
from app.schemas.problem import NurseHandoverSBAR, TwinPrognosisInfo
from app.services.patient_context import PatientContextBuilder

router = APIRouter(prefix="/api/v1/patients/{id}", tags=["ai-clinical"])


@router.post(
    "/twin/prognosis",
    response_model=TwinPrognosisInfo,
    summary="Generate comprehensive AI digital twin clinical prognosis",
)
@router.get(
    "/twin/prognosis",
    response_model=TwinPrognosisInfo,
    summary="Get cached or generate AI digital twin clinical prognosis",
)
async def get_patient_twin_prognosis(
    id: uuid.UUID,
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Evaluates 72-hour clinical prognosis over complete digital twin context (Section 8.3 & 8.4)."""
    builder = PatientContextBuilder(db)
    ctx = await builder.build(id)
    if not ctx:
        raise NotFoundException("Bemor topilmadi")

    ai_service = ClinicalAIService()
    return await ai_service.generate_twin_prognosis(ctx, session=db)


@router.post(
    "/nurse-handover",
    response_model=NurseHandoverSBAR,
    summary="Generate AI-powered SBAR nurse handover and shift patrol checklist",
)
@router.get(
    "/nurse-handover",
    response_model=NurseHandoverSBAR,
    summary="Get cached or generate SBAR nurse handover and shift patrol checklist",
)
async def get_nurse_handover(
    id: uuid.UUID,
    clinician: CurrentUser = Depends(require_clinician),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Generates an actionable SBAR report and priority checklist for on-duty nurses."""
    builder = PatientContextBuilder(db)
    ctx = await builder.build(id)
    if not ctx:
        raise NotFoundException("Bemor topilmadi")

    ai_service = ClinicalAIService()
    return await ai_service.generate_nurse_handover(ctx, session=db)

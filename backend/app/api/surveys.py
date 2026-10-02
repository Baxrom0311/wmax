from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_principal
from app.core.db import get_session
from app.services.survey_service import SurveyService

router = APIRouter(prefix="/api/v1/surveys", tags=["surveys"])


class SurveySubmitRequest(BaseModel):
    patient_id: uuid.UUID
    answers: dict[str, Any]
    per_question_ms: dict[str, int] = Field(default_factory=dict)
    score: float | None = None


@router.get("/pending", summary="List pending surveys for current principal")
async def pending_surveys(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> list[dict[str, Any]]:
    return await SurveyService(session).pending(current_user)


@router.get("/{id}", summary="Get survey questions")
async def get_survey(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    return await SurveyService(session).get(id, current_user)


@router.post("/{id}/submit", status_code=status.HTTP_201_CREATED, summary="Submit survey answers")
async def submit_survey(
    id: uuid.UUID,
    req: SurveySubmitRequest,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_principal),
) -> dict[str, Any]:
    return await SurveyService(session).submit(
        id,
        patient_id=req.patient_id,
        answers=req.answers,
        per_question_ms=req.per_question_ms,
        score=req.score,
        principal=current_user,
    )

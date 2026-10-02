from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models import Survey, SurveyResponse
from app.schemas.auth import CurrentUser
from app.schemas.common import CLINICIAN_ROLES


class SurveyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def pending(self, principal: CurrentUser) -> list[dict[str, Any]]:
        audiences = self._audiences_for(principal)
        rows = (
            await self.session.execute(
                select(Survey).where(
                    Survey.is_active == True,  # noqa: E712
                    Survey.audience.in_(audiences),
                )
            )
        ).scalars().all()
        return [self._survey_dict(row, include_questions=False) for row in rows]

    async def get(self, survey_id: uuid.UUID, principal: CurrentUser) -> dict[str, Any]:
        survey = await self.session.get(Survey, survey_id)
        if not survey or not survey.is_active or survey.audience not in self._audiences_for(principal):
            raise NotFoundException("So'rovnoma", survey_id)
        return self._survey_dict(survey, include_questions=True)

    async def submit(
        self,
        survey_id: uuid.UUID,
        *,
        patient_id: uuid.UUID,
        answers: dict[str, Any],
        per_question_ms: dict[str, int],
        score: float | None,
        principal: CurrentUser,
    ) -> dict[str, Any]:
        survey = await self.session.get(Survey, survey_id)
        if not survey or not survey.is_active or survey.audience not in self._audiences_for(principal):
            raise NotFoundException("So'rovnoma", survey_id)
        self._assert_patient_scope(principal, patient_id)

        existing = (
            await self.session.execute(
                select(SurveyResponse).where(
                    SurveyResponse.survey_id == survey_id,
                    SurveyResponse.patient_id == patient_id,
                    SurveyResponse.account_id == (principal.id if principal.role != "patient" else None),
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictException("Bu so'rovnomaga javob allaqachon yuborilgan")

        response = SurveyResponse(
            survey_id=survey_id,
            patient_id=patient_id,
            account_id=principal.id if principal.role != "patient" else None,
            answers={"answers": answers, "per_question_ms": per_question_ms},
            score=score,
        )
        self.session.add(response)
        await self.session.flush()
        await self.session.commit()
        return {"id": str(response.id), "submitted_at": response.submitted_at.isoformat()}

    def _audiences_for(self, principal: CurrentUser) -> set[str]:
        if principal.role == "patient":
            return {"all", "patient"}
        if principal.role == "relative":
            return {"all", "relative", "caregiver"}
        if principal.role in CLINICIAN_ROLES:
            return {"all", "clinician", "doctor", "nurse", principal.role}
        return {"all"}

    def _assert_patient_scope(self, principal: CurrentUser, patient_id: uuid.UUID) -> None:
        if principal.role == "patient" and principal.id != patient_id:
            raise ForbiddenException("Boshqa bemor nomidan javob yuborish mumkin emas")
        if principal.role == "relative" and patient_id not in principal.patient_ids:
            raise ForbiddenException("Bu bemorga ruxsat yo'q")

    def _survey_dict(self, survey: Survey, *, include_questions: bool) -> dict[str, Any]:
        data = {"id": str(survey.id), "code": survey.code, "audience": survey.audience}
        if include_questions:
            data["questions"] = survey.questions
        return data

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictException, ForbiddenException
from app.models import Survey, SurveyResponse
from app.schemas.auth import CurrentUser
from app.services.survey_service import SurveyService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    result.scalars.return_value.all.return_value = value if isinstance(value, list) else []
    return result


def _principal(role: str, *, patient_ids: list[uuid.UUID] | None = None) -> CurrentUser:
    return CurrentUser(
        id=uuid.uuid4(),
        full_name="Test",
        role=role,  # type: ignore[arg-type]
        patient_ids=patient_ids or [],
    )


def test_survey_audience_mapping():
    service = SurveyService(AsyncMock())

    assert "patient" in service._audiences_for(_principal("patient"))
    assert "relative" in service._audiences_for(_principal("relative"))
    assert "doctor" in service._audiences_for(_principal("doctor"))


@pytest.mark.asyncio
async def test_relative_cannot_submit_for_unassigned_patient(mock_session):
    survey_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    mock_session.get = AsyncMock(
        return_value=Survey(id=survey_id, code="phq9", audience="relative", questions={}, is_active=True)
    )

    with pytest.raises(ForbiddenException):
        await SurveyService(mock_session).submit(
            survey_id,
            patient_id=patient_id,
            answers={},
            per_question_ms={},
            score=None,
            principal=_principal("relative", patient_ids=[]),
        )


@pytest.mark.asyncio
async def test_submit_rejects_duplicate_response(mock_session):
    survey_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    account_id = uuid.uuid4()
    mock_session.get = AsyncMock(
        return_value=Survey(id=survey_id, code="phq9", audience="relative", questions={}, is_active=True)
    )
    mock_session.execute.return_value = _result(
        SurveyResponse(
            id=uuid.uuid4(),
            survey_id=survey_id,
            patient_id=patient_id,
            account_id=account_id,
            answers={},
            submitted_at=datetime.now(timezone.utc),
        )
    )
    principal = CurrentUser(
        id=account_id,
        full_name="Qarovchi",
        role="relative",
        patient_ids=[patient_id],
    )

    with pytest.raises(ConflictException):
        await SurveyService(mock_session).submit(
            survey_id,
            patient_id=patient_id,
            answers={},
            per_question_ms={},
            score=None,
            principal=principal,
        )

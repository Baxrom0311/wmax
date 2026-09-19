from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ForbiddenException, ValidationException
from app.models.sos import SosEvent
from app.services.patient_context import PatientContext
from app.services.sos_service import SosService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_raise_sos_creates_event_and_snapshots(mock_session):
    patient_id = uuid.uuid4()
    context = PatientContext(
        patient_id=patient_id,
        full_name="Alisher Navoiy",
        sex="m",
        age=60,
        blood_group="O",
        rh="pos",
    )

    dispatcher_mock = AsyncMock()

    service = SosService(mock_session, dispatcher=dispatcher_mock)
    service.context_builder.build = AsyncMock(return_value=context)

    fake_event = SosEvent(
        id=uuid.uuid4(),
        patient_id=patient_id,
        status="raised",
        source="watch_button",
        raised_at=datetime.now(timezone.utc),
    )
    service.sos_repo.create_event = AsyncMock(return_value=fake_event)
    service.sos_repo.add_notification = AsyncMock()

    event = await service.raise_sos(patient_id, source="watch_button")
    assert event.id == fake_event.id
    assert event.status == "raised"
    dispatcher_mock.dispatch.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_sos_within_60s_succeeds(mock_session):
    patient_id = uuid.uuid4()
    sos_id = uuid.uuid4()
    raised_at = datetime.now(timezone.utc) - timedelta(seconds=20)

    event = SosEvent(
        id=sos_id,
        patient_id=patient_id,
        status="raised",
        raised_at=raised_at,
    )

    service = SosService(mock_session)
    service.sos_repo.get_by_id = AsyncMock(return_value=event)

    cancelled = await service.cancel_sos(sos_id, patient_id=patient_id)
    assert cancelled.status == "cancelled"
    assert cancelled.cancelled_at is not None


@pytest.mark.asyncio
async def test_cancel_sos_after_60s_fails(mock_session):
    patient_id = uuid.uuid4()
    sos_id = uuid.uuid4()
    raised_at = datetime.now(timezone.utc) - timedelta(seconds=65)

    event = SosEvent(
        id=sos_id,
        patient_id=patient_id,
        status="raised",
        raised_at=raised_at,
    )

    service = SosService(mock_session)
    service.sos_repo.get_by_id = AsyncMock(return_value=event)

    with pytest.raises(ValidationException) as exc_info:
        await service.cancel_sos(sos_id, patient_id=patient_id)
    assert "muddati o'tib ketgan" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cancel_sos_different_patient_fails(mock_session):
    patient_id = uuid.uuid4()
    other_patient_id = uuid.uuid4()
    sos_id = uuid.uuid4()
    raised_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    event = SosEvent(
        id=sos_id,
        patient_id=patient_id,
        status="raised",
        raised_at=raised_at,
    )

    service = SosService(mock_session)
    service.sos_repo.get_by_id = AsyncMock(return_value=event)

    with pytest.raises(ForbiddenException):
        await service.cancel_sos(sos_id, patient_id=other_patient_id)


@pytest.mark.asyncio
async def test_acknowledge_and_resolve_sos(mock_session):
    patient_id = uuid.uuid4()
    sos_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    event = SosEvent(
        id=sos_id,
        patient_id=patient_id,
        status="raised",
        raised_at=datetime.now(timezone.utc),
    )

    service = SosService(mock_session)
    service.sos_repo.get_by_id = AsyncMock(return_value=event)

    ack = await service.acknowledge_sos(sos_id, user_id=doctor_id)
    assert ack.status == "acknowledged"
    assert ack.acknowledged_by == doctor_id

    resolved = await service.resolve_sos(sos_id, user_id=doctor_id, resolution_note="Yordam ko'rsatildi")
    assert resolved.status == "resolved"
    assert resolved.resolution_note == "Yordam ko'rsatildi"

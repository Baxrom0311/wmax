from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.reading import OrphanReading
from app.services.orphan_service import OrphanReadingService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_resolve_orphan_creates_attributed_reading(mock_session):
    orphan = OrphanReading(
        id=1,
        device_id=uuid.uuid4(),
        window_start=datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc),
        payload={
            "window_end": "2026-09-22T10:05:00+00:00",
            "hr_mean": 78.0,
            "worn": True,
            "samples_n": 5,
        },
    )
    patient_id = uuid.uuid4()
    resolved_by = uuid.uuid4()
    mock_session.get = AsyncMock(return_value=orphan)

    service = OrphanReadingService(mock_session)
    result = await service.resolve(1, patient_id=patient_id, resolved_by=resolved_by)

    assert result is not None
    assert result["resolved_to_patient_id"] == str(patient_id)
    assert orphan.resolved_by == resolved_by
    added = mock_session.add.call_args.args[0]
    assert added.patient_id == patient_id
    assert added.device_id == orphan.device_id
    assert added.attributed_by == "nurse"
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_discard_orphan_marks_resolved_without_patient(mock_session):
    orphan = OrphanReading(
        id=2,
        device_id=uuid.uuid4(),
        window_start=datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc),
        payload={},
    )
    resolved_by = uuid.uuid4()
    mock_session.get = AsyncMock(return_value=orphan)

    service = OrphanReadingService(mock_session)
    result = await service.discard(2, resolved_by=resolved_by)

    assert result is not None
    assert result["resolved_to_patient_id"] is None
    assert orphan.resolved_by == resolved_by
    assert orphan.resolved_at is not None
    mock_session.add.assert_not_called()

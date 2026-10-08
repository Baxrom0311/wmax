import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.device import create_device_token, get_current_device, verify_ingest_key
from app.core.config import settings
from app.models.device import DeviceCredential
from app.schemas.reading import IngestBatch
from app.services.pipeline_service import PipelineService, _previous_consecutive_windows


def test_persistence_history_requires_adjacent_windows():
    start = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    windows = [
        SimpleNamespace(window_start=start + timedelta(minutes=5 * index), window_end=start + timedelta(minutes=5 * (index + 1)))
        for index in range(3)
    ]
    assert _previous_consecutive_windows(windows) == windows[:2]

    windows[1].window_end += timedelta(minutes=5)
    assert _previous_consecutive_windows(windows) == []


@pytest.mark.asyncio
async def test_ingest_without_key_rejected_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "INGEST_API_KEY", "super_secret_ingest_key")
    with pytest.raises(HTTPException) as exc_info:
        await verify_ingest_key(x_ingest_key=None)

    assert exc_info.value.status_code == 401
    assert "Qurilma kaliti yaroqsiz" in exc_info.value.detail


@pytest.mark.asyncio
async def test_ingest_with_wrong_key_rejected(monkeypatch):
    monkeypatch.setattr(settings, "INGEST_API_KEY", "super_secret_ingest_key")
    with pytest.raises(HTTPException) as exc_info:
        await verify_ingest_key(x_ingest_key="wrong_key_submitted")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_ingest_with_correct_key_accepted(monkeypatch):
    monkeypatch.setattr(settings, "INGEST_API_KEY", "super_secret_ingest_key")
    # Should not raise any exception
    await verify_ingest_key(x_ingest_key="super_secret_ingest_key")


@pytest.mark.asyncio
async def test_ingest_without_key_accepted_when_unconfigured_in_dev(monkeypatch):
    monkeypatch.setattr(settings, "INGEST_API_KEY", "")
    # In non-prod with empty key, it warns and passes
    await verify_ingest_key(x_ingest_key=None)


@pytest.mark.asyncio
async def test_device_bearer_token_resolves_active_credential():
    device_id = uuid.uuid4()
    credential_id = uuid.uuid4()
    secret = "one-time-device-secret"
    token = create_device_token(
        device_id=device_id,
        credential_id=credential_id,
        credential_secret=secret,
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    class Session:
        async def get(self, model, key):
            return DeviceCredential(
                id=key,
                device_id=device_id,
                secret_hash=hashlib.sha256(secret.encode()).hexdigest(),
            )

        async def execute(self, stmt, params=None):
            return None

    principal = await get_current_device(credentials=credentials, session=Session())

    assert principal.device_id == device_id
    assert principal.credential_id == credential_id


@pytest.mark.asyncio
async def test_device_bearer_token_rejects_revoked_credential():
    from datetime import datetime, timezone

    device_id = uuid.uuid4()
    credential_id = uuid.uuid4()
    token = create_device_token(device_id=device_id, credential_id=credential_id)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    class Session:
        async def get(self, model, key):
            return DeviceCredential(
                id=key,
                device_id=device_id,
                secret_hash="hash",
                revoked_at=datetime.now(timezone.utc),
            )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_device(credentials=credentials, session=Session())

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_empty_ingest_ack_echoes_batch_identity():
    batch_id = uuid.uuid4()
    batch = IngestBatch(batch_id=batch_id, sequence=42, readings=[])

    result = await PipelineService(session=None).ingest_batch(batch, device_id=uuid.UUID("00000000-0000-0000-0000-000000000123"))  # type: ignore[arg-type]

    assert result.batch_id == batch_id
    assert result.sequence == 42
    assert result.idempotency_key == "00000000-0000-0000-0000-000000000123:" + str(batch_id) + ":42"
    assert result.accepted == []

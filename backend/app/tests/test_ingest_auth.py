import pytest
from fastapi import HTTPException
from app.auth.device import verify_ingest_key
from app.core.config import settings


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

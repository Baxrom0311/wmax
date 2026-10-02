from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.device import DevicePrincipal, get_current_device, verify_ingest_key
from app.core.db import get_session
from app.schemas.health_data import HealthDataBatch, HealthDataIngestResult
from app.repositories.reading_repo import ReadingRepository
from app.schemas.reading import IngestBatch, IngestResult
from app.services.health_data_service import HealthDataIngestService
from app.services.pipeline_service import PipelineService
from app.services.sos_service import SosService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ingest"])


class DeviceSosRequest(BaseModel):
    source: str = "watch_button"
    device_lat: float | None = None
    device_lon: float | None = None
    device_accuracy_m: float | None = None


@router.post(
    "/ingest/readings",
    response_model=IngestResult,
    status_code=status.HTTP_200_OK,
    summary="Batch upload of 5-minute aggregates using a per-device token.",
)
async def ingest_batch(
    batch: IngestBatch,
    device: DevicePrincipal = Depends(get_current_device),
    session: AsyncSession = Depends(get_session),
) -> IngestResult:
    """
    Accepts 5-minute physiological aggregates from wearable devices.
    Idempotent: duplicate (patient_id, ts) pairs are silently ignored.
    Triggers clinical signal evaluation pipeline on every accepted batch.
    """
    service = PipelineService(session)
    return await service.ingest_batch(batch, device_id=device.device_id)


@router.post(
    "/ingest/health-data",
    response_model=HealthDataIngestResult,
    status_code=status.HTTP_200_OK,
    summary="Batch upload of Wear OS Health Services and Health Connect records.",
)
async def ingest_health_data(
    batch: HealthDataBatch,
    device: DevicePrincipal = Depends(get_current_device),
    session: AsyncSession = Depends(get_session),
) -> HealthDataIngestResult:
    service = HealthDataIngestService(session)
    return await service.ingest_device_batch(batch, device_id=device.device_id)


@router.post(
    "/ingest/sos",
    status_code=status.HTTP_201_CREATED,
    summary="Raise SOS using a per-device token.",
)
async def ingest_sos(
    req: DeviceSosRequest,
    device: DevicePrincipal = Depends(get_current_device),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    assignment = await ReadingRepository(session).get_assignment_at(
        device.device_id,
        datetime.now(timezone.utc),
    )
    if assignment is None:
        return {
            "accepted": False,
            "reason": "orphan_device",
            "device_id": str(device.device_id),
        }
    service = SosService(session)
    event = await service.raise_sos(
        patient_id=assignment.patient_id,
        source=req.source,
        device_lat=req.device_lat,
        device_lon=req.device_lon,
        device_accuracy_m=req.device_accuracy_m,
    )
    await session.commit()
    return {
        "accepted": True,
        "id": str(event.id),
        "patient_id": str(assignment.patient_id),
        "source": event.source,
    }


@router.post(
    "/ingest",
    response_model=IngestResult,
    status_code=status.HTTP_200_OK,
    summary="Legacy fleet-key ingest endpoint kept for transitional clients.",
    dependencies=[Depends(verify_ingest_key)],
    include_in_schema=False,
)
async def ingest_batch_legacy(
    batch: IngestBatch,
    session: AsyncSession = Depends(get_session),
) -> IngestResult:
    service = PipelineService(session)
    return await service.ingest_batch(batch)

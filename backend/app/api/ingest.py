from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.schemas.reading import IngestBatch, IngestResult
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post(
    "/ingest",
    response_model=IngestResult,
    status_code=status.HTTP_200_OK,
    summary="Batch upload of 5-minute aggregates. Idempotent (UNIQUE patient_id, ts).",
)
async def ingest_batch(
    batch: IngestBatch,
    session: AsyncSession = Depends(get_session),
) -> IngestResult:
    """
    Accepts 5-minute physiological aggregates from wearable devices.
    Idempotent: duplicate (patient_id, ts) pairs are silently ignored.
    Triggers clinical signal evaluation pipeline on every accepted batch.
    """
    service = PipelineService(session)
    return await service.ingest_batch(batch)

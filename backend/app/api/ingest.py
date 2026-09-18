from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models import Reading
from app.schemas.reading import IngestBatch, IngestResult
from app.services.pipeline import run_pipeline_for_patient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post(
    "/ingest",
    response_model=IngestResult,
    status_code=status.HTTP_200_OK,
    summary="Batch upload of 5-minute aggregates. Idempotent.",
)
async def ingest_batch(
    batch: IngestBatch,
    session: AsyncSession = Depends(get_session),
) -> IngestResult:
    if not batch.readings:
        return IngestResult(accepted=0, duplicates=0, latest_level="no_data")

    records = [
        {
            "patient_id": batch.patient_id,
            "ts": r.ts,
            "hr_mean": r.hr_mean,
            "hr_min": r.hr_min,
            "hr_max": r.hr_max,
            "rmssd": r.rmssd,
            "sdnn": r.sdnn,
            "spo2": r.spo2,
            "skin_temp": r.skin_temp,
            "steps": r.steps,
            "rr_est": r.rr_est,
            "sleep_frag": r.sleep_frag,
            "worn": r.worn,
            "battery": r.battery,
        }
        for r in batch.readings
    ]

    total_submitted = len(records)

    # Idempotent insert with on_conflict_do_nothing
    stmt = (
        insert(Reading)
        .values(records)
        .on_conflict_do_nothing(index_elements=["patient_id", "ts"])
    )
    result = await session.execute(stmt)
    await session.commit()

    accepted = result.rowcount if result.rowcount >= 0 else total_submitted
    duplicates = max(0, total_submitted - accepted)

    # Run clinical signal pipeline
    alert_result = await run_pipeline_for_patient(session, batch.patient_id)

    return IngestResult(
        accepted=accepted,
        duplicates=duplicates,
        latest_level=alert_result.level,
    )

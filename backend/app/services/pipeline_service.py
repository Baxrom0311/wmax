from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import (
    AMBER_THRESHOLD,
    CRITICAL_HR_AT_REST,
    CRITICAL_SPO2,
    MIN_TRIGGERED_PARAMS,
    PARAM_DIRECTION,
    RED_THRESHOLD,
    REST_STEPS_MAX,
    WEIGHTS,
    Z_DEADZONE,
    AlertResult,
    BaselineEntry,
    ReadingVec,
    TrendResult,
)
from app.core.exceptions import NotFoundException
from app.core.metrics import alerts_total, readings_ingested_total
from app.models.patient import Patient
from app.repositories.alert_repo import AlertRepository
from app.repositories.baseline_repo import BaselineRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.reading_repo import ReadingRepository
from app.schemas.reading import IngestBatch, IngestItem, IngestResult
from app.services.clinical_math import compute_trend_pure

logger = logging.getLogger(__name__)

# Direct imports from algo package (A2 integration point)
from algo.baseline import compute_baselines, compute_zscores
from algo.signal import evaluate_alert
from algo.trend import compute_trend


class PipelineService:
    """Production service coordinating clinical ingestion, baseline calculation, and alerting."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.reading_repo = ReadingRepository(session)
        self.baseline_repo = BaselineRepository(session)
        self.alert_repo = AlertRepository(session)

    async def ingest_batch(self, batch: IngestBatch) -> IngestResult:
        """Ingests a 5-minute aggregate batch idempotently and triggers clinical evaluation."""
        if not batch.readings:
            return IngestResult(accepted=0, duplicates=0, latest_level="no_data")

        # Map to dicts for repository idempotent insert
        reading_dicts = [
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

        accepted, duplicates = await self.reading_repo.insert_batch_idempotent(reading_dicts)
        readings_ingested_total.inc(accepted)

        # Run clinical evaluation pipeline
        alert_result = await self.evaluate_patient(batch.patient_id)

        return IngestResult(
            accepted=accepted,
            duplicates=duplicates,
            latest_level=alert_result.level,
        )

    async def evaluate_patient(self, patient_id: uuid.UUID) -> AlertResult:
        """Evaluates clinical signal for the patient, persists baselines and alerts."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            return AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="patient_not_found",
            )

        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)

        # Read last 7 days of readings
        readings = await self.reading_repo.get_readings_since(patient_id, since)
        if not readings:
            return AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="no_readings",
            )

        latest_reading = readings[-1]

        # 45 minutes of silence -> no_data, not green
        if timewin.is_no_data(latest_reading.ts, now):
            no_data_result = AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            )
            await self.alert_repo.insert_idempotent(
                patient_id=patient_id,
                ts=latest_reading.ts,
                result=no_data_result,
            )
            return AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            )

        # Convert to ReadingVec for pure clinical functions
        vecs = [
            ReadingVec(
                ts=r.ts,
                hr_mean=r.hr_mean,
                hr_min=r.hr_min,
                hr_max=r.hr_max,
                rmssd=r.rmssd,
                sdnn=r.sdnn,
                spo2=r.spo2,
                skin_temp=r.skin_temp,
                steps=r.steps,
                rr_est=r.rr_est,
                sleep_frag=r.sleep_frag,
                worn=r.worn,
            )
            for r in readings
        ]

        # Personal baseline — learned, then frozen.
        #
        # While the patient is still being learned, the baseline is recomputed
        # from recent readings. Once a doctor signs it off
        # (`baseline_approved_at`), it is *loaded* rather than recomputed:
        # continuing to recompute lets the reference drift along with a
        # deteriorating patient, so their new and worse state quietly becomes
        # "normal" and the signal never fires. That is the exact failure this
        # system exists to prevent.
        #
        # The repository reads attributes off BaselineEntry directly, so the
        # old dict conversion here raised AttributeError on every call —
        # baselines were never persisted at all.
        stored = await self.baseline_repo.get_by_patient(patient_id)
        if patient.baseline_approved_at is not None and stored:
            baselines = [
                BaselineEntry(
                    param=b.param,
                    time_window=b.time_window,
                    median=b.median,
                    mad=b.mad,
                    n_samples=b.n_samples,
                )
                for b in stored
            ]
        else:
            baselines = compute_baselines(vecs)
            await self.baseline_repo.upsert_baselines(patient_id, baselines)

        # Recent z-scores for 15-minute persistence check
        recent_vecs = vecs[-3:-1] if len(vecs) >= 3 else []
        recent_zscores = [compute_zscores(rv, baselines) for rv in recent_vecs]

        # Evaluate alert
        alert_result = evaluate_alert(
            reading=vecs[-1],
            baselines=baselines,
            recent_zscores=recent_zscores,
            phase=patient.phase,
        )

        # Persist alert idempotently
        await self.alert_repo.insert_idempotent(
            patient_id=patient_id,
            ts=latest_reading.ts,
            result=alert_result,
        )
        alerts_total.labels(level=alert_result.level).inc()

        return alert_result


# Backward compatibility wrapper
async def run_pipeline_for_patient(
    session: AsyncSession, patient_id: uuid.UUID
) -> AlertResult:
    service = PipelineService(session)
    return await service.evaluate_patient(patient_id)

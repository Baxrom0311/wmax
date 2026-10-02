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
from app.schemas.reading import IngestAck, IngestBatch, IngestItem, IngestResult
from app.services.clinical_math import compute_trend_pure
from app.services.compat import to_reading_vec
from app.services.live_event_service import LiveEventService

logger = logging.getLogger(__name__)

# Direct imports from algo package (A2 integration point)
from algo.baseline import compute_baselines, compute_zscores
from algo.signal import evaluate_alert
from algo.trend import compute_trend


def _previous_consecutive_windows(readings: Sequence[Any]) -> list[Any]:
    """Return the two prior windows only when all three windows are contiguous."""
    if len(readings) < 3:
        return []

    recent = readings[-3:]
    for previous, current in zip(recent, recent[1:]):
        previous_end = getattr(previous, "window_end", None)
        current_start = getattr(current, "window_start", getattr(current, "ts", None))
        if previous_end is not None and current_start is not None:
            if previous_end != current_start:
                return []
            continue

        previous_start = getattr(previous, "window_start", getattr(previous, "ts", None))
        if previous_start is None or current_start is None:
            return []
        if current_start - previous_start != timedelta(minutes=5):
            return []
    return recent[:-1]


class PipelineService:
    """Production service coordinating clinical ingestion, baseline calculation, and alerting."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.reading_repo = ReadingRepository(session)
        self.baseline_repo = BaselineRepository(session)
        self.alert_repo = AlertRepository(session)

    async def ingest_batch(
        self, batch: IngestBatch, device_id: uuid.UUID | None = None
    ) -> IngestResult:
        """Ingests a 5-minute aggregate batch idempotently and triggers clinical evaluation."""
        server_time = datetime.now(timezone.utc)
        if not batch.readings:
            return IngestResult(
                server_time=server_time,
                batch_id=batch.batch_id,
                sequence=batch.sequence,
                idempotency_key=self._batch_idempotency_key(batch=batch, device_id=device_id),
            )

        accepted: list[datetime] = []
        duplicate: list[datetime] = []
        orphaned: list[datetime] = []
        rejected: list[IngestAck] = []
        patient_ids: set[uuid.UUID] = set()

        for reading in batch.readings:
            window_start = reading.window_start
            window_end = reading.window_end
            if window_start is None or window_end is None:
                rejected.append(IngestAck(window_start=server_time, reason="window_required"))
                continue
            if window_end <= window_start:
                rejected.append(IngestAck(window_start=window_start, reason="bad_window"))
                continue

            assignment = None
            patient_id = batch.patient_id
            if device_id is not None:
                assignment = await self.reading_repo.get_assignment_at(device_id, window_start)
                patient_id = assignment.patient_id if assignment else None

            if patient_id is None or device_id is None:
                if device_id is not None:
                    inserted = await self.reading_repo.insert_orphan_idempotent(
                        {
                            "device_id": device_id,
                            "window_start": window_start,
                            "payload": reading.model_dump(mode="json"),
                        }
                    )
                    target = orphaned if inserted else duplicate
                    target.append(window_start)
                else:
                    rejected.append(IngestAck(window_start=window_start, reason="device_required"))
                continue

            clock_offset_ms = None
            if batch.device_clock_utc is not None:
                clock_offset_ms = int((server_time - batch.device_clock_utc).total_seconds() * 1000)

            inserted, dupes = await self.reading_repo.insert_batch_idempotent(
                [
                    {
                        "patient_id": patient_id,
                        "device_id": device_id,
                        "device_assignment_id": assignment.id if assignment else None,
                        "window_start": window_start,
                        "window_end": window_end,
                        "hr_mean": reading.hr_mean,
                        "hr_min": reading.hr_min,
                        "hr_max": reading.hr_max,
                        "rmssd": reading.rmssd,
                        "sdnn": reading.sdnn,
                        "spo2": reading.spo2,
                        "skin_temp": reading.skin_temp,
                        "steps": reading.steps,
                        "rr_est": reading.rr_est,
                        "sleep_frag": reading.sleep_frag,
                        "worn": reading.worn,
                        "worn_pct": reading.worn_pct,
                        "samples_n": reading.samples_n,
                        "battery": reading.battery,
                        "device_clock_utc": batch.device_clock_utc,
                        "clock_offset_ms": clock_offset_ms,
                        "provenance": assignment.provenance if assignment else "unknown",
                        "attributed_by": "device_assignment" if assignment else None,
                    }
                ]
            )
            if inserted:
                accepted.append(window_start)
                patient_ids.add(patient_id)
                readings_ingested_total.inc(inserted)
            elif dupes:
                duplicate.append(window_start)

        for patient_id in patient_ids:
            await self.evaluate_patient(patient_id)

        await LiveEventService(self.session).publish_reading_batch(
            accepted=[item.isoformat() for item in accepted],
            duplicate=[item.isoformat() for item in duplicate],
            orphaned=[item.isoformat() for item in orphaned],
            rejected=[item.model_dump(mode="json") for item in rejected],
        )

        return IngestResult(
            server_time=server_time,
            batch_id=batch.batch_id,
            sequence=batch.sequence,
            idempotency_key=self._batch_idempotency_key(batch=batch, device_id=device_id),
            accepted=accepted,
            duplicate=duplicate,
            orphaned=orphaned,
            rejected=rejected,
        )

    def _batch_idempotency_key(
        self, *, batch: IngestBatch, device_id: uuid.UUID | None
    ) -> str:
        owner = str(device_id or batch.patient_id or "unknown")
        return f"{owner}:{batch.batch_id}:{batch.sequence if batch.sequence is not None else 'none'}"

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
        latest_ts = getattr(latest_reading, "window_start", getattr(latest_reading, "ts", None))
        if latest_ts is None:
            latest_ts = now

        if timewin.is_no_data(latest_ts, now):
            no_data_result = AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            )
            alert = await self.alert_repo.insert_idempotent(
                patient_id=patient_id,
                ts=latest_ts,
                result=no_data_result,
            )
            if alert:
                await LiveEventService(self.session).publish_alert(alert)
            return AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            )

        # Convert to ReadingVec for pure clinical functions
        vecs = [to_reading_vec(reading) for reading in readings]

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
        recent_readings = _previous_consecutive_windows(readings)
        recent_vecs = vecs[-1 - len(recent_readings):-1] if recent_readings else []
        recent_zscores = [compute_zscores(rv, baselines) for rv in recent_vecs]

        # Evaluate alert
        alert_result = evaluate_alert(
            reading=vecs[-1],
            baselines=baselines,
            recent_zscores=recent_zscores,
            phase=patient.phase,
        )

        # Persist alert idempotently
        alert = await self.alert_repo.insert_idempotent(
            patient_id=patient_id,
            ts=latest_ts,
            result=alert_result,
        )
        if alert:
            await LiveEventService(self.session).publish_alert(alert)
        alerts_total.labels(level=alert_result.level).inc()

        return alert_result


# Backward compatibility wrapper
async def run_pipeline_for_patient(
    session: AsyncSession, patient_id: uuid.UUID
) -> AlertResult:
    service = PipelineService(session)
    return await service.evaluate_patient(patient_id)

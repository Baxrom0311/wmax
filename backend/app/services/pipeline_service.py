from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from collections.abc import Sequence
from itertools import pairwise
from typing import Any

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo.baseline import compute_baselines, compute_zscores
from algo.signal import evaluate_alert
from algo_interface import AlertResult, BaselineEntry
from app.core.metrics import alerts_total, readings_ingested_total
from app.models.schema import PatientMembership, TenantMember
from app.repositories.alert_repo import AlertRepository
from app.repositories.baseline_repo import BaselineRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.reading_repo import ReadingRepository
from app.repositories.task_repo import TaskRepository
from app.schemas.reading import IngestAck, IngestBatch, IngestResult
from app.services.compat import to_reading_vec
from app.services.live_event_service import LiveEventService

logger = logging.getLogger(__name__)

def _previous_consecutive_windows(readings: Sequence[Any]) -> list[Any]:
    """Return the two prior windows only when all three windows are contiguous."""
    if len(readings) < 3:
        return []

    recent = readings[-3:]
    for previous, current in pairwise(recent):
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
        self.task_repo = TaskRepository(session)

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
        accepted_by_patient: dict[uuid.UUID, list[str]] = {}
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
                assignment = await self.reading_repo.get_assignment_covering(
                    device_id, window_start, window_end
                )
                patient_id = assignment.patient_id if assignment else None

            if patient_id is None or device_id is None:
                if device_id is not None:
                    if await self.reading_repo.get_assignment_at(device_id, window_start):
                        rejected.append(
                            IngestAck(
                                window_start=window_start,
                                reason="assignment_boundary",
                            )
                        )
                        continue
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
                accepted_by_patient.setdefault(patient_id, []).append(
                    window_start.isoformat()
                )
                patient_ids.add(patient_id)
                readings_ingested_total.inc(inserted)
            elif dupes:
                duplicate.append(window_start)

        for patient_id in patient_ids:
            await self.evaluate_patient(patient_id)

        event_service = LiveEventService(self.session)
        for patient_id, windows in accepted_by_patient.items():
            await event_service.publish_patient_readings(patient_id, windows)

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
        if not patient or getattr(patient, "deceased_at", None) is not None:
            return AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="patient_deceased" if (patient and getattr(patient, "deceased_at", None) is not None) else "patient_not_found",
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
            if alert_result.level in {"amber", "red"}:
                await self._create_alert_task(patient=patient, alert=alert, result=alert_result)
        alerts_total.labels(level=alert_result.level).inc()

        return alert_result

    async def _create_alert_task(
        self, patient: Any, alert: Any, result: AlertResult
    ) -> None:
        try:
            open_task = await self.task_repo.get_open_task(patient.id)
            if open_task:
                return

            membership = (
                await self.session.execute(
                    select(PatientMembership).where(
                        PatientMembership.patient_id == patient.id,
                        PatientMembership.kind == "care",
                        PatientMembership.revoked_at.is_(None),
                    )
                )
            ).scalar_one_or_none()

            tenant_id = membership.tenant_id if membership else getattr(patient, "tenant_id", None)
            if not tenant_id:
                return

            # 1. First priority: patient's explicitly assigned doctor or care owner
            assignee_id = getattr(patient, "doctor_id", None)
            if assignee_id:
                eligible = (
                    await self.session.execute(
                        select(TenantMember.id).where(
                            TenantMember.account_id == assignee_id,
                            TenantMember.tenant_id == tenant_id,
                            TenantMember.left_at.is_(None),
                            TenantMember.role.in_(["doctor", "head_doctor"]),
                        ).limit(1)
                    )
                ).scalar_one_or_none()
                if eligible is None:
                    logger.warning(
                        "Assigned doctor %s is not an active eligible member of tenant %s for patient %s",
                        assignee_id,
                        tenant_id,
                        patient.id,
                    )
                    assignee_id = None

            # 2. Second priority: active clinician (doctor, nurse, head_doctor) in the tenant
            if not assignee_id:
                clinician_member = (
                    await self.session.execute(
                        select(TenantMember).where(
                            TenantMember.tenant_id == tenant_id,
                            TenantMember.left_at.is_(None),
                            TenantMember.role.in_(["doctor", "nurse", "head_doctor"]),
                        ).order_by(
                            case(
                                (TenantMember.role == "doctor", 0),
                                (TenantMember.role == "head_doctor", 1),
                                (TenantMember.role == "nurse", 2),
                                else_=3,
                            ),
                            TenantMember.joined_at.asc(),
                        ).limit(1)
                    )
                ).scalar_one_or_none()
                if clinician_member:
                    assignee_id = clinician_member.account_id

            if not assignee_id:
                logger.warning("No eligible clinician found in tenant %s for alert on patient %s", tenant_id, patient.id)
                return

            now = datetime.now(timezone.utc)
            due_at = now + (timedelta(hours=2) if result.level == "red" else timedelta(hours=24))
            await self.task_repo.create_task(
                patient_id=patient.id,
                tenant_id=tenant_id,
                assignee_account_id=assignee_id,
                due_at=due_at,
                kind="clinical",
                alert_id=getattr(alert, "id", None),
                note=f"Avtomatik klinik signal: {result.level.upper()}",
            )
        except Exception as e:
            logger.warning(f"Could not create task for alert on patient {patient.id}: {e}")


# Backward compatibility wrapper
async def run_pipeline_for_patient(
    session: AsyncSession, patient_id: uuid.UUID
) -> AlertResult:
    service = PipelineService(session)
    return await service.evaluate_patient(patient_id)

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.health_quality import sample_quality_flags
from app.domain.device_assignment import assignment_covers_interval
from app.models import (
    DeviceSyncEvent,
    ExerciseSession,
    HealthSample,
    PatientConsent,
    PatientMembership,
    Reading,
    SleepSession,
)
from app.repositories.reading_repo import ReadingRepository
from app.schemas.health_data import HealthDataBatch, HealthDataIngestResult
from app.services.pipeline_service import PipelineService


class HealthDataIngestService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.readings = ReadingRepository(session)

    async def ingest_device_batch(
        self,
        batch: HealthDataBatch,
        *,
        device_id: uuid.UUID,
    ) -> HealthDataIngestResult:
        accepted = 0
        duplicate = 0
        rejected: list[dict[str, str]] = []
        received_at = datetime.now(timezone.utc)
        event_times = (
            [time for sample in batch.samples for time in (
                sample.recorded_at, sample.started_at, sample.ended_at
            ) if time is not None]
            + [time for session in batch.sleep_sessions for time in (
                session.start_time, session.end_time
            )]
            + [time for session in batch.exercise_sessions for time in (
                session.start_time, session.end_time
            )]
        )
        assignments = (
            await self.readings.get_assignments_for_device_range(
                device_id, min(event_times), max(event_times)
            )
            if event_times
            else []
        )
        assigned_patient_ids = {assignment.patient_id for assignment in assignments}
        consented_patient_ids: set[uuid.UUID] = set()
        if assigned_patient_ids:
            consent_result = await self.session.execute(
                select(PatientConsent.patient_id)
                .join(PatientMembership, PatientMembership.patient_id == PatientConsent.patient_id)
                .where(
                    PatientConsent.patient_id.in_(assigned_patient_ids),
                    PatientConsent.scope == "clinical_monitoring",
                    PatientConsent.granted.is_(True),
                    PatientConsent.revoked_at.is_(None),
                    PatientMembership.kind == "care",
                    PatientMembership.revoked_at.is_(None),
                    (PatientConsent.target_tenant_id.is_(None)
                     | (PatientConsent.target_tenant_id == PatientMembership.tenant_id)),
                )
                .distinct()
            )
            consented_patient_ids = set(consent_result.scalars().all())

        def assignment_at(recorded_at: datetime) -> Any | None:
            return next(
                (
                    assignment
                    for assignment in reversed(assignments)
                    if assignment.assigned_at <= recorded_at
                    and (
                        assignment.released_at is None
                        or recorded_at < assignment.released_at
                    )
                ),
                None,
            )

        def assignment_covering(start: datetime, end: datetime) -> Any | None:
            return next(
                (
                    assignment
                    for assignment in reversed(assignments)
                    if assignment_covers_interval(assignment, start, end)
                ),
                None,
            )

        sample_rows: list[dict[str, Any]] = []
        sleep_rows: list[dict[str, Any]] = []
        exercise_rows: list[dict[str, Any]] = []

        for index, sample in enumerate(batch.samples):
            quality_flags = sample_quality_flags(sample, received_at=received_at)
            start = sample.started_at or sample.recorded_at
            end = sample.ended_at or sample.recorded_at
            assignment = assignment_covering(start, end)
            if assignment is not None and not (
                start <= sample.recorded_at <= end
            ):
                assignment = None
            if assignment is None:
                point_assignment = assignment_at(sample.recorded_at)
                reason = "assignment_boundary" if point_assignment else "orphan_device"
                rejected.append({"kind": "sample", "index": str(index), "reason": reason})
                continue
            if assignment.patient_id not in consented_patient_ids:
                rejected.append({"kind": "sample", "index": str(index), "reason": "consent_missing_or_revoked"})
                continue
            key = self._key(
                device_id=device_id,
                source=batch.source,
                source_record_id=sample.source_record_id,
                kind="sample",
                natural=f"{sample.metric}:{sample.recorded_at.isoformat()}",
            )
            sample_rows.append(
                {
                    "idempotency_key": key,
                    "patient_id": assignment.patient_id,
                    "device_id": device_id,
                    "device_assignment_id": assignment.id,
                    "source": batch.source,
                    "source_record_id": sample.source_record_id,
                    "metric": sample.metric,
                    "unit": sample.unit,
                    "value_num": sample.value_num,
                    "value_text": sample.value_text,
                    "started_at": sample.started_at,
                    "recorded_at": sample.recorded_at,
                    "ended_at": sample.ended_at,
                    "quality": sample.quality,
                    "metadata_json": {
                        **{
                            key: value
                            for key, value in sample.metadata.items()
                            if key != "ingest_quality_flags"
                        },
                        **(
                            {"ingest_quality_flags": list(quality_flags)}
                            if quality_flags
                            else {}
                        ),
                    },
                }
            )

        for index, sleep_session in enumerate(batch.sleep_sessions):
            assignment = assignment_covering(
                sleep_session.start_time, sleep_session.end_time
            )
            if assignment is None:
                reason = (
                    "assignment_boundary"
                    if assignment_at(sleep_session.start_time)
                    else "orphan_device"
                )
                rejected.append({"kind": "sleep_session", "index": str(index), "reason": reason})
                continue
            if assignment.patient_id not in consented_patient_ids:
                rejected.append({"kind": "sleep_session", "index": str(index), "reason": "consent_missing_or_revoked"})
                continue
            key = self._key(
                device_id=device_id,
                source=batch.source,
                source_record_id=sleep_session.source_record_id,
                kind="sleep",
                natural=f"{sleep_session.start_time.isoformat()}:{sleep_session.end_time.isoformat()}",
            )
            sleep_rows.append(
                {
                    "idempotency_key": key,
                    "patient_id": assignment.patient_id,
                    "device_id": device_id,
                    "source": batch.source,
                    "source_record_id": sleep_session.source_record_id,
                    "start_time": sleep_session.start_time,
                    "end_time": sleep_session.end_time,
                    "stages": [stage.model_dump(mode="json") for stage in sleep_session.stages],
                    "metrics": sleep_session.metrics,
                    "metadata_json": sleep_session.metadata,
                }
            )

        for index, exercise_session in enumerate(batch.exercise_sessions):
            assignment = assignment_covering(
                exercise_session.start_time, exercise_session.end_time
            )
            if assignment is None:
                reason = (
                    "assignment_boundary"
                    if assignment_at(exercise_session.start_time)
                    else "orphan_device"
                )
                rejected.append({"kind": "exercise_session", "index": str(index), "reason": reason})
                continue
            if assignment.patient_id not in consented_patient_ids:
                rejected.append({"kind": "exercise_session", "index": str(index), "reason": "consent_missing_or_revoked"})
                continue
            key = self._key(
                device_id=device_id,
                source=batch.source,
                source_record_id=exercise_session.source_record_id,
                kind="exercise",
                natural=f"{exercise_session.exercise_type}:{exercise_session.start_time.isoformat()}:{exercise_session.end_time.isoformat()}",
            )
            exercise_rows.append(
                {
                    "idempotency_key": key,
                    "patient_id": assignment.patient_id,
                    "device_id": device_id,
                    "source": batch.source,
                    "source_record_id": exercise_session.source_record_id,
                    "exercise_type": exercise_session.exercise_type,
                    "start_time": exercise_session.start_time,
                    "end_time": exercise_session.end_time,
                    "metrics": exercise_session.metrics,
                    "route": exercise_session.route,
                    "metadata_json": exercise_session.metadata,
                }
            )

        inserted_sample_keys = await self._insert_sample_rows(sample_rows)
        inserted_samples = len(inserted_sample_keys)
        if inserted_sample_keys:
            # A replay must not double-count step deltas or sample values.
            await self._aggregate_samples_to_readings(
                [row for row in sample_rows if row["idempotency_key"] in inserted_sample_keys]
            )

        inserted_sleep = await self._insert_many(
            SleepSession, sleep_rows, "uq_sleep_session_idempotency"
        )
        inserted_exercise = await self._insert_many(
            ExerciseSession, exercise_rows, "uq_exercise_session_idempotency"
        )
        accepted = inserted_samples + inserted_sleep + inserted_exercise
        duplicate = (
            len(sample_rows) + len(sleep_rows) + len(exercise_rows) - accepted
        )

        await self._record_sync_event(
            device_id=device_id,
            source=batch.source,
            batch_id=str(batch.batch_id),
            sequence=batch.sequence,
            accepted_count=accepted,
            duplicate_count=duplicate,
            rejected_count=len(rejected),
            metadata=batch.metadata,
        )
        await self.session.commit()

        return HealthDataIngestResult(
            server_time=datetime.now(timezone.utc),
            batch_id=batch.batch_id,
            accepted=accepted,
            duplicate=duplicate,
            rejected=rejected,
        )

    async def _insert_many(
        self, model: Any, rows: list[dict[str, Any]], constraint: str
    ) -> int:
        if not rows:
            return 0
        stmt = insert(model).values(rows).on_conflict_do_nothing(constraint=constraint)
        result = await self.session.execute(stmt)
        await self.session.flush()
        rowcount = result.rowcount
        return rowcount if rowcount is not None and rowcount >= 0 else len(rows)

    async def _insert_sample_rows(self, rows: list[dict[str, Any]]) -> set[str]:
        if not rows:
            return set()
        stmt = (
            insert(HealthSample)
            .values(rows)
            .on_conflict_do_nothing(constraint="uq_health_sample_idempotency")
            .returning(HealthSample.idempotency_key)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return set(result.scalars().all())

    async def _record_sync_event(
        self,
        *,
        device_id: uuid.UUID,
        source: str,
        batch_id: str,
        sequence: int | None,
        accepted_count: int,
        duplicate_count: int,
        rejected_count: int,
        metadata: dict,
    ) -> None:
        stmt = insert(DeviceSyncEvent).values(
            {
                "device_id": device_id,
                "source": source,
                "batch_id": batch_id,
                "sequence": sequence,
                "accepted_count": accepted_count,
                "duplicate_count": duplicate_count,
                "rejected_count": rejected_count,
                "metadata_json": metadata,
            }
        ).on_conflict_do_nothing(constraint="uq_device_sync_batch")
        await self.session.execute(stmt)
        await self.session.flush()

    def _key(
        self,
        *,
        device_id: uuid.UUID,
        source: str,
        source_record_id: str | None,
        kind: str,
        natural: str,
    ) -> str:
        # One provider record may contain many points; include the point's own
        # identity so those points do not collapse into a single database row.
        raw = f"{device_id}:{source}:{source_record_id or ''}:{natural}:{kind}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _aggregate_samples_to_readings(
        self, sample_rows: list[dict[str, Any]]
    ) -> None:
        windows: dict[tuple[uuid.UUID, uuid.UUID, datetime], dict[str, Any]] = {}
        affected_patients: set[uuid.UUID] = set()

        for row in sample_rows:
            metric = row.get("metric")
            val = row.get("value_num")
            flags = set((row.get("metadata_json") or {}).get("ingest_quality_flags", []))
            if row.get("quality") is not None and row["quality"] < 0.5:
                flags.add("low_quality")
            if flags.intersection({"missing_unit", "unexpected_unit", "value_out_of_expected_range", "recorded_at_in_future"}):
                continue

            patient_id = row["patient_id"]
            device_id = row["device_id"]
            recorded_at = row["recorded_at"]
            affected_patients.add(patient_id)

            win_start = recorded_at.replace(second=0, microsecond=0)
            win_start = win_start.replace(minute=(win_start.minute // 5) * 5)
            key = (patient_id, device_id, win_start)

            if key not in windows:
                windows[key] = {
                    "patient_id": patient_id,
                    "device_id": device_id,
                    "device_assignment_id": row.get("device_assignment_id"),
                    "window_start": win_start,
                    "window_end": win_start + timedelta(minutes=5),
                    "hr_list": [],
                    "spo2_list": [],
                    "temp_list": [],
                    "steps": 0,
                    "worn_state": None,
                }

            if metric == "worn_state":
                state = str(row.get("value_text", row.get("value_num", ""))).lower()
                if state in {"true", "worn", "on", "1"}:
                    windows[key]["worn_state"] = True
                elif state in {"false", "not_worn", "off", "0"}:
                    windows[key]["worn_state"] = False
            if val is not None:
                if metric in ("heart_rate_bpm", "resting_heart_rate_bpm"):
                    windows[key]["hr_list"].append(float(val))
                elif metric == "oxygen_saturation_pct":
                    windows[key]["spo2_list"].append(float(val))
                elif metric in ("skin_temperature_c", "body_temperature_c"):
                    windows[key]["temp_list"].append(float(val))
                elif metric in ("steps", "daily_steps"):
                    windows[key]["steps"] += int(val)

        reading_records: list[dict[str, Any]] = []
        for (pat_id, dev_id, w_start), data in windows.items():
            hr_list = data["hr_list"]
            spo2_list = data["spo2_list"]
            temp_list = data["temp_list"]

            reading_records.append(
                {
                    "patient_id": pat_id,
                    "device_id": dev_id,
                    "device_assignment_id": data["device_assignment_id"],
                    "window_start": w_start,
                    "window_end": data["window_end"],
                    "hr_mean": round(sum(hr_list) / len(hr_list), 1) if hr_list else None,
                    "hr_min": round(min(hr_list), 1) if hr_list else None,
                    "hr_max": round(max(hr_list), 1) if hr_list else None,
                    "spo2": round(sum(spo2_list) / len(spo2_list), 1) if spo2_list else None,
                    "skin_temp": round(sum(temp_list) / len(temp_list), 1) if temp_list else None,
                    "steps": data["steps"],
                    # A valid physiological measurement implies the sensor had
                    # contact, unless the source explicitly reported unworn.
                    "worn": data["worn_state"] if data["worn_state"] is not None else bool(hr_list or spo2_list),
                }
            )

        if reading_records:
            await self._insert_many(Reading, reading_records, "uq_reading_key")

        pipeline = PipelineService(self.session)
        for p_id in affected_patients:
            await pipeline.evaluate_patient(p_id)

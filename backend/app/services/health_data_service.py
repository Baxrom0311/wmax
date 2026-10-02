from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.health_quality import sample_quality_flags
from app.models import DeviceSyncEvent, ExerciseSession, HealthSample, SleepSession
from app.repositories.reading_repo import ReadingRepository
from app.schemas.health_data import HealthDataBatch, HealthDataIngestResult


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
            [sample.recorded_at for sample in batch.samples]
            + [session.start_time for session in batch.sleep_sessions]
            + [session.start_time for session in batch.exercise_sessions]
        )
        assignments = (
            await self.readings.get_assignments_for_device_range(
                device_id, min(event_times), max(event_times)
            )
            if event_times
            else []
        )

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

        sample_rows: list[dict[str, Any]] = []
        sleep_rows: list[dict[str, Any]] = []
        exercise_rows: list[dict[str, Any]] = []

        for index, sample in enumerate(batch.samples):
            quality_flags = sample_quality_flags(sample, received_at=received_at)
            assignment = assignment_at(sample.recorded_at)
            if assignment is None:
                rejected.append({"kind": "sample", "index": str(index), "reason": "orphan_device"})
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
            assignment = assignment_at(sleep_session.start_time)
            if assignment is None:
                rejected.append({"kind": "sleep_session", "index": str(index), "reason": "orphan_device"})
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
            assignment = assignment_at(exercise_session.start_time)
            if assignment is None:
                rejected.append({"kind": "exercise_session", "index": str(index), "reason": "orphan_device"})
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

        inserted_samples = await self._insert_many(
            HealthSample, sample_rows, "uq_health_sample_idempotency"
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

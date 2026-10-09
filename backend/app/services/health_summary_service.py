from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.health_summary import (
    SPARSE_LOOKBACK_DAYS,
    SPARSE_METRICS,
    SUMMARY_METRICS,
    ExerciseRow,
    SampleRow,
    SleepRow,
    build_health_summary,
)
from app.models import ExerciseSession, HealthSample, SleepSession
from app.schemas.health_summary import HealthSummary


class HealthSummaryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(
        self,
        patient_id: uuid.UUID,
        *,
        days: int,
        now: datetime | None = None,
    ) -> HealthSummary:
        now = now or datetime.now(timezone.utc)
        # One extra day covers the local-midnight offset from UTC.
        since = now - timedelta(days=days + 1)
        sparse_since = now - timedelta(days=SPARSE_LOOKBACK_DAYS)
        dense_metrics = [m for m in SUMMARY_METRICS if m not in SPARSE_METRICS]

        columns = (
            HealthSample.metric,
            HealthSample.recorded_at,
            HealthSample.value_num,
            HealthSample.value_text,
            HealthSample.source,
            HealthSample.started_at,
            HealthSample.ended_at,
            HealthSample.quality,
            HealthSample.metadata_json,
        )
        dense = await self.session.execute(
            select(*columns).where(
                HealthSample.patient_id == patient_id,
                HealthSample.metric.in_(dense_metrics),
                HealthSample.recorded_at >= since,
                HealthSample.recorded_at <= now + timedelta(minutes=5),
            )
        )
        sparse = await self.session.execute(
            select(*columns).where(
                HealthSample.patient_id == patient_id,
                HealthSample.metric.in_(SPARSE_METRICS),
                HealthSample.recorded_at >= sparse_since,
                HealthSample.recorded_at <= now + timedelta(minutes=5),
            )
        )
        samples = [
            SampleRow(
                metric=row.metric,
                recorded_at=row.recorded_at,
                value_num=row.value_num,
                value_text=row.value_text,
                source=row.source,
                started_at=row.started_at,
                ended_at=row.ended_at,
                quality=row.quality,
                metadata=row.metadata_json or {},
            )
            for result in (dense, sparse)
            for row in result.all()
        ]

        sleep_rows = (
            await self.session.execute(
                select(SleepSession).where(
                    SleepSession.patient_id == patient_id,
                    SleepSession.end_time >= since,
                )
            )
        ).scalars().all()
        exercise_rows = (
            await self.session.execute(
                select(ExerciseSession).where(
                    ExerciseSession.patient_id == patient_id,
                    ExerciseSession.end_time >= since,
                )
            )
        ).scalars().all()

        summary = build_health_summary(
            samples,
            [
                SleepRow(
                    start_time=row.start_time,
                    end_time=row.end_time,
                    source=row.source,
                    stages=list(row.stages or []),
                )
                for row in sleep_rows
            ],
            [
                ExerciseRow(
                    exercise_type=row.exercise_type,
                    start_time=row.start_time,
                    end_time=row.end_time,
                    source=row.source,
                    metrics=row.metrics or {},
                )
                for row in exercise_rows
            ],
            now=now,
            days=days,
        )
        return HealthSummary.model_validate({"patient_id": str(patient_id), **summary})

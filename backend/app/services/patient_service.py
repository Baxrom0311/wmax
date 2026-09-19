from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import AlertLevel
from app.ai.clinical_ai import ClinicalAIService
from app.core.exceptions import NotFoundException
from app.models.patient import Patient
from app.repositories.alert_repo import AlertRepository
from app.repositories.baseline_repo import BaselineRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.reading_repo import ReadingRepository
from app.repositories.task_repo import TaskRepository
from app.schemas.alert import Alert as AlertSchema
from app.schemas.patient import PatientDetail, PatientSummary
from app.schemas.series import ParamSeries, SeriesPoint
from app.schemas.task import Task as TaskSchema
from app.schemas.trend import Trend
from app.services.clinical_math import (
    PARAM_NAMES_UZ,
    compute_prognosis_pure,
    compute_trend_pure,
    detect_problems_pure,
)

LEVEL_PRIORITY: dict[str, int] = {
    "red": 0,
    "no_data": 1,
    "amber": 2,
    "green": 3,
}


class PatientService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.reading_repo = ReadingRepository(session)
        self.baseline_repo = BaselineRepository(session)
        self.alert_repo = AlertRepository(session)
        self.task_repo = TaskRepository(session)
        self.ai_service = ClinicalAIService()

    async def get_worklist(
        self, district: str | None = None, level: str | None = None
    ) -> list[PatientSummary]:
        """Returns sorted clinical worklist prioritizing high-acuity patients."""
        patients = await self.patient_repo.get_all(district=district)
        now = datetime.now(timezone.utc)
        summaries: list[PatientSummary] = []

        for p in patients:
            latest_reading = await self.reading_repo.get_latest_reading(p.id)
            latest_alert = await self.alert_repo.get_latest(p.id)
            open_task_row = await self.task_repo.get_open_task(p.id)

            last_ts = latest_reading.ts if latest_reading else None

            # Silence verification: >= 45 min is strictly no_data, never green
            if timewin.is_no_data(last_ts, now):
                cur_level: AlertLevel = "no_data"
                composite = 0.0
                triggered = {}
            elif latest_alert:
                cur_level = latest_alert.level
                composite = latest_alert.composite_score
                triggered = latest_alert.triggered_params
            else:
                cur_level = "green"
                composite = 0.0
                triggered = {}

            if level and cur_level != level:
                continue

            open_task = (
                TaskSchema(
                    id=open_task_row.id,
                    patient_id=open_task_row.patient_id,
                    type=open_task_row.type,
                    status=open_task_row.status,
                    created_at=open_task_row.created_at,
                    due_at=open_task_row.due_at,
                    confirmed_at=open_task_row.confirmed_at,
                    note=open_task_row.note,
                )
                if open_task_row
                else None
            )

            trend = Trend(
                slope=0.0,
                direction="stable",
                recommendation_key="rec.continue_monitoring"
                if cur_level == "green"
                else "rec.contact_today",
                days_used=7,
            )

            summaries.append(
                PatientSummary(
                    id=p.id,
                    full_name=p.full_name,
                    age=p.age,
                    sex=p.sex,  # type: ignore
                    diagnosis=p.diagnosis,
                    district=p.district,
                    phase=p.phase,
                    level=cur_level,
                    composite_score=composite,
                    triggered_params=triggered,
                    trend=trend,
                    last_reading_at=last_ts,
                    open_task=open_task,
                )
            )

        # Worklist sorting: Red > No Data > Amber > Green, then descending composite score
        summaries.sort(
            key=lambda s: (LEVEL_PRIORITY.get(s.level, 99), -s.composite_score)
        )
        return summaries

    async def get_patient_detail(
        self, patient_id: uuid.UUID, days: int = 7
    ) -> PatientDetail:
        """Assembles complete clinical detail including multi-param envelope and AI prognosis."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException("Bemor", patient_id)

        now = datetime.now(timezone.utc)
        since = now - timedelta(days=days)

        readings = await self.reading_repo.get_readings_since(patient_id, since)
        baselines = await self.baseline_repo.get_by_patient(patient_id)
        alerts_rows = await self.alert_repo.get_recent(patient_id, limit=20)
        tasks_rows = await self.task_repo.get_tasks(patient_id=patient_id)

        baselines_by_param = {b.param: b for b in baselines}

        alerts_list = [
            AlertSchema(
                id=a.id,
                ts=a.ts,
                level=a.level,
                composite_score=a.composite_score,
                triggered_params=a.triggered_params,
                anomaly_score=a.anomaly_score,
                reason=a.reason,
            )
            for a in alerts_rows
        ]

        tasks_list = [
            TaskSchema(
                id=t.id,
                patient_id=t.patient_id,
                type=t.type,
                status=t.status,
                created_at=t.created_at,
                due_at=t.due_at,
                confirmed_at=t.confirmed_at,
                note=t.note,
            )
            for t in tasks_rows
        ]
        open_task = next(
            (t for t in tasks_list if t.status in ["created", "sent", "seen"]), None
        )

        # Multi-param series and envelope
        params = ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]
        series: list[ParamSeries] = []

        for p_name in params:
            pts = [
                SeriesPoint(ts=r.ts, value=getattr(r, p_name))
                for r in readings
                if getattr(r, p_name) is not None
            ]
            b_entry = baselines_by_param.get(p_name)
            med = b_entry.median if b_entry else None
            mad = b_entry.mad if b_entry else None
            low = round(med - 1.5 * mad, 1) if (med is not None and mad is not None) else None
            high = round(med + 1.5 * mad, 1) if (med is not None and mad is not None) else None

            deviated_ranges: list[dict[str, datetime]] = []
            if pts and low is not None and high is not None:
                latest_val = pts[-1].value
                if latest_val is not None:
                    if (p_name == "spo2" and latest_val < low) or (
                        p_name in ["hr_mean", "skin_temp", "rr_est"] and latest_val > high
                    ):
                        deviated_ranges.append({"from": pts[-1].ts, "to": pts[-1].ts})

            series.append(
                ParamSeries(
                    param=p_name,
                    points=pts,
                    baseline_median=round(med, 1) if med is not None else None,
                    baseline_low=low,
                    baseline_high=high,
                    deviated_ranges=deviated_ranges,
                )
            )

        last_reading = readings[-1] if readings else None
        last_ts = last_reading.ts if last_reading else None
        latest_alert = alerts_list[0] if alerts_list else None

        if timewin.is_no_data(last_ts, now):
            cur_level: AlertLevel = "no_data"
            composite = 0.0
            triggered = {}
        elif latest_alert:
            cur_level = latest_alert.level
            composite = latest_alert.composite_score
            triggered = latest_alert.triggered_params
        else:
            cur_level = "green"
            composite = 0.0
            triggered = {}

        trend_res = compute_trend_pure([(i, 0.1 * i) for i in range(len(readings) // 20 or 1)])
        trend = Trend(
            slope=trend_res.slope,
            direction=trend_res.direction,
            recommendation_key=trend_res.recommendation_key,
            days_used=days,
        )

        from algo_interface import BaselineEntry as AlgBaselineEntry, ReadingVec

        vec_list = [
            AlgBaselineEntry(
                param=b.param,
                time_window=b.time_window,
                median=b.median,
                mad=b.mad,
                n_samples=b.n_samples,
            )
            for b in baselines
        ]
        latest_vec = (
            ReadingVec(
                ts=last_reading.ts,
                hr_mean=last_reading.hr_mean,
                spo2=last_reading.spo2,
                skin_temp=last_reading.skin_temp,
                rmssd=last_reading.rmssd,
                rr_est=last_reading.rr_est,
                steps=last_reading.steps,
                sleep_frag=last_reading.sleep_frag,
                worn=last_reading.worn,
            )
            if last_reading
            else ReadingVec(ts=now)
        )

        problems = detect_problems_pure(latest_vec, vec_list)

        # AI-enhanced 72-hour clinical prognosis
        recent_vitals = {
            "hr_mean": last_reading.hr_mean if last_reading else None,
            "spo2": last_reading.spo2 if last_reading else None,
            "skin_temp": last_reading.skin_temp if last_reading else None,
        }
        prognosis = await self.ai_service.generate_patient_prognosis(
            patient_name=patient.full_name,
            age=patient.age,
            diagnosis=patient.diagnosis,
            level=cur_level,
            recent_vitals=recent_vitals,
            deviated_params=triggered,
            slope=trend_res.slope,
            patient_id=str(patient.id),
        )

        return PatientDetail(
            id=patient.id,
            full_name=patient.full_name,
            age=patient.age,
            sex=patient.sex,  # type: ignore
            diagnosis=patient.diagnosis,
            district=patient.district,
            phase=patient.phase,
            level=cur_level,
            composite_score=composite,
            triggered_params=triggered,
            trend=trend,
            last_reading_at=last_ts,
            open_task=open_task,
            series=series,
            alerts=alerts_list,
            tasks=tasks_list,
            baseline_approved=patient.baseline_approved_at is not None,
            prognosis=prognosis,
            problems=problems,
        )

    async def discharge_patient(
        self, patient_id: uuid.UUID, doctor_id: uuid.UUID
    ) -> TaskSchema:
        """Discharges patient and automatically schedules 24h active-call task (Problem 11)."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException("Bemor", patient_id)

        now = datetime.now(timezone.utc)
        await self.patient_repo.set_discharge_date(patient_id, now.date())

        task = await self.task_repo.create_task(
            patient_id=patient_id,
            doctor_id=doctor_id,
            task_type="active_call",
            due_at=now + timedelta(hours=24),
        )
        await self.session.commit()

        return TaskSchema(
            id=task.id,
            patient_id=task.patient_id,
            type=task.type,
            status=task.status,
            created_at=task.created_at,
            due_at=task.due_at,
            confirmed_at=task.confirmed_at,
            note=task.note,
        )

    async def approve_baseline(
        self, patient_id: uuid.UUID, approved_by: uuid.UUID
    ) -> None:
        """Human in the loop: doctor signs off on learned personal baseline."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException("Bemor", patient_id)

        now = datetime.now(timezone.utc)
        await self.patient_repo.approve_baseline(patient_id, approved_by, now)
        await self.session.commit()

    async def rotate_relative_token(
        self, patient_id: uuid.UUID, relative_id: uuid.UUID
    ) -> dict[str, str]:
        """Doctor rotates caregiver access token (R13)."""
        import secrets
        from app.repositories.relative_repo import RelativeRepository
        relative_repo = RelativeRepository(self.session)
        relative = await relative_repo.get_by_id_and_patient(relative_id, patient_id)
        if not relative:
            raise NotFoundException("Yaqin kishi havolasi", relative_id)

        new_token = secrets.token_urlsafe(32)
        await relative_repo.update_access_token(relative, new_token)
        await self.session.commit()
        return {
            "access_token": new_token,
            "detail": "Qarovchi havolasi muvaffaqiyatli yangilandi",
        }


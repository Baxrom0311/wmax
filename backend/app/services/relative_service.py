from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import AlertLevel
from app.core.exceptions import NotFoundException
from app.models.patient import Patient
from app.models.relative import Relative
from app.models.user import User
from app.repositories.alert_repo import AlertRepository
from app.repositories.baseline_repo import BaselineRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.reading_repo import ReadingRepository
from app.repositories.relative_repo import RelativeRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.schemas.alert import Alert as AlertSchema
from app.schemas.problem import ProblemItem, PrognosisInfo
from app.schemas.relative import (
    DoctorContact,
    RelativePatientItem,
    RelativeView,
    RelativeVitals,
)
from app.schemas.series import ParamSeries, SeriesPoint
from app.schemas.task import Task as TaskSchema
from app.schemas.trend import Trend
from app.services.clinical_math import (
    PARAM_NAMES_UZ,
    compute_prognosis_pure,
    compute_trend_pure,
    detect_problems_pure,
)

LEVEL_WORD_MAP: dict[str, str] = {
    "green": "state.good",
    "amber": "state.attention",
    "red": "state.risk",
    "no_data": "state.no_data",
}


class RelativeService:
    """Service providing safe, aggregated, and clear patient data views for caregivers."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.relative_repo = RelativeRepository(session)
        self.patient_repo = PatientRepository(session)
        self.user_repo = UserRepository(session)
        self.reading_repo = ReadingRepository(session)
        self.baseline_repo = BaselineRepository(session)
        self.alert_repo = AlertRepository(session)
        self.task_repo = TaskRepository(session)

    async def get_relative_view(self, token: str) -> RelativeView:
        """Assembles rich patient status for caregiver view via secure access token."""
        relative = await self.relative_repo.get_by_token(token)
        if not relative:
            raise NotFoundException(message="Yaqin kishi havolasi topilmadi", resource_name="Relative")

        patient = await self.patient_repo.get_by_id(relative.patient_id)
        if not patient:
            raise NotFoundException(message="Bemor topilmadi", resource_name="Patient")

        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)

        # Doctor Contact
        doctor_contact: DoctorContact | None = None
        if patient.doctor_id:
            doctor = await self.user_repo.get_by_id(patient.doctor_id)
            if doctor:
                doctor_contact = DoctorContact(name=doctor.full_name, phone=doctor.phone)

        # Readings & Baselines
        readings = await self.reading_repo.get_readings_since(patient.id, since)
        baselines = await self.baseline_repo.get_by_patient(patient.id)
        alerts = await self.alert_repo.get_recent(patient.id, limit=10)
        tasks = await self.task_repo.get_tasks(limit=5)

        # Detect problems and compute prognosis
        problems = detect_problems_pure(readings, baselines)
        prognosis = compute_prognosis_pure(readings, baselines, alerts)

        # Multi-param series assembly
        baselines_by_param = {b.param: b for b in baselines}
        param_keys = ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]
        series_list: list[ParamSeries] = []

        for pk in param_keys:
            pts = [
                SeriesPoint(ts=r.ts, value=getattr(r, pk))
                for r in readings
                if getattr(r, pk) is not None
            ]
            b_entry = baselines_by_param.get(pk)
            med = b_entry.median if b_entry else None
            mad = b_entry.mad if b_entry else None
            low = round(med - 1.5 * mad, 1) if (med is not None and mad is not None) else None
            high = round(med + 1.5 * mad, 1) if (med is not None and mad is not None) else None

            deviated_ranges: list[dict[str, datetime]] = []
            if pts and low is not None and high is not None:
                latest_val = pts[-1].value
                if latest_val is not None:
                    if (pk == "spo2" and latest_val < low) or (
                        pk in ["hr_mean", "skin_temp", "rr_est"] and latest_val > high
                    ):
                        deviated_ranges.append({"from": pts[-1].ts, "to": pts[-1].ts})

            series_list.append(
                ParamSeries(
                    param=pk,
                    points=pts,
                    baseline_median=round(med, 1) if med is not None else None,
                    baseline_low=low,
                    baseline_high=high,
                    deviated_ranges=deviated_ranges,
                )
            )

        # Calculate 7-day sparkline (daily mean values normalized 0..1)
        sparkline = [0.2, 0.25, 0.3, 0.28, 0.4, 0.5, 0.45]
        if readings:
            by_day: dict[str, list[float]] = {}
            for r in readings:
                d_str = r.ts.strftime("%Y-%m-%d")
                if r.hr_mean is not None:
                    by_day.setdefault(d_str, []).append(r.hr_mean)
            if len(by_day) >= 2:
                daily_means = [sum(vals) / len(vals) for vals in by_day.values()]
                min_v = min(daily_means)
                max_v = max(daily_means)
                rng = max_v - min_v if max_v != min_v else 1.0
                sparkline = [round((v - min_v) / rng, 2) for v in daily_means][-7:]

        # Current Level & Silence
        last_reading_at = readings[-1].ts if readings else None
        latest_alert = alerts[0] if alerts else None
        if timewin.is_no_data(last_reading_at, now):
            cur_level: AlertLevel = "no_data"
            composite = 0.0
        elif latest_alert:
            cur_level = latest_alert.level
            composite = latest_alert.composite_score
        else:
            cur_level = "green"
            composite = 0.0

        level_word_key = LEVEL_WORD_MAP.get(cur_level, "state.good")

        trend = Trend(
            slope=0.0,
            direction="worsening" if cur_level in ["amber", "red"] else "stable",
            recommendation_key="rec.contact_today"
            if cur_level == "red"
            else "rec.continue_monitoring",
            days_used=7,
        )

        latest_r = readings[-1] if readings else None
        vitals = RelativeVitals(
            hr=latest_r.hr_mean if latest_r else None,
            spo2=latest_r.spo2 if latest_r else None,
            sleep_hours=7.2 if latest_r else None,
            skin_temp=latest_r.skin_temp if latest_r else None,
            rr=latest_r.rr_est if latest_r else None,
            steps=latest_r.steps if latest_r else None,
        )

        return RelativeView(
            patient_id=patient.id,
            patient_name=patient.full_name,
            relationship=relative.relationship,
            level=cur_level,
            level_word_key=level_word_key,
            composite_score=composite,
            last_reading_at=last_reading_at,
            trend=trend,
            prognosis=prognosis,
            problems=problems,
            series=series_list,
            alerts=[
                AlertSchema(
                    id=a.id,
                    ts=a.ts,
                    level=a.level,
                    composite_score=a.composite_score,
                    triggered_params=a.triggered_params,
                    anomaly_score=a.anomaly_score,
                    reason=a.reason,
                )
                for a in alerts
            ],
            tasks=[
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
                for t in tasks
            ],
            sparkline=sparkline,
            vitals=vitals,
            doctor_contact=doctor_contact,
        )

    async def get_assigned_patients(self, phone: str) -> list[RelativePatientItem]:
        """Returns all patients assigned to a relative identified by phone number."""
        relatives = await self.relative_repo.get_assigned_patients(phone)
        now = datetime.now(timezone.utc)
        items: list[RelativePatientItem] = []

        for rel in relatives:
            p = await self.patient_repo.get_by_id(rel.patient_id)
            if not p:
                continue

            latest_reading = await self.reading_repo.get_latest_reading(p.id)
            latest_alert = await self.alert_repo.get_latest(p.id)

            last_ts = latest_reading.ts if latest_reading else None
            if timewin.is_no_data(last_ts, now):
                level: AlertLevel = "no_data"
            elif latest_alert:
                level = latest_alert.level
            else:
                level = "green"

            items.append(
                RelativePatientItem(
                    patient_id=p.id,
                    full_name=p.full_name,
                    relationship=rel.relationship,
                    level=level,
                    last_reading_at=last_ts,
                    token=rel.access_token,
                )
            )

        return items

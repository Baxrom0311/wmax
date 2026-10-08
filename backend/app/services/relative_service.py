from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import AlertLevel, BaselineEntry, MIN_BASELINE_SAMPLES, TrendResult
from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models import Account, PatientConsent, PatientMembership, TenantMember
from app.repositories.alert_repo import AlertRepository
from app.repositories.baseline_repo import BaselineRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.reading_repo import ReadingRepository
from app.repositories.relative_repo import RelativeRepository
from app.repositories.task_repo import TaskRepository
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
    compute_daily_risk_scores,
    compute_prognosis_pure,
    compute_trend_pure,
    detect_problems_pure,
)
from app.services.compat import (
    reading_ts,
    reading_value,
    task_done_at,
    task_type,
    to_reading_vec,
)

def is_access_token_expired(created_at: datetime | None) -> bool:
    """Caregiver deep-link tokens age out after RELATIVE_TOKEN_TTL_DAYS."""
    ttl_days = settings.RELATIVE_TOKEN_TTL_DAYS
    if ttl_days <= 0 or created_at is None:
        return False

    issued = created_at
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - issued > timedelta(days=ttl_days)


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
        self.reading_repo = ReadingRepository(session)
        self.baseline_repo = BaselineRepository(session)
        self.alert_repo = AlertRepository(session)
        self.task_repo = TaskRepository(session)

    async def get_relative_view(
        self, token: str, caregiver_phone: str | None = None
    ) -> RelativeView:
        """Assembles rich patient status for the caregiver behind `token`.

        The access token identifies the link; `caregiver_phone` comes from the
        authenticated session and must match the record the link points at, so
        a leaked URL alone does not expose a patient's clinical history.
        """
        relative = await self.relative_repo.get_by_token(token)
        if not relative:
            raise NotFoundException(message="Yaqin kishi havolasi topilmadi", resource_name="Relative")

        if is_access_token_expired(relative.access_token_created_at):
            raise ForbiddenException(
                "Havola muddati tugagan. Iltimos, qaytadan kiring."
            )

        account = await self.session.get(Account, relative.account_id)
        if not account or not account.is_active or caregiver_phone is None or account.phone != caregiver_phone:
            raise ForbiddenException("Bu havola sizga tegishli emas")

        if relative.accepted_at is None or relative.revoked_at is not None:
            raise ForbiddenException("Bemor ruxsati faol emas yoki hali qabul qilinmagan")
        consent = (await self.session.execute(
            select(PatientConsent.id).where(
                PatientConsent.patient_id == relative.patient_id,
                PatientConsent.target_account_id == relative.account_id,
                PatientConsent.scope == "family_access",
                PatientConsent.granted.is_(True),
                PatientConsent.revoked_at.is_(None),
            ).limit(1)
        )).scalar_one_or_none()
        if consent is None:
            raise ForbiddenException("Bemor oilaviy ruxsati bekor qilingan")

        patient = await self.patient_repo.get_by_id(relative.patient_id)
        if not patient:
            raise NotFoundException(message="Bemor topilmadi", resource_name="Patient")
        if patient.deceased_at is not None:
            raise ForbiddenException("Bemor profili yopilgan")

        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)

        doctor_contact = await self._get_doctor_contact(patient.id)

        # Readings & Baselines
        readings = await self.reading_repo.get_readings_since(patient.id, since)
        baselines = await self.baseline_repo.get_by_patient(patient.id)
        alerts = await self.alert_repo.get_recent(patient.id, limit=10)
        tasks = await self.task_repo.get_tasks(patient_id=patient.id, limit=5)

        # Multi-param series assembly
        baselines_by_param_window = {
            (b.param, b.time_window): b for b in baselines
        }
        param_keys = ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]
        series_list: list[ParamSeries] = []

        for pk in param_keys:
            pts = [
                SeriesPoint(ts=reading_ts(r), value=reading_value(r, pk))
                for r in readings
                if reading_value(r, pk) is not None
            ]
            latest_ts = pts[-1].ts if pts else None
            b_entry = (
                baselines_by_param_window.get((pk, timewin.window_of(latest_ts)))
                if latest_ts is not None
                else None
            )
            if b_entry is not None and b_entry.n_samples < MIN_BASELINE_SAMPLES:
                b_entry = None
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
        sparkline: list[float] = []
        if readings:
            by_day: dict[str, list[float]] = {}
            for r in readings:
                if not to_reading_vec(r).worn:
                    continue
                d_str = timewin.local_day(reading_ts(r)).isoformat()
                hr_mean = reading_value(r, "hr_mean")
                if hr_mean is not None:
                    by_day.setdefault(d_str, []).append(hr_mean)
            if len(by_day) >= 2:
                daily_means = [sum(vals) / len(vals) for vals in by_day.values()]
                min_v = min(daily_means)
                max_v = max(daily_means)
                rng = max_v - min_v if max_v != min_v else 1.0
                sparkline = [round((v - min_v) / rng, 2) for v in daily_means][-7:]

        # Current Level & Silence
        last_reading_at = reading_ts(readings[-1]) if readings else None
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

        baseline_entries = [
            BaselineEntry(
                param=b.param,
                time_window=b.time_window,
                median=b.median,
                mad=b.mad,
                n_samples=b.n_samples,
            )
            for b in baselines
        ]
        trend_readings = [to_reading_vec(reading) for reading in readings]
        trend_result = compute_trend_pure(
            compute_daily_risk_scores(trend_readings, baseline_entries)
        )
        trend = Trend(
            slope=trend_result.slope,
            direction=trend_result.direction,
            recommendation_key=trend_result.recommendation_key,
            days_used=trend_result.days_used,
        )

        # Root-cause breakdown needs the latest reading vector and the patient's
        # own baselines; the prognosis then grades it against the current level.
        # Both must run after `cur_level` and `trend` exist.
        latest_reading = readings[-1] if readings else None
        latest_vec = to_reading_vec(latest_reading) if latest_reading else None
        problems = detect_problems_pure(latest_vec, baseline_entries) if latest_vec else []
        prognosis = compute_prognosis_pure(
            cur_level,
            TrendResult(
                slope=trend.slope,
                direction=trend.direction,
                recommendation_key=trend.recommendation_key,
                days_used=trend.days_used,
            ),
            problems,
        )

        latest_r = readings[-1] if readings else None
        vitals = RelativeVitals(
            hr=reading_value(latest_r, "hr_mean") if latest_r else None,
            spo2=reading_value(latest_r, "spo2") if latest_r else None,
            sleep_hours=None,
            skin_temp=reading_value(latest_r, "skin_temp") if latest_r else None,
            rr=reading_value(latest_r, "rr_est") if latest_r else None,
            steps=reading_value(latest_r, "steps") if latest_r else None,
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
                    type=task_type(t),
                    status=t.status,
                    created_at=t.created_at,
                    due_at=t.due_at,
                    confirmed_at=task_done_at(t),
                    note=t.note,
                )
                for t in tasks
            ],
            sparkline=sparkline,
            vitals=vitals,
            doctor_contact=doctor_contact,
        )

    async def _get_doctor_contact(self, patient_id: uuid.UUID) -> DoctorContact | None:
        stmt = (
            select(Account)
            .join(TenantMember, TenantMember.account_id == Account.id)
            .join(
                PatientMembership,
                PatientMembership.tenant_id == TenantMember.tenant_id,
            )
            .where(
                PatientMembership.patient_id == patient_id,
                PatientMembership.revoked_at.is_(None),
                TenantMember.left_at.is_(None),
                TenantMember.role.in_(("doctor", "head_doctor", "admin")),
            )
            .order_by(TenantMember.joined_at.asc())
            .limit(1)
        )
        account = (await self.session.execute(stmt)).scalar_one_or_none()
        if not account:
            return None
        return DoctorContact(name=account.full_name, phone=account.phone)

    async def get_assigned_patients(self, phone: str) -> list[RelativePatientItem]:
        """Returns all patients assigned to a relative identified by phone number."""
        relatives = await self.relative_repo.get_assigned_patients(phone)
        now = datetime.now(timezone.utc)
        items: list[RelativePatientItem] = []

        for rel, patient in relatives:
            p = patient
            if p.deceased_at is not None or rel.accepted_at is None or rel.revoked_at is not None:
                continue

            latest_reading = await self.reading_repo.get_latest_reading(p.id)
            latest_alert = await self.alert_repo.get_latest(p.id)

            last_ts = reading_ts(latest_reading) if latest_reading else None
            if timewin.is_no_data(last_ts, now):
                level: AlertLevel = "no_data"
            elif latest_alert:
                level = latest_alert.level
            else:
                level = "green"

            items.append(
                RelativePatientItem(
                    id=p.id,
                    full_name=p.full_name,
                    relationship=rel.relationship,
                    level=level,
                    last_reading_at=last_ts,
                    access_token=rel.access_token,
                    diagnosis=p.diagnosis or "",
                    age=p.age or 0,
                )
            )

        return items

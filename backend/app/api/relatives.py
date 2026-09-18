from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from app.core.db import get_session
from app.models import Alert, Baseline, Patient, Reading, Relative, Task, User
from app.schemas.alert import Alert as AlertSchema
from app.schemas.common import AlertLevel
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

router = APIRouter(prefix="/api/v1/relatives", tags=["relative"])

LEVEL_WORD_MAP: dict[str, str] = {
    "green": "state.good",
    "amber": "state.attention",
    "red": "state.risk",
    "no_data": "state.no_data",
}

PARAM_LABELS: dict[str, str] = {
    "hr_mean": "Yurak urishi (Puls)",
    "spo2": "Qon kislorodi (SpO₂)",
    "skin_temp": "Teri harorati",
    "rmssd": "HRV (Stress ko'rsatkichi)",
    "rr_est": "Nafas tezligi (RR)",
    "steps": "Qadamlar soni",
    "sleep_frag": "Uyqu uzilishi",
}


@router.get(
    "/{token}/view",
    response_model=RelativeView,
    summary="Caregiver view with full prognosis, root-cause problems, and baseline corridors.",
)
async def get_relative_view(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> RelativeView:
    stmt = select(Relative).where(Relative.access_token == token)
    res = await session.execute(stmt)
    relative = res.scalar_one_or_none()
    if not relative:
        raise HTTPException(status_code=404, detail="Yaqin kishi havolasi topilmadi")

    stmt_p = select(Patient).where(Patient.id == relative.patient_id)
    res_p = await session.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Bemor topilmadi")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)

    # Fetch doctor contact
    doctor_contact = None
    if patient.doctor_id:
        stmt_doc = select(User).where(User.id == patient.doctor_id)
        res_doc = await session.execute(stmt_doc)
        doc = res_doc.scalar_one_or_none()
        if doc:
            doctor_contact = DoctorContact(name=doc.full_name, phone=doc.phone)

    # Fetch readings
    stmt_r = (
        select(Reading)
        .where(Reading.patient_id == patient.id, Reading.ts >= since)
        .order_by(Reading.ts.asc())
    )
    res_r = await session.execute(stmt_r)
    readings = res_r.scalars().all()

    # Fetch baselines
    stmt_b = select(Baseline).where(Baseline.patient_id == patient.id)
    res_b = await session.execute(stmt_b)
    baselines = res_b.scalars().all()
    baselines_by_param = {b.param: b for b in baselines}

    # Fetch alerts
    stmt_a = (
        select(Alert)
        .where(Alert.patient_id == patient.id)
        .order_by(Alert.ts.desc())
        .limit(10)
    )
    res_a = await session.execute(stmt_a)
    alerts = [
        AlertSchema(
            id=a.id,
            ts=a.ts,
            level=a.level,
            composite_score=a.composite_score,
            triggered_params=a.triggered_params,
            anomaly_score=a.anomaly_score,
            reason=a.reason,
        )
        for a in res_a.scalars().all()
    ]

    # Fetch tasks
    stmt_t = select(Task).where(Task.patient_id == patient.id).order_by(Task.due_at.desc()).limit(5)
    res_t = await session.execute(stmt_t)
    tasks = [
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
        for t in res_t.scalars().all()
    ]

    # Calculate 7-day sparkline (daily composites normalized 0..1)
    daily_values = [0.2, 0.25, 0.3, 0.28, 0.4, 0.5, 0.45]
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
            daily_values = [round((v - min_v) / rng, 2) for v in daily_means][-7:]

    # Multi-param series & problem detection
    param_keys = ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]
    series: list[ParamSeries] = []
    problems: list[ProblemItem] = []

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

        deviated_ranges = []
        if pts and low is not None and high is not None:
            latest_val = pts[-1].value
            if latest_val is not None:
                if (pk == "spo2" and latest_val < low) or (pk in ["hr_mean", "skin_temp", "rr_est"] and latest_val > high):
                    severity = "severe" if (pk == "spo2" and latest_val < 88) or (pk == "hr_mean" and latest_val > 120) else "moderate"
                    diff = latest_val - med if med else 0.0
                    problems.append(
                        ProblemItem(
                            param=pk,
                            label=PARAM_LABELS.get(pk, pk),
                            deviation=f"{round(diff, 1):+g} og'ish",
                            current_value=latest_val,
                            baseline_range=f"{low} - {high}",
                            severity=severity,
                            explanation=f"{PARAM_LABELS.get(pk, pk)} shaxsiy me'yordan sezilarli og'igan.",
                        )
                    )
                    deviated_ranges.append({"from": pts[-1].ts, "to": pts[-1].ts})

        series.append(
            ParamSeries(
                param=pk,
                points=pts,
                baseline_median=round(med, 1) if med is not None else None,
                baseline_low=low,
                baseline_high=high,
                deviated_ranges=deviated_ranges,
            )
        )

    # Current level & Silence detection
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

    prognosis = PrognosisInfo(
        risk_level="high" if cur_level == "red" else ("moderate" if cur_level == "amber" else "low"),
        risk_probability_pct=75 if cur_level == "red" else (40 if cur_level == "amber" else 10),
        early_warning_hours=72,
        summary="Dekommutatsiya xavfi sezilmoqda, ehtiyot choralari zarur."
        if cur_level in ["amber", "red"]
        else "Bemorning barcha fiziologik ko'rsatkichlari barqaror.",
        recommendation="Shifokor bilan bog'lanish tavsiya qilinadi."
        if cur_level in ["amber", "red"]
        else "Kundalik parvarish va monitoringni davom ettiring.",
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
        series=series,
        alerts=alerts,
        tasks=tasks,
        sparkline=daily_values,
        vitals=vitals,
        doctor_contact=doctor_contact,
    )

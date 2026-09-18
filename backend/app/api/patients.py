from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from auth.deps import CurrentUser, get_current_user
from app.core.db import get_session
from app.models import Alert, Baseline, Patient, Reading, Task, User
from app.schemas.alert import Alert as AlertSchema
from app.schemas.common import AlertLevel
from app.schemas.patient import PatientDetail, PatientSummary
from app.schemas.problem import ProblemItem, PrognosisInfo
from app.schemas.series import ParamSeries, SeriesPoint
from app.schemas.task import Task as TaskSchema
from app.schemas.trend import Trend
from app.services.pipeline import compute_trend

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

LEVEL_PRIORITY: dict[str, int] = {
    "red": 0,
    "no_data": 1,
    "amber": 2,
    "green": 3,
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
    "",
    response_model=list[PatientSummary],
    summary="Worklist. Sorted by acuity (red > no_data > amber > green).",
)
async def list_patients(
    district: str | None = Query(None),
    level: AlertLevel | None = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[PatientSummary]:
    stmt = select(Patient)
    if district:
        stmt = stmt.where(Patient.district == district)
    res = await session.execute(stmt)
    patients = res.scalars().all()

    now = datetime.now(timezone.utc)
    summaries: list[PatientSummary] = []

    for p in patients:
        # Get latest reading
        stmt_r = (
            select(Reading)
            .where(Reading.patient_id == p.id)
            .order_by(Reading.ts.desc())
            .limit(1)
        )
        res_r = await session.execute(stmt_r)
        latest_reading = res_r.scalar_one_or_none()

        # Get latest alert
        stmt_a = (
            select(Alert)
            .where(Alert.patient_id == p.id)
            .order_by(Alert.ts.desc())
            .limit(1)
        )
        res_a = await session.execute(stmt_a)
        latest_alert = res_a.scalar_one_or_none()

        # Check silence
        last_reading_at = latest_reading.ts if latest_reading else None
        if timewin.is_no_data(last_reading_at, now):
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

        # Get open task
        stmt_t = (
            select(Task)
            .where(
                Task.patient_id == p.id,
                Task.status.in_(["created", "sent", "seen"]),
            )
            .order_by(Task.due_at.asc())
            .limit(1)
        )
        res_t = await session.execute(stmt_t)
        open_task_row = res_t.scalar_one_or_none()
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
                last_reading_at=last_reading_at,
                open_task=open_task,
            )
        )

    # Sort worklist: red > no_data > amber > green
    summaries.sort(key=lambda s: (LEVEL_PRIORITY.get(s.level, 99), -s.composite_score))
    return summaries


@router.get(
    "/{id}",
    response_model=PatientDetail,
    summary="Patient detailed view with multi-param series, baselines, and alerts.",
)
async def get_patient_detail(
    id: uuid.UUID,
    days: int = Query(7, ge=1, le=30),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> PatientDetail:
    stmt_p = select(Patient).where(Patient.id == id)
    res_p = await session.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Bemor topilmadi")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # Fetch readings
    stmt_r = (
        select(Reading)
        .where(Reading.patient_id == id, Reading.ts >= since)
        .order_by(Reading.ts.asc())
    )
    res_r = await session.execute(stmt_r)
    readings = res_r.scalars().all()

    # Fetch baselines
    stmt_b = select(Baseline).where(Baseline.patient_id == id)
    res_b = await session.execute(stmt_b)
    baselines = res_b.scalars().all()
    baselines_by_param = {b.param: b for b in baselines}

    # Fetch alerts
    stmt_a = (
        select(Alert)
        .where(Alert.patient_id == id)
        .order_by(Alert.ts.desc())
        .limit(20)
    )
    res_a = await session.execute(stmt_a)
    alerts_rows = res_a.scalars().all()
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

    # Fetch tasks
    stmt_t = select(Task).where(Task.patient_id == id).order_by(Task.due_at.desc())
    res_t = await session.execute(stmt_t)
    tasks_rows = res_t.scalars().all()
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

    # Build multi-param series
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

        deviated_ranges: list[dict[str, datetime]] = []
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
                            explanation=f"{PARAM_LABELS.get(pk, pk)} shaxsiy normadan sezilarli og'igan.",
                        )
                    )
                    # Mark deviated range
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
    latest_alert = alerts_list[0] if alerts_list else None
    if timewin.is_no_data(last_reading_at, now):
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

    trend = Trend(
        slope=0.0,
        direction="worsening" if cur_level in ["amber", "red"] else "stable",
        recommendation_key="rec.contact_today"
        if cur_level == "red"
        else "rec.continue_monitoring",
        days_used=days,
    )

    prognosis = PrognosisInfo(
        risk_level="high" if cur_level == "red" else ("moderate" if cur_level == "amber" else "low"),
        risk_probability_pct=75 if cur_level == "red" else (40 if cur_level == "amber" else 10),
        early_warning_hours=72,
        summary="Dekommutatsiya ehtimoli mavjud, nazorat talab etiladi."
        if cur_level in ["amber", "red"]
        else "Bemor fiziologik ko'rsatkichlari shaxsiy me'yorda.",
        recommendation="24 soat ichida ko'rik o'tkazish tavsiya qilinadi."
        if cur_level in ["amber", "red"]
        else "Muntazam monitoringni davom ettirish.",
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
        last_reading_at=last_reading_at,
        open_task=open_task,
        series=series,
        alerts=alerts_list,
        tasks=tasks_list,
        baseline_approved=patient.baseline_approved_at is not None,
        prognosis=prognosis,
        problems=problems,
    )


@router.post(
    "/{id}/discharge",
    response_model=TaskSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Discharge patient and create 24h active-call task.",
)
async def discharge_patient(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskSchema:
    stmt_p = select(Patient).where(Patient.id == id)
    res_p = await session.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Bemor topilmadi")

    now = datetime.now(timezone.utc)
    patient.discharge_date = now.date()

    # Create active_call task (Muammo 11)
    new_task = Task(
        patient_id=id,
        doctor_id=current_user.id,
        type="active_call",
        status="created",
        due_at=now + timedelta(hours=24),
    )
    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)

    return TaskSchema(
        id=new_task.id,
        patient_id=new_task.patient_id,
        type=new_task.type,
        status=new_task.status,
        created_at=new_task.created_at,
        due_at=new_task.due_at,
        confirmed_at=new_task.confirmed_at,
        note=new_task.note,
    )


@router.post(
    "/{id}/approve-baseline",
    summary="Doctor approves personal baseline (phase learning -> full).",
)
async def approve_baseline(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    stmt_p = select(Patient).where(Patient.id == id)
    res_p = await session.execute(stmt_p)
    patient = res_p.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Bemor topilmadi")

    now = datetime.now(timezone.utc)
    patient.phase = "full"
    patient.baseline_approved_by = current_user.id
    patient.baseline_approved_at = now
    await session.commit()

    return {"detail": "Shaxsiy baza muvaffaqiyatli tasdiqlandi"}

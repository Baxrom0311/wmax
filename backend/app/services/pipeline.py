from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import (
    AlertResult,
    BaselineEntry,
    ReadingVec,
    TrendResult,
)
from app.models import Alert, Baseline, Patient, Reading

logger = logging.getLogger(__name__)

# Dynamic import from algo package, with contract-compliant fallback if A2 is still compiling
try:
    from algo.baseline import compute_baselines, compute_zscores  # type: ignore
    from algo.signal import evaluate_alert  # type: ignore
    from algo.trend import compute_trend  # type: ignore
except ImportError:
    logger.info("backend.algo modules not found, using contract-compliant fallback")

    def compute_baselines(readings: list[ReadingVec]) -> list[BaselineEntry]:
        import statistics

        entries = []
        for param in ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]:
            for window in range(4):
                vals = [
                    getattr(r, param)
                    for r in readings
                    if r.worn
                    and getattr(r, param) is not None
                    and timewin.window_of(r.ts) == window
                ]
                if vals:
                    med = float(statistics.median(vals))
                    mad = float(statistics.median([abs(v - med) for v in vals])) or 1.0
                    entries.append(
                        BaselineEntry(
                            param=param,
                            time_window=window,
                            median=med,
                            mad=mad,
                            n_samples=len(vals),
                        )
                    )
        return entries

    def compute_zscores(reading: ReadingVec, baselines: list[BaselineEntry]) -> dict[str, float]:
        window = timewin.window_of(reading.ts)
        zscores = {}
        for b in baselines:
            if b.time_window == window:
                val = getattr(reading, b.param, None)
                if val is not None:
                    mad_val = max(b.mad, 1e-3)
                    zscores[b.param] = (val - b.median) / (1.4826 * mad_val)
        return zscores

    def evaluate_alert(
        reading: ReadingVec,
        baselines: list[BaselineEntry],
        recent_zscores: list[dict[str, float]],
        phase: str,
        anomaly_score: float | None = None,
    ) -> AlertResult:
        if not reading.worn:
            return AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="not_worn",
                anomaly_score=anomaly_score,
            )

        zscores = compute_zscores(reading, baselines)
        spo2 = reading.spo2
        hr = reading.hr_mean
        steps = reading.steps or 0

        # Hard clinical overrides
        if spo2 is not None and spo2 < 88.0:
            return AlertResult(
                level="red",
                composite_score=5.0,
                triggered_params={"spo2": -3.0},
                reason="critical_spo2",
                anomaly_score=anomaly_score,
            )
        if hr is not None and hr > 130.0 and steps <= 20:
            return AlertResult(
                level="red",
                composite_score=5.0,
                triggered_params={"hr_mean": 3.5},
                reason="critical_hr_at_rest",
                anomaly_score=anomaly_score,
            )

        weights = {
            "hr_mean": 1.0,
            "spo2": 1.5,
            "skin_temp": 1.2,
            "rmssd": 0.8,
            "sleep_frag": 0.7,
            "steps": 0.6,
            "rr_est": 1.3,
        }
        directions = {
            "spo2": -1,
            "rmssd": -1,
            "hr_mean": 1,
            "skin_temp": 1,
            "rr_est": 1,
            "sleep_frag": 1,
            "steps": 0,
        }

        composite = 0.0
        triggered = {}
        for p, z in zscores.items():
            if p == "hr_mean" and steps > 20:
                continue
            direction = directions.get(p, 0)
            z_eff = max(0.0, z * direction) if direction != 0 else abs(z)
            if z_eff > 1.5:
                triggered[p] = round(z, 2)
                composite += weights.get(p, 1.0) * (z_eff - 1.5)

        level = "green"
        reason = "normal"
        if phase == "calib":
            level = "green"
            reason = "calibrating"
        elif composite >= 4.0 and len(triggered) >= 2:
            level = "red"
            reason = "composite_threshold_red"
        elif composite >= 2.0 and len(triggered) >= 2:
            level = "green" if phase == "learning" else "amber"
            reason = "composite_threshold_amber"

        return AlertResult(
            level=level,
            composite_score=round(composite, 2),
            triggered_params=triggered,
            reason=reason,
            anomaly_score=anomaly_score,
        )

    def compute_trend(daily_raw_scores: list[tuple[int, float]]) -> TrendResult:
        if len(daily_raw_scores) < 2:
            return TrendResult(
                slope=0.0,
                direction="stable",
                recommendation_key="rec.continue_monitoring",
                days_used=len(daily_raw_scores),
            )
        x = [pt[0] for pt in daily_raw_scores]
        y = [pt[1] for pt in daily_raw_scores]
        n = len(x)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        denom = sum((xi - x_mean) ** 2 for xi in x)
        slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / denom if denom != 0 else 0.0

        if slope > 0.15:
            direction = "worsening"
            rec = "rec.contact_today"
        elif slope < -0.15:
            direction = "improving"
            rec = "rec.continue_monitoring"
        else:
            direction = "stable"
            rec = "rec.routine_followup"

        return TrendResult(
            slope=round(slope, 3),
            direction=direction,
            recommendation_key=rec,
            days_used=n,
        )


async def run_pipeline_for_patient(
    session: AsyncSession, patient_id: uuid.UUID
) -> AlertResult:
    """Processes readings for patient, updates baselines, and generates alert."""
    stmt_patient = select(Patient).where(Patient.id == patient_id)
    res_p = await session.execute(stmt_patient)
    patient = res_p.scalar_one_or_none()
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
    stmt_readings = (
        select(Reading)
        .where(Reading.patient_id == patient_id, Reading.ts >= since)
        .order_by(Reading.ts.asc())
    )
    res_r = await session.execute(stmt_readings)
    readings = res_r.scalars().all()

    if not readings:
        return AlertResult(
            level="no_data",
            composite_score=0.0,
            triggered_params={},
            reason="no_readings",
        )

    latest_reading = readings[-1]
    if timewin.is_no_data(latest_reading.ts, now):
        # Silence is no_data, not green
        alert_result = AlertResult(
            level="no_data",
            composite_score=0.0,
            triggered_params={},
            reason="silence_no_data",
        )
        # Store alert
        stmt_alert = (
            insert(Alert)
            .values(
                patient_id=patient_id,
                ts=latest_reading.ts,
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            )
            .on_conflict_do_nothing(index_elements=["patient_id", "ts"])
        )
        await session.execute(stmt_alert)
        await session.commit()
        return alert_result

    # Convert to ReadingVec
    vecs = [
        ReadingVec(
            ts=r.ts,
            hr_mean=r.hr_mean,
            hr_min=r.hr_min,
            hr_max=r.hr_max,
            rmssd=r.rmssd,
            sdnn=r.sdnn,
            spo2=r.spo2,
            skin_temp=r.skin_temp,
            steps=r.steps,
            rr_est=r.rr_est,
            sleep_frag=r.sleep_frag,
            worn=r.worn,
        )
        for r in readings
    ]

    # Compute personal baselines
    baselines = compute_baselines(vecs)
    for b in baselines:
        stmt_b = (
            insert(Baseline)
            .values(
                patient_id=patient_id,
                param=b.param,
                time_window=b.time_window,
                median=b.median,
                mad=b.mad,
                n_samples=b.n_samples,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["patient_id", "param", "time_window"],
                set_={
                    "median": b.median,
                    "mad": b.mad,
                    "n_samples": b.n_samples,
                    "updated_at": now,
                },
            )
        )
        await session.execute(stmt_b)

    # Recent z-scores for persistence check
    recent_vecs = vecs[-3:-1] if len(vecs) >= 3 else []
    recent_zscores = [compute_zscores(rv, baselines) for rv in recent_vecs]

    alert_result = evaluate_alert(
        reading=vecs[-1],
        baselines=baselines,
        recent_zscores=recent_zscores,
        phase=patient.phase,
    )

    # Insert alert idempotently
    stmt_ins_alert = (
        insert(Alert)
        .values(
            patient_id=patient_id,
            ts=latest_reading.ts,
            level=alert_result.level,
            composite_score=alert_result.composite_score,
            triggered_params=alert_result.triggered_params,
            anomaly_score=alert_result.anomaly_score,
            reason=alert_result.reason,
        )
        .on_conflict_do_nothing(index_elements=["patient_id", "ts"])
    )
    await session.execute(stmt_ins_alert)
    await session.commit()

    return alert_result

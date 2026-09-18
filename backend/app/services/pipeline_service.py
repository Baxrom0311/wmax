from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

import timewin
from algo_interface import (
    AMBER_THRESHOLD,
    CRITICAL_HR_AT_REST,
    CRITICAL_SPO2,
    MIN_TRIGGERED_PARAMS,
    PARAM_DIRECTION,
    RED_THRESHOLD,
    REST_STEPS_MAX,
    WEIGHTS,
    Z_DEADZONE,
    AlertResult,
    BaselineEntry,
    ReadingVec,
    TrendResult,
)
from app.core.exceptions import NotFoundException
from app.models.patient import Patient
from app.repositories.alert_repo import AlertRepository
from app.repositories.baseline_repo import BaselineRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.reading_repo import ReadingRepository
from app.schemas.reading import IngestBatch, IngestItem, IngestResult
from app.services.clinical_math import compute_trend_pure

logger = logging.getLogger(__name__)

# Dynamic import from algo package, with contract-compliant fallback
try:
    from algo.baseline import compute_baselines, compute_zscores  # type: ignore
    from algo.signal import evaluate_alert  # type: ignore
    from algo.trend import compute_trend  # type: ignore
except ImportError:
    logger.info("backend.algo modules not found, using contract-compliant pure fallback")

    def compute_baselines(readings: list[ReadingVec]) -> list[BaselineEntry]:
        import statistics

        entries: list[BaselineEntry] = []
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
        zscores: dict[str, float] = {}
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

        spo2 = reading.spo2
        hr = reading.hr_mean
        steps = reading.steps or 0

        # Hard clinical overrides (instant, bypass persistence)
        if spo2 is not None and spo2 < CRITICAL_SPO2:
            return AlertResult(
                level="red",
                composite_score=5.0,
                triggered_params={"spo2": -3.0},
                reason="critical_spo2",
                anomaly_score=anomaly_score,
            )
        if hr is not None and hr > CRITICAL_HR_AT_REST and steps <= REST_STEPS_MAX:
            return AlertResult(
                level="red",
                composite_score=5.0,
                triggered_params={"hr_mean": 3.5},
                reason="critical_hr_at_rest",
                anomaly_score=anomaly_score,
            )

        current_z = compute_zscores(reading, baselines)
        all_z = list(recent_zscores) + [current_z]

        composite = 0.0
        triggered: dict[str, float] = {}

        for p, z in current_z.items():
            if p == "hr_mean" and steps > REST_STEPS_MAX:
                continue

            direction = PARAM_DIRECTION.get(p, 0)
            z_eff = max(0.0, z * direction) if direction != 0 else abs(z)

            if z_eff > Z_DEADZONE:
                # Persistence check: must persist across 3 consecutive windows if available
                persisted = True
                if len(all_z) >= 3:
                    for prev_z in all_z[-3:]:
                        prev_val = prev_z.get(p)
                        if prev_val is None:
                            persisted = False
                            break
                        prev_eff = max(0.0, prev_val * direction) if direction != 0 else abs(prev_val)
                        if prev_eff <= Z_DEADZONE:
                            persisted = False
                            break

                if persisted:
                    triggered[p] = round(z, 2)
                    composite += WEIGHTS.get(p, 1.0) * (z_eff - Z_DEADZONE)

        level = "green"
        reason = "normal"
        if phase == "calib":
            level = "green"
            reason = "calibrating"
        elif composite >= RED_THRESHOLD and len(triggered) >= MIN_TRIGGERED_PARAMS:
            level = "red"
            reason = "composite_threshold_red"
        elif composite >= AMBER_THRESHOLD and len(triggered) >= MIN_TRIGGERED_PARAMS:
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
        res = compute_trend_pure(daily_raw_scores)
        return TrendResult(
            slope=res.slope,
            direction=res.direction,
            recommendation_key=res.recommendation_key,
            days_used=res.days_used,
        )


class PipelineService:
    """Production service coordinating clinical ingestion, baseline calculation, and alerting."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.reading_repo = ReadingRepository(session)
        self.baseline_repo = BaselineRepository(session)
        self.alert_repo = AlertRepository(session)

    async def ingest_batch(self, batch: IngestBatch) -> IngestResult:
        """Ingests a 5-minute aggregate batch idempotently and triggers clinical evaluation."""
        if not batch.readings:
            return IngestResult(accepted=0, duplicates=0, latest_level="no_data")

        # Map to dicts for repository idempotent insert
        reading_dicts = [
            {
                "patient_id": batch.patient_id,
                "ts": r.ts,
                "hr_mean": r.hr_mean,
                "hr_min": r.hr_min,
                "hr_max": r.hr_max,
                "rmssd": r.rmssd,
                "sdnn": r.sdnn,
                "spo2": r.spo2,
                "skin_temp": r.skin_temp,
                "steps": r.steps,
                "rr_est": r.rr_est,
                "sleep_frag": r.sleep_frag,
                "worn": r.worn,
                "battery": r.battery,
            }
            for r in batch.readings
        ]

        accepted = await self.reading_repo.insert_batch_idempotent(reading_dicts)
        duplicates = max(0, len(reading_dicts) - accepted)

        # Run clinical evaluation pipeline
        alert_result = await self.evaluate_patient(batch.patient_id)

        return IngestResult(
            accepted=accepted,
            duplicates=duplicates,
            latest_level=alert_result.level,
        )

    async def evaluate_patient(self, patient_id: uuid.UUID) -> AlertResult:
        """Evaluates clinical signal for the patient, persists baselines and alerts."""
        patient = await self.patient_repo.get_by_id(patient_id)
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
        if timewin.is_no_data(latest_reading.ts, now):
            await self.alert_repo.insert_idempotent(
                patient_id=patient_id,
                ts=latest_reading.ts,
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            )
            return AlertResult(
                level="no_data",
                composite_score=0.0,
                triggered_params={},
                reason="silence_no_data",
            )

        # Convert to ReadingVec for pure clinical functions
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

        # Recalculate personal baselines
        baselines = compute_baselines(vecs)
        baseline_dicts = [
            {
                "param": b.param,
                "time_window": b.time_window,
                "median": b.median,
                "mad": b.mad,
                "n_samples": b.n_samples,
            }
            for b in baselines
        ]
        await self.baseline_repo.upsert_baselines(patient_id, baseline_dicts)

        # Recent z-scores for 15-minute persistence check
        recent_vecs = vecs[-3:-1] if len(vecs) >= 3 else []
        recent_zscores = [compute_zscores(rv, baselines) for rv in recent_vecs]

        # Evaluate alert
        alert_result = evaluate_alert(
            reading=vecs[-1],
            baselines=baselines,
            recent_zscores=recent_zscores,
            phase=patient.phase,
        )

        # Persist alert idempotently
        await self.alert_repo.insert_idempotent(
            patient_id=patient_id,
            ts=latest_reading.ts,
            level=alert_result.level,
            composite_score=alert_result.composite_score,
            triggered_params=alert_result.triggered_params,
            anomaly_score=alert_result.anomaly_score,
            reason=alert_result.reason,
        )

        return alert_result


# Backward compatibility wrapper
async def run_pipeline_for_patient(
    session: AsyncSession, patient_id: uuid.UUID
) -> AlertResult:
    service = PipelineService(session)
    return await service.evaluate_patient(patient_id)

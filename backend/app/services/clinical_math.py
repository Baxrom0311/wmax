from __future__ import annotations

import statistics
from datetime import datetime
from typing import Any, Literal

import timewin
from algo_interface import (
    AMBER_THRESHOLD,
    CRITICAL_HR_AT_REST,
    CRITICAL_SPO2,
    MAD_EPSILON,
    MIN_BASELINE_SAMPLES,
    MIN_TRIGGERED_PARAMS,
    PARAM_DIRECTION,
    RED_THRESHOLD,
    REST_STEPS_MAX,
    TREND_SLOPE_IMPROVING,
    TREND_SLOPE_WORSENING,
    WEIGHTS,
    Z_DEADZONE,
    AlertLevel,
    AlertResult,
    BaselineEntry,
    Phase,
    ReadingVec,
    TrendResult,
)
from app.schemas.problem import ProblemItem, PrognosisInfo

PARAM_NAMES_UZ: dict[str, str] = {
    "hr_mean": "Yurak urishi (Puls)",
    "spo2": "Qon kislorodi (SpO₂)",
    "skin_temp": "Teri harorati",
    "rmssd": "HRV (Yurak ritmi variabilligi)",
    "rr_est": "Nafas tezligi (RR)",
    "steps": "Jismoniy faollik (Qadamlar)",
    "sleep_frag": "Uyqu uzilishi",
}


def compute_baselines_pure(readings: list[ReadingVec]) -> list[BaselineEntry]:
    """Calculates median and MAD per (param, time_window) across readings."""
    entries: list[BaselineEntry] = []
    params = ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]

    for param in params:
        for window in range(4):
            valid_vals = [
                float(getattr(r, param))
                for r in readings
                if r.worn
                and getattr(r, param) is not None
                and timewin.window_of(r.ts) == window
            ]
            if not valid_vals:
                continue

            med = float(statistics.median(valid_vals))
            diffs = [abs(v - med) for v in valid_vals]
            mad = float(statistics.median(diffs))
            entries.append(
                BaselineEntry(
                    param=param,
                    time_window=window,
                    median=round(med, 2),
                    mad=round(mad, 3),
                    n_samples=len(valid_vals),
                )
            )
    return entries


def compute_zscores_pure(
    reading: ReadingVec, baselines: list[BaselineEntry]
) -> dict[str, float]:
    """Calculates raw signed z-scores for the reading's local time window."""
    window = timewin.window_of(reading.ts)
    window_baselines = {b.param: b for b in baselines if b.time_window == window}

    zscores: dict[str, float] = {}
    for param, b in window_baselines.items():
        val = getattr(reading, param, None)
        if val is not None:
            mad_safe = max(b.mad, MAD_EPSILON)
            z = (float(val) - b.median) / (1.4826 * mad_safe)
            zscores[param] = round(z, 2)
    return zscores


def evaluate_alert_pure(
    reading: ReadingVec,
    baselines: list[BaselineEntry],
    recent_zscores: list[dict[str, float]],
    phase: Phase,
    anomaly_score: float | None = None,
) -> AlertResult:
    """Evaluates clinical alert level following frozen clinical guidelines."""
    if not reading.worn:
        return AlertResult(
            level="no_data",
            composite_score=0.0,
            triggered_params={},
            reason="not_worn",
            anomaly_score=anomaly_score,
        )

    zscores = compute_zscores_pure(reading, baselines)
    spo2 = reading.spo2
    hr = reading.hr_mean
    steps = reading.steps or 0

    # 1. Hard clinical overrides — bypass composite entirely
    if spo2 is not None and spo2 < CRITICAL_SPO2:
        return AlertResult(
            level="red",
            composite_score=5.0,
            triggered_params={"spo2": -3.5},
            reason="critical_spo2",
            anomaly_score=anomaly_score,
        )

    if hr is not None and hr > CRITICAL_HR_AT_REST and steps <= REST_STEPS_MAX:
        return AlertResult(
            level="red",
            composite_score=5.0,
            triggered_params={"hr_mean": 3.8},
            reason="critical_hr_at_rest",
            anomaly_score=anomaly_score,
        )

    # 2. Compute directional z and composite score
    composite = 0.0
    triggered: dict[str, float] = {}

    for param, z in zscores.items():
        # Mask heart rate during physical activity
        if param == "hr_mean" and steps > REST_STEPS_MAX:
            continue

        direction = PARAM_DIRECTION.get(param, 0)
        z_eff = max(0.0, z * direction) if direction != 0 else abs(z)

        if z_eff > Z_DEADZONE:
            weight = WEIGHTS.get(param, 1.0)
            composite += weight * (z_eff - Z_DEADZONE)
            triggered[param] = round(z, 2)

    composite = round(composite, 2)

    # 3. Persistence verification across consecutive windows
    is_persistent = True
    if recent_zscores and len(recent_zscores) >= 2:
        # Check if at least 1 triggered param was also deviating in past windows
        for past_z in recent_zscores:
            past_triggered = any(
                abs(past_z.get(p, 0)) > Z_DEADZONE for p in triggered.keys()
            )
            if not past_triggered:
                is_persistent = False
                break

    # 4. Phase gating and Alert level determination
    level: AlertLevel = "green"
    reason = "normal"

    if phase == "calib":
        level = "green"
        reason = "calibrating"
    elif composite >= RED_THRESHOLD and len(triggered) >= MIN_TRIGGERED_PARAMS:
        if is_persistent:
            level = "red"
            reason = "composite_threshold_red"
        else:
            level = "amber"
            reason = "transient_high_deviation"
    elif composite >= AMBER_THRESHOLD and len(triggered) >= MIN_TRIGGERED_PARAMS:
        if phase == "learning":
            # Learning phase absorbs mild deviations
            level = "green"
            reason = "learning_phase_suppressed"
        elif is_persistent:
            level = "amber"
            reason = "composite_threshold_amber"
        else:
            level = "green"
            reason = "transient_mild_deviation"

    return AlertResult(
        level=level,
        composite_score=composite,
        triggered_params=triggered,
        reason=reason,
        anomaly_score=anomaly_score,
    )


def compute_trend_pure(daily_raw_scores: list[tuple[int, float]]) -> TrendResult:
    """Computes linear regression slope over daily raw scores (7 local days)."""
    n = len(daily_raw_scores)
    if n < 2:
        return TrendResult(
            slope=0.0,
            direction="stable",
            recommendation_key="rec.continue_monitoring",
            days_used=n,
        )

    x = [pt[0] for pt in daily_raw_scores]
    y = [pt[1] for pt in daily_raw_scores]
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    denom = sum((xi - x_mean) ** 2 for xi in x)
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / denom if denom != 0 else 0.0

    if slope > TREND_SLOPE_WORSENING:
        direction = "worsening"
        rec = "rec.contact_today"
    elif slope < TREND_SLOPE_IMPROVING:
        direction = "improving"
        rec = "rec.continue_monitoring"
    else:
        direction = "stable"
        rec = "rec.routine_followup"

    return TrendResult(
        slope=round(slope, 3),
        direction=direction,  # type: ignore
        recommendation_key=rec,
        days_used=n,
    )


def detect_problems_pure(
    reading: ReadingVec, baselines: list[BaselineEntry]
) -> list[ProblemItem]:
    """Generates human-readable clinical root-cause problem breakdowns."""
    window = timewin.window_of(reading.ts)
    window_b = {b.param: b for b in baselines if b.time_window == window}
    problems: list[ProblemItem] = []

    for param, b in window_b.items():
        val = getattr(reading, param, None)
        if val is None:
            continue

        med = b.median
        mad = b.mad
        low = round(med - 1.5 * mad, 1)
        high = round(med + 1.5 * mad, 1)
        val_f = float(val)

        is_problem = False
        severity: Literal["mild", "moderate", "severe"] = "mild"
        diff = val_f - med

        if param == "spo2" and val_f < low:
            is_problem = True
            severity = "severe" if val_f < CRITICAL_SPO2 else ("moderate" if val_f < 92 else "mild")
            explanation = (
                f"Kislorod to'yinishi me'yordan {abs(round(diff, 1))}% ga pasaygan. "
                f"Nafas qisishi yoki holsizlik kuzatilishi mumkin."
            )
        elif param == "hr_mean" and val_f > high:
            is_problem = True
            severity = "severe" if val_f > 120 else ("moderate" if val_f > 100 else "mild")
            explanation = (
                f"Yurak urishi shaxsiy normadan {round(diff, 1):+g} bpm ga yuqori (taxikardiya alomati)."
            )
        elif param == "skin_temp" and val_f > high:
            is_problem = True
            severity = "moderate" if val_f > 37.8 else "mild"
            explanation = f"Tana harorati me'yordan {round(diff, 1):+g}°C ga ko'tarilgan."
        elif param == "rr_est" and val_f > high:
            is_problem = True
            severity = "moderate" if val_f > 24 else "mild"
            explanation = f"Nafas olish tezlashgan ({round(val_f, 1)} nafas/daqiqada)."
        elif param == "rmssd" and val_f < low:
            is_problem = True
            severity = "mild"
            explanation = "Yurak ritmi variabilligi pasaygan — tana charchoq yoki stress holatida."

        if is_problem:
            problems.append(
                ProblemItem(
                    param=param,
                    label=PARAM_NAMES_UZ.get(param, param),
                    deviation=f"{round(diff, 1):+g} og'ish",
                    current_value=round(val_f, 1),
                    baseline_range=f"{low} - {high}",
                    severity=severity,
                    explanation=explanation,
                )
            )

    return problems


def compute_prognosis_pure(
    level: AlertLevel, trend: TrendResult, problems: list[ProblemItem]
) -> PrognosisInfo:
    """Generates 72-hour clinical prognosis and early warning recommendation."""
    if level == "red":
        risk_level = "high"
        prob = 80 if trend.direction == "worsening" else 65
        summary = (
            "Dekommutatsiya xavfi yuqori. Oxirgi ko'rsatkichlar jiddiy fiziologik og'ishlarni ko'rsatmoqda."
        )
        rec = "Shifokor bilan darhol bog'laning yoki favqulodda yordam ko'rsatilishini ta'minlang."
    elif level == "amber":
        risk_level = "moderate"
        prob = 50 if trend.direction == "worsening" else 35
        summary = (
            "Holatda salbiy o'zgarishlar sezilmoqda. 72 soat ichida yomonlashuv ehtimoli mavjud."
        )
        rec = "Bemorning dam olishini ta'minlang, dori-darmonlar qabulini nazorat qiling va shifokorga xabar bering."
    elif level == "no_data":
        risk_level = "low"
        prob = 0
        summary = "Aqlli soatdan 45 daqiqadan beri ma'lumot kelmayapti. Xavfni aniqlash imkoni yo'q."
        rec = "Soat bemorning qo'liga to'g'ri taqilganligini va quvvati borligini tekshiring."
    else:
        risk_level = "low"
        prob = 15 if trend.direction == "worsening" else 5
        summary = "Barcha asosiy fiziologik ko'rsatkichlar bemorning shaxsiy normasi doirasida barqaror."
        rec = "Muntazam monitoring va belgilangan rejimni davom ettiring."

    return PrognosisInfo(
        risk_level=risk_level,
        risk_probability_pct=prob,
        early_warning_hours=72,
        summary=summary,
        recommendation=rec,
    )

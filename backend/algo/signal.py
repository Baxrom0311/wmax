"""Clinical signal evaluation engine.

Implements AlgoAPI signal evaluation as a pure function:
- evaluate_alert: Multi-parameter composite z-score, directional checks,
  clinical hard overrides, persistence verification, and phase gating.
- apply_medication_context: Context-aware damping of expected pharmacological effects.
- is_auto_critical_sos: Automated high-confidence trigger for life-threatening emergencies.
"""
from __future__ import annotations

from typing import Any

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
    AlertLevel,
    AlertResult,
    BaselineEntry,
    Phase,
    ReadingVec,
)

from .baseline import compute_zscores

# Damping factor applied to expected pharmacological effects (Architecture V2 Section 8.2)
MEDICATION_DAMPING: float = 0.5

# Critical emergency thresholds for automated SOS (Section 6.4)
AUTO_CRITICAL_SPO2: float = 85.0
AUTO_CRITICAL_HR_HIGH: float = 150.0
AUTO_CRITICAL_HR_LOW: float = 35.0


def apply_medication_context(
    zscores: dict[str, float],
    medications: list[dict[str, Any]] | None = None,
) -> dict[str, float]:
    """Damps expected pharmacological effects in z-scores to reduce false alarms.

    E.g. beta-blockers intentionally lower heart rate; dampening the negative z-score
    prevents spurious bradycardia alerts while retaining responsiveness to extreme drops.
    """
    if not medications:
        return dict(zscores)

    adjusted = dict(zscores)
    for med in medications:
        # Ignore stopped medications
        if med.get("stopped_at") is not None:
            continue

        affects = med.get("affects_params") or {}
        if not isinstance(affects, dict):
            continue

        for param, effect in affects.items():
            if param not in adjusted:
                continue

            # "lowers" = decrease is clinically expected therapy outcome
            if effect == "lowers" and adjusted[param] < 0:
                adjusted[param] = round(adjusted[param] * MEDICATION_DAMPING, 3)
            # "raises" = increase is clinically expected therapy outcome
            elif effect == "raises" and adjusted[param] > 0:
                adjusted[param] = round(adjusted[param] * MEDICATION_DAMPING, 3)

    return adjusted


def is_auto_critical_reading(reading: ReadingVec) -> bool:
    """Checks if a single reading reaches absolute life-threatening thresholds."""
    if not reading.worn:
        return False

    spo2 = reading.spo2
    if spo2 is not None and spo2 < AUTO_CRITICAL_SPO2:
        return True

    hr = reading.hr_mean
    steps = reading.steps or 0
    if hr is not None and steps <= REST_STEPS_MAX:
        if hr > AUTO_CRITICAL_HR_HIGH or hr < AUTO_CRITICAL_HR_LOW:
            return True

    return False


def is_auto_critical_sos(
    current_reading: ReadingVec,
    recent_readings: list[ReadingVec] | None = None,
) -> bool:
    """Determines whether to raise automated SOS (auto_critical) per Section 6.4.

    Requires:
    1. worn = True
    2. SpO2 < 85 OR (HR > 150 or HR < 35 at rest)
    3. Sustained across at least 3 consecutive 5-minute windows (current + 2 past)
    """
    if not is_auto_critical_reading(current_reading):
        return False

    if not recent_readings or len(recent_readings) < 2:
        return False

    # Check last 2 readings for sustained critical deviation
    return all(is_auto_critical_reading(r) for r in recent_readings[:2])


def evaluate_alert(
    reading: ReadingVec,
    baselines: list[BaselineEntry],
    recent_zscores: list[dict[str, float]],
    phase: Phase,
    anomaly_score: float | None = None,
    medications: list[dict[str, Any]] | None = None,
) -> AlertResult:
    """Evaluates clinical alert level following frozen clinical domain rules."""
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

    # 1. Hard clinical overrides — instant, bypass composite and persistence.
    # Note: Hard clinical overrides are NEVER damped by medication context!
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

    # 2. Apply medication context to z-scores if provided (Architecture V2 Section 8.2)
    effective_zscores = apply_medication_context(zscores, medications)

    # 3. Compute directional z and composite score
    composite = 0.0
    triggered: dict[str, float] = {}

    for param, z in effective_zscores.items():
        # Mask heart rate during physical exertion
        if param == "hr_mean" and steps > REST_STEPS_MAX:
            continue

        direction = PARAM_DIRECTION.get(param, 0)
        z_eff = max(0.0, z * direction) if direction != 0 else abs(z)

        if z_eff > Z_DEADZONE:
            weight = WEIGHTS.get(param, 1.0)
            composite += weight * (z_eff - Z_DEADZONE)
            triggered[param] = round(z, 2)

    composite = round(composite, 2)

    # 4. Persistence verification across consecutive windows (3 windows = 15 mins)
    is_persistent = True
    if recent_zscores and len(recent_zscores) >= 2:
        for past_z in recent_zscores:
            past_triggered = any(
                abs(past_z.get(p, 0)) > Z_DEADZONE for p in triggered.keys()
            )
            if not past_triggered:
                is_persistent = False
                break

    # 5. Phase gating and Alert level determination
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

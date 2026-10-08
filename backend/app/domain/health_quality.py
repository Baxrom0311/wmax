from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.health_data import HealthSampleIn

FUTURE_TIMESTAMP_TOLERANCE = timedelta(minutes=5)

VALUE_RANGES: dict[str, tuple[float, float]] = {
    "heart_rate_bpm": (20, 260),
    "resting_heart_rate_bpm": (20, 220),
    "heart_rate_variability_rmssd_ms": (0, 600),
    "heart_rate_variability_sdnn_ms": (0, 600),
    "blood_pressure_systolic_mmhg": (30, 300),
    "blood_pressure_diastolic_mmhg": (20, 200),
    "blood_glucose_mmol_l": (0.1, 100),
    "body_fat_pct": (0, 100),
    "vo2_max_ml_kg_min": (0, 120),
    "oxygen_saturation_pct": (0, 100),
    "respiratory_rate_bpm": (1, 100),
    "skin_temperature_c": (20, 45),
    "skin_temperature_baseline_c": (20, 45),
    "body_temperature_c": (25, 45),
    "steps": (0, 250_000),
    "daily_steps": (0, 250_000),
    "distance_m": (0, 500_000),
    "speed_mps": (0, 100),
    "pace_mps": (0, 100),
    "active_calories_kcal": (0, 100_000),
    "total_calories_kcal": (0, 100_000),
    "basal_calories_kcal": (0, 100_000),
    "elevation_gain_m": (0, 100_000),
    "floors": (0, 100_000),
    "battery_pct": (0, 100),
}

EXPECTED_UNITS: dict[str, set[str]] = {
    "heart_rate_bpm": {"bpm"},
    "resting_heart_rate_bpm": {"bpm"},
    "heart_rate_variability_rmssd_ms": {"ms"},
    "heart_rate_variability_sdnn_ms": {"ms"},
    "blood_pressure_systolic_mmhg": {"mmHg"},
    "blood_pressure_diastolic_mmhg": {"mmHg"},
    "blood_glucose_mmol_l": {"mmol/L"},
    "body_fat_pct": {"%"},
    "vo2_max_ml_kg_min": {"mL/kg/min"},
    "oxygen_saturation_pct": {"%"},
    "respiratory_rate_bpm": {"breaths/min"},
    "skin_temperature_c": {"celsius"},
    "skin_temperature_baseline_c": {"celsius"},
    "skin_temperature_delta_c": {"celsius"},
    "body_temperature_c": {"celsius"},
    "steps": {"count", "steps"},
    "daily_steps": {"steps"},
    "distance_m": {"m", "meter"},
    "speed_mps": {"m/s"},
    "pace_mps": {"m/s"},
    "active_calories_kcal": {"kcal"},
    "total_calories_kcal": {"kcal"},
    "basal_calories_kcal": {"kcal"},
    "elevation_gain_m": {"m"},
    "floors": {"floors"},
    "battery_pct": {"%"},
}


def is_worn_window(worn: bool, worn_pct: int | None) -> bool:
    """Treat an explicitly zero wear fraction as unworn; keep legacy nulls unchanged."""
    return worn and worn_pct != 0


def sample_quality_flags(
    sample: HealthSampleIn,
    *,
    received_at: datetime | None = None,
) -> tuple[str, ...]:
    """Return explainable ingestion-quality warnings without judging clinical values."""
    flags: list[str] = []
    if sample.source_record_id is None:
        flags.append("missing_source_record_id")
    if sample.value_num is not None and not sample.unit:
        flags.append("missing_unit")
    elif (
        sample.value_num is not None
        and sample.metric in EXPECTED_UNITS
        and sample.unit not in EXPECTED_UNITS[sample.metric]
    ):
        flags.append("unexpected_unit")
    if sample.value_num is not None and sample.metric in VALUE_RANGES:
        minimum, maximum = VALUE_RANGES[sample.metric]
        if not minimum <= sample.value_num <= maximum:
            flags.append("value_out_of_expected_range")

    now = received_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if sample.recorded_at > now + FUTURE_TIMESTAMP_TOLERANCE:
        flags.append("recorded_at_in_future")
    if sample.started_at is not None and sample.recorded_at < sample.started_at:
        flags.append("recorded_before_interval_start")
    if sample.ended_at is not None and sample.recorded_at > sample.ended_at:
        flags.append("recorded_after_interval_end")
    return tuple(flags)

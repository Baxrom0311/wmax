"""Deterministic daily health summary built from stored device samples.

The summary reports measurements, their freshness and how many samples back
them. It never fills gaps: a metric without usable samples is reported as
missing rather than as a normal value. The only derived score (stress) is an
explicitly labelled wellness estimate relative to the person's own HRV
baseline, not a clinical measurement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from statistics import median
from typing import Any

from timewin import NO_DATA_MINUTES, local_day

# Samples carrying any of these ingest flags are not trustworthy measurements.
BAD_QUALITY_FLAGS = frozenset(
    {"missing_unit", "unexpected_unit", "value_out_of_expected_range", "recorded_at_in_future"}
)
MIN_SAMPLE_QUALITY = 0.5

VITAL_METRICS = (
    "heart_rate_bpm",
    "resting_heart_rate_bpm",
    "heart_rate_variability_rmssd_ms",
    "oxygen_saturation_pct",
    "respiratory_rate_bpm",
    "skin_temperature_delta_c",
    "skin_temperature_c",
)
# Sparse metrics are measured rarely (days or weeks apart), so their latest
# value is looked up over a longer horizon than the daily trend window.
SPARSE_METRICS = (
    "vo2_max_ml_kg_min",
    "blood_pressure_systolic_mmhg",
    "blood_pressure_diastolic_mmhg",
    "blood_glucose_mmol_l",
    "weight_kg",
    "body_fat_pct",
    "body_temperature_c",
)
ACTIVITY_METRICS = (
    "steps",
    "distance_m",
    "active_calories_kcal",
    "total_calories_kcal",
    "floors",
    "elevation_gain_m",
)
EVENT_METRICS = ("fall_detected",)
SUMMARY_METRICS = VITAL_METRICS + SPARSE_METRICS + ACTIVITY_METRICS + ("daily_steps",) + EVENT_METRICS
SPARSE_LOOKBACK_DAYS = 90

DEFAULT_STEP_GOAL = 6000
SPO2_LOW_PCT = 90.0
RESTING_HR_RISE_BPM = 7.0
HRV_DROP_RATIO = 0.75
SHORT_SLEEP_MINUTES = 6 * 60
SKIN_TEMP_DELTA_HIGH_C = 1.0
MIN_BASELINE_DAYS = 3

ASLEEP_STAGES = frozenset({"sleeping", "light", "deep", "rem", "unknown", "asleep"})
AWAKE_STAGES = frozenset({"awake", "awake_in_bed", "out_of_bed"})


@dataclass(frozen=True)
class SampleRow:
    metric: str
    recorded_at: datetime
    value_num: float | None
    source: str
    value_text: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    quality: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SleepRow:
    start_time: datetime
    end_time: datetime
    source: str
    stages: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ExerciseRow:
    exercise_type: str
    start_time: datetime
    end_time: datetime
    source: str
    metrics: dict[str, Any] = field(default_factory=dict)


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def is_usable(sample: SampleRow) -> bool:
    if sample.value_num is None and sample.metric not in EVENT_METRICS:
        return False
    if sample.quality is not None and sample.quality < MIN_SAMPLE_QUALITY:
        return False
    flags = set((sample.metadata or {}).get("ingest_quality_flags") or [])
    return not flags.intersection(BAD_QUALITY_FLAGS)


def is_daily_cumulative(sample: SampleRow) -> bool:
    """True when the value is a running total since local midnight.

    Wear OS *_DAILY data types report cumulative totals; adding them to the
    interval deltas from the same day would double count activity.
    """
    if sample.metric == "daily_steps":
        return True
    if (sample.metadata or {}).get("aggregation") == "daily_cumulative":
        return True
    # Older watch builds sent CALORIES_DAILY/DISTANCE_DAILY without the marker.
    return sample.source == "wear_health_services" and sample.metric in {
        "total_calories_kcal",
        "distance_m",
    }


def _round(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(value, digits)


def _point(sample: SampleRow) -> dict[str, Any]:
    return {
        "value": _round(sample.value_num, 2),
        "at": _utc(sample.recorded_at),
        "source": sample.source,
    }


def _day_window(now: datetime, days: int) -> list[date]:
    today = local_day(now)
    return [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]


def _vital_summary(samples: list[SampleRow], days: list[date]) -> dict[str, Any]:
    by_day: dict[date, list[float]] = {}
    for sample in samples:
        by_day.setdefault(local_day(sample.recorded_at), []).append(float(sample.value_num))
    latest = max(samples, key=lambda s: _utc(s.recorded_at)) if samples else None
    daily = []
    for day in days:
        values = by_day.get(day, [])
        daily.append(
            {
                "day": day,
                "avg": _round(sum(values) / len(values)) if values else None,
                "min": _round(min(values)) if values else None,
                "max": _round(max(values)) if values else None,
                "n": len(values),
            }
        )
    return {
        "latest": _point(latest) if latest else None,
        "daily": daily,
        "samples_n": sum(len(values) for day, values in by_day.items() if day in days),
    }


def _baseline(daily: list[dict[str, Any]], *, exclude: date) -> float | None:
    """Median of earlier daily means; needs several days to mean anything."""
    values = [row["avg"] for row in daily if row["avg"] is not None and row["day"] != exclude]
    if len(values) < MIN_BASELINE_DAYS:
        return None
    return round(median(values), 1)


def stress_score(hrv_ms: float, baseline_ms: float) -> int:
    """Wellness stress estimate 0..100 from HRV relative to personal baseline.

    At the personal baseline the score is 30; lower HRV than usual raises it.
    """
    if baseline_ms <= 0:
        raise ValueError("baseline must be positive")
    ratio = hrv_ms / baseline_ms
    return int(max(0, min(100, round(30 + 70 * (1 - ratio)))))


def stress_level(score: int) -> str:
    if score < 40:
        return "low"
    if score < 70:
        return "medium"
    return "high"


def _activity_summary(samples: list[SampleRow], days: list[date]) -> dict[str, Any]:
    # (day, metric, source) -> [interval sum, cumulative max]
    totals: dict[tuple[date, str, str], list[float]] = {}
    for sample in samples:
        metric = "steps" if sample.metric == "daily_steps" else sample.metric
        key = (local_day(sample.ended_at or sample.recorded_at), metric, sample.source)
        bucket = totals.setdefault(key, [0.0, 0.0])
        value = float(sample.value_num)
        if is_daily_cumulative(sample):
            bucket[1] = max(bucket[1], value)
        else:
            bucket[0] += value

    # Different sources (watch, Health Connect) describe the same movement,
    # so the day's value is the most complete source, never their sum.
    per_day: dict[tuple[date, str], float] = {}
    for (day, metric, _source), (interval_sum, cumulative_max) in totals.items():
        value = max(interval_sum, cumulative_max)
        per_day[(day, metric)] = max(per_day.get((day, metric), 0.0), value)

    daily = []
    for day in days:
        row: dict[str, Any] = {"day": day}
        for metric in ACTIVITY_METRICS:
            value = per_day.get((day, metric))
            digits = 0 if metric in {"steps", "floors"} else 1
            row[metric] = None if value is None else _round(value, digits)
        daily.append(row)
    return {"today": daily[-1] if daily else None, "daily": daily, "goal_steps": DEFAULT_STEP_GOAL}


def _stage_minutes(session: SleepRow) -> dict[str, float]:
    minutes = {"deep": 0.0, "light": 0.0, "rem": 0.0, "awake": 0.0, "unspecified": 0.0}
    for stage in session.stages:
        try:
            start = _utc(datetime.fromisoformat(str(stage["start_time"])))
            end = _utc(datetime.fromisoformat(str(stage["end_time"])))
        except (KeyError, ValueError):
            continue
        length = max(0.0, (end - start).total_seconds() / 60)
        name = str(stage.get("stage", "unknown")).lower()
        if name in {"deep", "light", "rem"}:
            minutes[name] += length
        elif name in AWAKE_STAGES:
            minutes["awake"] += length
        elif name in ASLEEP_STAGES:
            minutes["unspecified"] += length
    return minutes


def _sleep_night(sessions: list[SleepRow], day: date) -> dict[str, Any]:
    in_bed = sum((_utc(s.end_time) - _utc(s.start_time)).total_seconds() / 60 for s in sessions)
    stages = {"deep": 0.0, "light": 0.0, "rem": 0.0, "awake": 0.0, "unspecified": 0.0}
    has_stages = any(s.stages for s in sessions)
    for session in sessions:
        for name, value in _stage_minutes(session).items():
            stages[name] += value
    if has_stages:
        asleep = stages["deep"] + stages["light"] + stages["rem"] + stages["unspecified"]
    else:
        asleep = in_bed
    return {
        "day": day,
        "start_time": min(_utc(s.start_time) for s in sessions),
        "end_time": max(_utc(s.end_time) for s in sessions),
        "source": sessions[0].source,
        "in_bed_minutes": round(in_bed),
        "asleep_minutes": round(asleep),
        "efficiency_pct": round(100 * asleep / in_bed) if in_bed > 0 and has_stages else None,
        "stages_minutes": {name: round(value) for name, value in stages.items()} if has_stages else None,
    }


def _sleep_summary(sessions: list[SleepRow], days: list[date]) -> dict[str, Any]:
    # A night belongs to the local day the person woke up on. When several
    # sources recorded it, keep the source with the longest coverage.
    grouped: dict[tuple[date, str], list[SleepRow]] = {}
    for session in sessions:
        grouped.setdefault((local_day(session.end_time), session.source), []).append(session)
    nights: dict[date, dict[str, Any]] = {}
    for (day, _source), rows in grouped.items():
        night = _sleep_night(rows, day)
        current = nights.get(day)
        if current is None or night["in_bed_minutes"] > current["in_bed_minutes"]:
            nights[day] = night
    daily = [
        {
            "day": day,
            "asleep_minutes": nights[day]["asleep_minutes"] if day in nights else None,
            "in_bed_minutes": nights[day]["in_bed_minutes"] if day in nights else None,
        }
        for day in days
    ]
    recorded = [nights[day] for day in days if day in nights]
    return {"last_night": recorded[-1] if recorded else None, "daily": daily}


def _stress_summary(hrv: dict[str, Any], days: list[date], now: datetime) -> dict[str, Any]:
    today = days[-1]
    baseline = _baseline(hrv["daily"], exclude=today)
    result: dict[str, Any] = {
        "method": "hrv_rmssd_vs_personal_baseline",
        "is_estimate": True,
        "baseline_hrv_ms": baseline,
        "latest": None,
        "daily": [],
    }
    if baseline is None:
        result["status"] = "insufficient_baseline"
        result["daily"] = [{"day": row["day"], "score": None} for row in hrv["daily"]]
        return result
    latest = hrv["latest"]
    if latest is not None and now - latest["at"] <= timedelta(hours=24):
        score = stress_score(latest["value"], baseline)
        result["latest"] = {"score": score, "level": stress_level(score), "at": latest["at"]}
    result["daily"] = [
        {"day": row["day"], "score": stress_score(row["avg"], baseline) if row["avg"] is not None else None}
        for row in hrv["daily"]
    ]
    result["status"] = "ok" if result["latest"] else "no_recent_hrv"
    return result


def _blood_pressure(samples_by_metric: dict[str, list[SampleRow]]) -> dict[str, Any] | None:
    systolic = samples_by_metric.get("blood_pressure_systolic_mmhg", [])
    diastolic = {
        _utc(s.recorded_at): s for s in samples_by_metric.get("blood_pressure_diastolic_mmhg", [])
    }
    paired = [(s, diastolic[_utc(s.recorded_at)]) for s in systolic if _utc(s.recorded_at) in diastolic]
    if not paired:
        return None
    sys_sample, dia_sample = max(paired, key=lambda pair: _utc(pair[0].recorded_at))
    return {
        "systolic": round(sys_sample.value_num),
        "diastolic": round(dia_sample.value_num),
        "at": _utc(sys_sample.recorded_at),
        "source": sys_sample.source,
    }


def _insights(summary: dict[str, Any], spo2_today: list[SampleRow], now: datetime) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    freshness = summary["freshness"]
    if freshness["status"] != "fresh":
        insights.append(
            {"key": "data_stale", "severity": "attention", "params": {"last_sample_at": freshness["last_sample_at"]}}
        )
    low = [s for s in spo2_today if s.value_num < SPO2_LOW_PCT]
    if low:
        insights.append(
            {
                "key": "spo2_low_today",
                "severity": "attention",
                "params": {"count": len(low), "min": _round(min(s.value_num for s in low))},
            }
        )
    resting = summary["metrics"]["resting_heart_rate_bpm"]
    resting_baseline = _baseline(resting["daily"], exclude=resting["daily"][-1]["day"])
    if resting["latest"] and resting_baseline is not None:
        rise = resting["latest"]["value"] - resting_baseline
        if rise >= RESTING_HR_RISE_BPM:
            insights.append(
                {
                    "key": "resting_hr_above_baseline",
                    "severity": "attention",
                    "params": {"value": resting["latest"]["value"], "baseline": resting_baseline},
                }
            )
    hrv = summary["metrics"]["heart_rate_variability_rmssd_ms"]
    hrv_baseline = summary["stress"]["baseline_hrv_ms"]
    today_hrv = hrv["daily"][-1]["avg"]
    if hrv_baseline and today_hrv is not None and today_hrv < HRV_DROP_RATIO * hrv_baseline:
        insights.append(
            {"key": "hrv_below_baseline", "severity": "info", "params": {"value": today_hrv, "baseline": hrv_baseline}}
        )
    skin = summary["metrics"]["skin_temperature_delta_c"]["latest"]
    if skin and now - skin["at"] <= timedelta(hours=24) and skin["value"] >= SKIN_TEMP_DELTA_HIGH_C:
        insights.append({"key": "skin_temp_above_baseline", "severity": "attention", "params": {"delta": skin["value"]}})
    night = summary["sleep"]["last_night"]
    if night and night["day"] == local_day(now) and night["asleep_minutes"] < SHORT_SLEEP_MINUTES:
        insights.append({"key": "short_sleep", "severity": "info", "params": {"minutes": night["asleep_minutes"]}})
    today = summary["activity"]["today"]
    if today and today["steps"] is not None and today["steps"] >= summary["activity"]["goal_steps"]:
        insights.append({"key": "steps_goal_met", "severity": "positive", "params": {"steps": today["steps"]}})
    if summary["events"]["falls"]:
        insights.append(
            {"key": "fall_detected", "severity": "attention", "params": {"count": len(summary["events"]["falls"])}}
        )
    return insights


def build_health_summary(
    samples: list[SampleRow],
    sleep_sessions: list[SleepRow],
    exercise_sessions: list[ExerciseRow],
    *,
    now: datetime,
    days: int,
) -> dict[str, Any]:
    now = _utc(now)
    window = _day_window(now, days)
    first_day = window[0]

    usable = [s for s in samples if is_usable(s)]
    excluded = len(samples) - len(usable)
    by_metric: dict[str, list[SampleRow]] = {}
    for sample in usable:
        by_metric.setdefault(sample.metric, []).append(sample)

    def in_window(sample: SampleRow) -> bool:
        return local_day(sample.recorded_at) >= first_day

    metrics = {
        metric: _vital_summary([s for s in by_metric.get(metric, []) if in_window(s)], window)
        for metric in VITAL_METRICS
    }
    sparse = {}
    for metric in SPARSE_METRICS:
        rows = by_metric.get(metric, [])
        latest = max(rows, key=lambda s: _utc(s.recorded_at)) if rows else None
        sparse[metric] = _point(latest) if latest else None

    hr = metrics["heart_rate_bpm"]
    today = window[-1]
    hr["today"] = next(row for row in hr["daily"] if row["day"] == today)

    activity_samples = [
        s for s in usable if s.metric in ACTIVITY_METRICS + ("daily_steps",) and in_window(s)
    ]
    timestamps = [_utc(s.recorded_at) for s in usable if s.metric not in EVENT_METRICS]
    last_sample_at = max(timestamps) if timestamps else None
    if last_sample_at is None:
        freshness_status = "no_data"
    elif now - last_sample_at > timedelta(minutes=NO_DATA_MINUTES):
        freshness_status = "stale"
    else:
        freshness_status = "fresh"

    falls = [
        {"at": _utc(s.recorded_at), "source": s.source}
        for s in by_metric.get("fall_detected", [])
        if in_window(s)
    ]
    exercises = sorted(
        (e for e in exercise_sessions if local_day(e.end_time) >= first_day),
        key=lambda e: _utc(e.start_time),
        reverse=True,
    )[:10]

    summary: dict[str, Any] = {
        "generated_at": now,
        "window_days": days,
        "timezone": "Asia/Tashkent",
        "freshness": {
            "status": freshness_status,
            "last_sample_at": last_sample_at,
            "stale_after_minutes": NO_DATA_MINUTES,
            "excluded_samples": excluded,
        },
        "metrics": metrics,
        "latest_measurements": sparse,
        "blood_pressure": _blood_pressure(by_metric),
        "activity": _activity_summary(activity_samples, window),
        "sleep": _sleep_summary(
            [s for s in sleep_sessions if local_day(s.end_time) >= first_day], window
        ),
        "exercise_sessions": [
            {
                "exercise_type": e.exercise_type,
                "start_time": _utc(e.start_time),
                "end_time": _utc(e.end_time),
                "duration_minutes": round((_utc(e.end_time) - _utc(e.start_time)).total_seconds() / 60),
                "source": e.source,
            }
            for e in exercises
        ],
        "events": {"falls": falls},
    }
    summary["stress"] = _stress_summary(metrics["heart_rate_variability_rmssd_ms"], window, now)
    spo2_today = [s for s in by_metric.get("oxygen_saturation_pct", []) if local_day(s.recorded_at) == today]
    summary["insights"] = _insights(summary, spo2_today, now)
    return summary

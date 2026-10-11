from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.dialects import postgresql

from app.core.exceptions import ForbiddenException
from app.domain.health_summary import (
    SampleRow,
    SleepRow,
    build_health_summary,
    stress_level,
    stress_score,
)
from app.schemas.health_summary import HealthSummary
from app.services.health_data_service import HealthDataIngestService
from app.services.health_summary_service import HealthSummaryService
from app.services.pipeline_service import PipelineService
from app.services.relative_service import RelativeService

# 2026-10-09 15:00 in Tashkent (UTC+5).
NOW = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


def sample(metric, value, at, *, source="health_connect", unit=None, **kwargs):
    return SampleRow(
        metric=metric,
        recorded_at=at,
        value_num=value,
        source=source,
        **kwargs,
    )


def summary(samples=(), sleeps=(), days=7):
    return build_health_summary(list(samples), list(sleeps), [], now=NOW, days=days)


def test_no_samples_reports_no_data_instead_of_normal_values():
    result = summary()
    assert result["freshness"]["status"] == "no_data"
    assert result["metrics"]["heart_rate_bpm"]["latest"] is None
    assert result["metrics"]["oxygen_saturation_pct"]["daily"][-1]["avg"] is None
    assert result["activity"]["today"]["steps"] is None
    assert result["sleep"]["last_night"] is None
    assert result["stress"]["status"] == "insufficient_baseline"
    assert [i["key"] for i in result["insights"]] == ["data_stale"]
    HealthSummary.model_validate({"patient_id": "p", **result})


def test_stale_data_is_flagged_not_reported_as_current():
    result = summary([sample("heart_rate_bpm", 72, NOW - timedelta(hours=2))])
    assert result["freshness"]["status"] == "stale"
    assert result["metrics"]["heart_rate_bpm"]["latest"]["value"] == 72
    assert "data_stale" in [i["key"] for i in result["insights"]]


def test_low_quality_and_flagged_samples_are_excluded():
    result = summary(
        [
            sample("heart_rate_bpm", 70, NOW - timedelta(minutes=5)),
            sample("heart_rate_bpm", 190, NOW - timedelta(minutes=4), quality=0.2),
            sample(
                "heart_rate_bpm",
                180,
                NOW - timedelta(minutes=3),
                metadata={"ingest_quality_flags": ["unexpected_unit"]},
            ),
        ]
    )
    today = result["metrics"]["heart_rate_bpm"]["today"]
    assert today["max"] == 70
    assert today["n"] == 1
    assert result["freshness"]["excluded_samples"] == 2


def test_daily_cumulative_steps_are_not_added_to_interval_steps():
    watch = "wear_health_services"
    result = summary(
        [
            sample("steps", 1200, NOW - timedelta(hours=2), source=watch),
            sample("steps", 800, NOW - timedelta(hours=1), source=watch),
            sample("daily_steps", 1500, NOW - timedelta(hours=2), source=watch),
            sample("daily_steps", 2000, NOW - timedelta(hours=1), source=watch),
            # Old watch builds sent DISTANCE_DAILY as plain distance_m.
            sample("distance_m", 900, NOW - timedelta(hours=2), source=watch),
            sample("distance_m", 1400, NOW - timedelta(hours=1), source=watch),
        ]
    )
    today = result["activity"]["today"]
    assert today["steps"] == 2000
    assert today["distance_m"] == 1400


def test_overlapping_sources_use_most_complete_source_not_sum():
    result = summary(
        [
            sample("steps", 3000, NOW - timedelta(hours=3), source="wear_health_services"),
            sample("steps", 2500, NOW - timedelta(hours=3), source="health_connect"),
            sample("steps", 1000, NOW - timedelta(hours=1), source="health_connect"),
        ]
    )
    assert result["activity"]["today"]["steps"] == 3500


def test_days_are_grouped_by_tashkent_local_day():
    # 20:00 UTC on Oct 8 is 01:00 on Oct 9 in Tashkent.
    result = summary([sample("oxygen_saturation_pct", 96, datetime(2026, 10, 8, 20, 0, tzinfo=timezone.utc))])
    daily = result["metrics"]["oxygen_saturation_pct"]["daily"]
    assert daily[-1]["day"].isoformat() == "2026-10-09"
    assert daily[-1]["avg"] == 96


def test_spo2_below_90_today_is_reported_with_count_and_minimum():
    result = summary(
        [
            sample("oxygen_saturation_pct", 97, NOW - timedelta(minutes=10)),
            sample("oxygen_saturation_pct", 88, NOW - timedelta(minutes=20)),
            sample("oxygen_saturation_pct", 86, NOW - timedelta(minutes=30)),
        ]
    )
    insight = next(i for i in result["insights"] if i["key"] == "spo2_low_today")
    assert insight["params"] == {"count": 2, "min": 86}


def test_stress_needs_personal_baseline_and_rises_as_hrv_drops():
    hrv = [sample("heart_rate_variability_rmssd_ms", 40, NOW - timedelta(days=d)) for d in (1, 2, 3, 4)]
    without_baseline = summary(hrv[:2])
    assert without_baseline["stress"]["status"] == "insufficient_baseline"
    assert without_baseline["stress"]["latest"] is None

    result = summary(hrv + [sample("heart_rate_variability_rmssd_ms", 20, NOW - timedelta(minutes=30))])
    stress = result["stress"]
    assert stress["is_estimate"] is True
    assert stress["baseline_hrv_ms"] == 40
    assert stress["latest"]["score"] == stress_score(20, 40) == 65
    assert stress["latest"]["level"] == "medium"
    assert "hrv_below_baseline" in [i["key"] for i in result["insights"]]


def test_stress_score_bounds():
    assert stress_score(40, 40) == 30
    assert stress_score(400, 40) == 0
    assert stress_score(1, 40) == 98
    assert stress_level(30) == "low"
    assert stress_level(98) == "high"


def test_sleep_stages_efficiency_and_source_dedup():
    start = datetime(2026, 10, 8, 18, 0, tzinfo=timezone.utc)  # 23:00 local
    end = start + timedelta(hours=7)

    def stage(name, offset_min, length_min):
        s = start + timedelta(minutes=offset_min)
        return {
            "stage": name,
            "start_time": s.isoformat(),
            "end_time": (s + timedelta(minutes=length_min)).isoformat(),
        }

    staged = SleepRow(
        start_time=start,
        end_time=end,
        source="health_connect",
        stages=[
            stage("light", 0, 180),
            stage("deep", 180, 90),
            stage("rem", 270, 90),
            stage("awake", 360, 60),
        ],
    )
    partial = SleepRow(start_time=start + timedelta(hours=1), end_time=end, source="wear_health_services")
    night = summary(sleeps=[staged, partial])["sleep"]["last_night"]
    assert night["source"] == "health_connect"
    assert night["in_bed_minutes"] == 420
    assert night["asleep_minutes"] == 360
    assert night["efficiency_pct"] == 86
    assert night["stages_minutes"]["deep"] == 90


def test_short_sleep_without_stages_uses_session_length():
    start = datetime(2026, 10, 8, 21, 0, tzinfo=timezone.utc)
    result = summary(sleeps=[SleepRow(start_time=start, end_time=start + timedelta(hours=5), source="health_connect")])
    night = result["sleep"]["last_night"]
    assert night["asleep_minutes"] == 300
    assert night["stages_minutes"] is None
    assert night["efficiency_pct"] is None
    assert "short_sleep" in [i["key"] for i in result["insights"]]


def test_blood_pressure_pairs_systolic_and_diastolic():
    at = NOW - timedelta(days=20)
    result = summary(
        [
            sample("blood_pressure_systolic_mmhg", 132, at),
            sample("blood_pressure_diastolic_mmhg", 84, at),
        ]
    )
    assert result["blood_pressure"]["systolic"] == 132
    assert result["blood_pressure"]["diastolic"] == 84


def test_fall_event_is_surfaced():
    result = summary(
        [
            sample("heart_rate_bpm", 80, NOW - timedelta(minutes=2)),
            SampleRow(
                metric="fall_detected",
                recorded_at=NOW - timedelta(minutes=1),
                value_num=None,
                value_text="fall_detected",
                source="wear_health_services",
            ),
        ]
    )
    assert len(result["events"]["falls"]) == 1
    assert "fall_detected" in [i["key"] for i in result["insights"]]


@pytest.mark.asyncio
async def test_summary_service_builds_valid_response_from_rows():
    session = AsyncMock()

    def rows(items):
        result = MagicMock()
        result.all.return_value = items
        return result

    def scalars(items):
        result = MagicMock()
        result.scalars.return_value.all.return_value = items
        return result

    hr_row = MagicMock(
        metric="heart_rate_bpm",
        recorded_at=NOW - timedelta(minutes=3),
        value_num=74.0,
        value_text=None,
        source="wear_health_services",
        started_at=None,
        ended_at=None,
        quality=1.0,
        metadata_json={},
    )
    session.execute.side_effect = [rows([hr_row]), rows([]), scalars([]), scalars([])]
    patient_id = uuid.uuid4()
    result = await HealthSummaryService(session).get_summary(patient_id, days=7, now=NOW)
    assert result.patient_id == str(patient_id)
    assert result.freshness.status == "fresh"
    assert result.metrics["heart_rate_bpm"].latest.value == 74.0
    assert len(result.metrics["heart_rate_bpm"].daily) == 7


@pytest.mark.asyncio
async def test_relative_summary_link_requires_current_family_consent():
    session = AsyncMock()
    relative = MagicMock(
        account_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        access_token_created_at=None,
        accepted_at=NOW,
        revoked_at=None,
    )
    session.get.return_value = MagicMock(is_active=True, phone="+998900000000")
    no_consent = MagicMock()
    no_consent.scalar_one_or_none.return_value = None
    session.execute.return_value = no_consent
    service = RelativeService(session)
    service.relative_repo.get_by_token = AsyncMock(return_value=relative)
    with pytest.raises(ForbiddenException):
        await service.authorize_link("token", caregiver_phone="+998900000000")


@pytest.mark.asyncio
async def test_daily_steps_running_total_is_not_summed_into_reading_window():
    session = AsyncMock()
    session.execute.return_value = MagicMock(rowcount=1)
    patient_id, device_id = uuid.uuid4(), uuid.uuid4()
    at = datetime(2026, 10, 7, 10, 2, tzinfo=timezone.utc)
    base = {"patient_id": patient_id, "device_id": device_id, "recorded_at": at, "quality": 1.0, "metadata_json": {}}
    with patch.object(PipelineService, "evaluate_patient", new_callable=AsyncMock):
        await HealthDataIngestService(session)._aggregate_samples_to_readings(
            [
                {**base, "metric": "steps", "value_num": 120},
                {**base, "metric": "daily_steps", "value_num": 5400},
                {**base, "metric": "heart_rate_variability_rmssd_ms", "value_num": 42.0},
                {**base, "metric": "respiratory_rate_bpm", "value_num": 15.0},
            ]
        )
    reading = session.execute.call_args_list[0].args[0].compile(dialect=postgresql.dialect()).params
    assert reading["steps_m0"] == 120
    assert reading["rmssd_m0"] == 42.0
    assert reading["rr_est_m0"] == 15.0

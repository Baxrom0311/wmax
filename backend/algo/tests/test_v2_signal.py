"""Unit tests for Architecture V2 clinical signal extensions:
- Medication damping context (Section 8.2)
- Auto critical SOS detection (Section 6.4)
"""
from datetime import datetime, timezone

from algo_interface import BaselineEntry, ReadingVec
from algo.signal import (
    MEDICATION_DAMPING,
    apply_medication_context,
    evaluate_alert,
    is_auto_critical_sos,
)


def test_medication_damping_lowers_zscore():
    zscores = {"hr_mean": -2.4, "spo2": 0.5, "skin_temp": 1.0}
    meds = [
        {
            "name": "Bisoprolol",
            "dose": "5mg",
            "stopped_at": None,
            "affects_params": {"hr_mean": "lowers"},
        }
    ]

    adjusted = apply_medication_context(zscores, meds)
    assert adjusted["hr_mean"] == -1.2
    assert adjusted["spo2"] == 0.5


def test_stopped_medication_does_not_damp():
    zscores = {"hr_mean": -2.4}
    meds = [
        {
            "name": "Bisoprolol",
            "dose": "5mg",
            "stopped_at": "2026-09-01",
            "affects_params": {"hr_mean": "lowers"},
        }
    ]

    adjusted = apply_medication_context(zscores, meds)
    assert adjusted["hr_mean"] == -2.4


def test_hard_override_never_damped_by_medication():
    # If SpO2 < 88, hard override triggers red immediately regardless of medications
    reading = ReadingVec(
        ts=datetime.now(timezone.utc),
        hr_mean=55.0,
        spo2=86.0,
        worn=True,
    )
    baselines = [
        BaselineEntry(param="spo2", time_window=1, median=97.0, mad=1.0, n_samples=100),
        BaselineEntry(param="hr_mean", time_window=1, median=65.0, mad=5.0, n_samples=100),
    ]
    meds = [{"name": "TestMed", "affects_params": {"spo2": "lowers"}}]

    res = evaluate_alert(
        reading=reading,
        baselines=baselines,
        recent_zscores=[],
        phase="full",
        medications=meds,
    )
    assert res.level == "red"
    assert res.reason == "critical_spo2"


def test_auto_critical_sos_detection():
    now = datetime.now(timezone.utc)
    critical_reading = ReadingVec(ts=now, hr_mean=50.0, spo2=83.0, worn=True)
    past_critical = [
        ReadingVec(ts=now, hr_mean=50.0, spo2=84.0, worn=True),
        ReadingVec(ts=now, hr_mean=50.0, spo2=82.0, worn=True),
    ]

    assert is_auto_critical_sos(critical_reading, past_critical) is True

    # Not sustained if only 1 reading
    assert is_auto_critical_sos(critical_reading, past_critical[:1]) is False

    # Not triggered if worn is False
    unworn = ReadingVec(ts=now, hr_mean=50.0, spo2=80.0, worn=False)
    assert is_auto_critical_sos(unworn, past_critical) is False

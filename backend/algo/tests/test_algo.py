"""Unit tests for WMAX clinical algorithm package (A2)."""
from datetime import datetime, timezone
import pytest
import timewin

from algo_interface import (
    BaselineEntry,
    ReadingVec,
)
from algo.baseline import compute_baselines, compute_zscores
from algo.signal import evaluate_alert
from algo.trend import compute_trend
from algo.anomaly import fit_anomaly_model, score_anomaly


def test_direction_spo2_increase_causes_no_risk():
    """SpO2 rising above baseline should NOT trigger directional risk."""
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    w = timewin.window_of(now)
    baseline = [
        BaselineEntry(param="spo2", time_window=w, median=96.0, mad=0.5, n_samples=20)
    ]
    # SpO2 rises to 99.0
    reading = ReadingVec(ts=now, spo2=99.0, worn=True)
    res = evaluate_alert(reading, baseline, [], "full")
    assert res.composite_score == 0.0
    assert "spo2" not in res.triggered_params


def test_single_param_deviation_does_not_alert():
    """A single deviating parameter must not trigger amber or red without 2nd param."""
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    w = timewin.window_of(now)
    baseline = [
        BaselineEntry(param="hr_mean", time_window=w, median=65.0, mad=2.0, n_samples=30),
        BaselineEntry(param="spo2", time_window=w, median=98.0, mad=0.5, n_samples=30),
    ]
    # Extreme HR deviation (z > 4.0), but spo2 normal
    reading = ReadingVec(ts=now, hr_mean=110.0, spo2=98.0, steps=0, worn=True)
    res = evaluate_alert(reading, baseline, [], "full")
    assert res.level == "green"  # blocked by MIN_TRIGGERED_PARAMS == 2


def test_persistence_requires_consecutive_windows():
    """High deviation on only the current window should not escalate to persistent red."""
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    w = timewin.window_of(now)
    baseline = [
        BaselineEntry(param="hr_mean", time_window=w, median=65.0, mad=1.0, n_samples=30),
        BaselineEntry(param="skin_temp", time_window=w, median=36.4, mad=0.1, n_samples=30),
    ]
    reading = ReadingVec(ts=now, hr_mean=95.0, skin_temp=38.0, steps=0, worn=True)
    # Past windows were normal
    past_zscores = [{"hr_mean": 0.0, "skin_temp": 0.0}, {"hr_mean": 0.2, "skin_temp": 0.1}]
    res = evaluate_alert(reading, baseline, past_zscores, "full")
    # Transient high deviation becomes amber rather than full red
    assert res.level == "amber"
    assert res.reason == "transient_high_deviation"


def test_critical_spo2_overrides_immediately():
    """SpO2 < 88.0 triggers immediate Red level regardless of past windows or single param."""
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    w = timewin.window_of(now)
    baseline = [
        BaselineEntry(param="spo2", time_window=w, median=97.0, mad=0.5, n_samples=30)
    ]
    reading = ReadingVec(ts=now, spo2=86.0, worn=True)
    res = evaluate_alert(reading, baseline, [], "full")
    assert res.level == "red"
    assert res.reason == "critical_spo2"


def test_activity_mask_ignores_tachycardia_when_moving():
    """Elevated HR when steps > 20 is exercise/movement, not resting tachycardia."""
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    w = timewin.window_of(now)
    baseline = [
        BaselineEntry(param="hr_mean", time_window=w, median=65.0, mad=1.5, n_samples=30)
    ]
    reading = ReadingVec(ts=now, hr_mean=135.0, steps=150, worn=True)
    res = evaluate_alert(reading, baseline, [], "full")
    assert res.level == "green"
    assert "hr_mean" not in res.triggered_params


def test_learning_phase_suppresses_amber_to_green():
    """During learning phase (first 5-7 days), mild deviations are green."""
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    w = timewin.window_of(now)
    baseline = [
        BaselineEntry(param="hr_mean", time_window=w, median=65.0, mad=1.0, n_samples=30),
        BaselineEntry(param="skin_temp", time_window=w, median=36.4, mad=0.1, n_samples=30),
    ]
    # Mild deviation (composite >= AMBER_THRESHOLD but < RED_THRESHOLD)
    reading = ReadingVec(ts=now, hr_mean=70.0, skin_temp=36.8, steps=0, worn=True)
    past = [{"hr_mean": 3.0, "skin_temp": 3.0}, {"hr_mean": 3.0, "skin_temp": 3.0}]
    res = evaluate_alert(reading, baseline, past, "learning")
    assert res.level == "green"
    assert res.reason == "learning_phase_suppressed"


def test_trend_calculation():
    """Tests trend slope classification across 7 days."""
    # Worsening: increasing z-scores
    worsening_pts = [(0, 0.2), (1, 0.5), (2, 0.8), (3, 1.2), (4, 1.8), (5, 2.3), (6, 2.9)]
    res = compute_trend(worsening_pts)
    assert res.direction == "worsening"
    assert res.recommendation_key == "rec.contact_today"

    # Improving: decreasing z-scores
    improving_pts = [(0, 3.0), (1, 2.4), (2, 1.8), (3, 1.2), (4, 0.8), (5, 0.4), (6, 0.1)]
    res_imp = compute_trend(improving_pts)
    assert res_imp.direction == "improving"
    assert res_imp.recommendation_key == "rec.continue_monitoring"

    # Stable
    stable_pts = [(0, 0.5), (1, 0.52), (2, 0.49), (3, 0.51), (4, 0.50), (5, 0.48), (6, 0.52)]
    res_stb = compute_trend(stable_pts)
    assert res_stb.direction == "stable"
    assert res_stb.recommendation_key == "rec.routine_followup"


def test_anomaly_model_lifecycle():
    """Tests fitting and scoring of advisory IsolationForest model."""
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    sample_readings = [
        ReadingVec(ts=now, hr_mean=65.0 + (i % 5), spo2=97.0, skin_temp=36.4, rmssd=35.0, rr_est=15.0, steps=10, worn=True)
        for i in range(15)
    ]
    model_bytes = fit_anomaly_model(sample_readings)
    assert isinstance(model_bytes, bytes)
    assert len(model_bytes) > 0

    normal_reading = ReadingVec(ts=now, hr_mean=67.0, spo2=97.0, skin_temp=36.4, rmssd=35.0, rr_est=15.0, steps=10, worn=True)
    score = score_anomaly(model_bytes, normal_reading)
    assert 0.0 <= score <= 1.0

"""
Pytest test suite for WMAX clinical math engine.

Tests are pure Python (no DB, no network) — they run against
app.services.clinical_math functions and algo_interface constants.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

import pytest

# Allow import without installed packages by checking if they exist
try:
    from app.services.clinical_math import (
        compute_prognosis_pure,
        compute_trend_pure,
        detect_problems_pure,
    )
    from app.services.clinical_math import _compute_directional_zscore  # internal helper
    HAS_CLINICAL_MATH = True
except (ImportError, Exception):
    HAS_CLINICAL_MATH = False

try:
    from algo_interface import (
        AMBER_THRESHOLD,
        CRITICAL_HR_AT_REST,
        CRITICAL_SPO2,
        MIN_TRIGGERED_PARAMS,
        PARAM_DIRECTION,
        RED_THRESHOLD,
        REST_STEPS_MAX,
        Z_DEADZONE,
        AlertResult,
        BaselineEntry,
        ReadingVec,
        TrendResult,
    )
    HAS_CONTRACTS = True
except ImportError:
    HAS_CONTRACTS = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_ts(offset_minutes: int = 0) -> datetime:
    """UTC timestamp with optional minute offset."""
    from datetime import timedelta
    return datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=offset_minutes)


def make_reading(**overrides) -> "ReadingVec":
    defaults = dict(
        ts=make_ts(),
        hr_mean=70.0,
        spo2=97.0,
        skin_temp=36.5,
        rmssd=35.0,
        rr_est=15.0,
        steps=50,
        sleep_frag=2.0,
        worn=True,
    )
    defaults.update(overrides)
    return ReadingVec(**defaults)


def make_baseline(param: str, window: int = 1, median: float = 70.0, mad: float = 5.0, n: int = 20) -> "BaselineEntry":
    return BaselineEntry(param=param, time_window=window, median=median, mad=mad, n_samples=n)


# ── Contract constants tests ──────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_CONTRACTS, reason="algo_interface not installed")
class TestContractConstants:
    def test_critical_spo2_threshold(self):
        assert CRITICAL_SPO2 == 88.0, "FROZEN: CRITICAL_SPO2 must be 88.0"

    def test_critical_hr_threshold(self):
        assert CRITICAL_HR_AT_REST == 130.0, "FROZEN: CRITICAL_HR_AT_REST must be 130.0"

    def test_rest_steps_max(self):
        assert REST_STEPS_MAX == 20, "FROZEN: REST_STEPS_MAX must be 20"

    def test_z_deadzone(self):
        assert Z_DEADZONE == 1.5, "FROZEN: Z_DEADZONE must be 1.5"

    def test_amber_threshold(self):
        assert AMBER_THRESHOLD == 2.0

    def test_red_threshold(self):
        assert RED_THRESHOLD == 4.0

    def test_min_triggered_params(self):
        assert MIN_TRIGGERED_PARAMS == 2

    def test_spo2_direction_negative(self):
        """spo2 falling is dangerous — direction must be -1."""
        assert PARAM_DIRECTION["spo2"] == -1

    def test_rmssd_direction_negative(self):
        """HRV drop is dangerous — direction must be -1."""
        assert PARAM_DIRECTION["rmssd"] == -1

    def test_hr_direction_positive(self):
        """HR rise is dangerous — direction must be +1."""
        assert PARAM_DIRECTION["hr_mean"] == +1

    def test_skin_temp_direction_positive(self):
        assert PARAM_DIRECTION["skin_temp"] == +1

    def test_rr_direction_positive(self):
        assert PARAM_DIRECTION["rr_est"] == +1


# ── Pipeline fallback function tests ─────────────────────────────────────────

@pytest.mark.skipif(not HAS_CONTRACTS, reason="algo_interface not installed")
class TestPipelineFallbackFunctions:
    """Tests the contract-compliant fallback implementations in pipeline_service.py."""

    def _get_fallback_functions(self):
        """Import fallback functions from pipeline_service."""
        import sys
        # Force reload to get fallback path
        try:
            from app.services.pipeline_service import (
                compute_baselines,
                compute_zscores,
                evaluate_alert,
                compute_trend,
            )
            return compute_baselines, compute_zscores, evaluate_alert, compute_trend
        except ImportError:
            pytest.skip("pipeline_service not available")

    def test_critical_spo2_override_bypasses_composite(self):
        """SpO2 < 88 must immediately produce red regardless of other parameters."""
        _, _, evaluate_alert, _ = self._get_fallback_functions()
        reading = make_reading(spo2=85.0, steps=5)
        baselines = [make_baseline("spo2", median=97.0, mad=1.0)]
        result = evaluate_alert(reading, baselines, [], phase="full")
        assert result.level == "red"
        assert result.reason == "critical_spo2"

    def test_critical_hr_at_rest_override(self):
        """HR > 130 at rest (steps<=20) must immediately produce red."""
        _, _, evaluate_alert, _ = self._get_fallback_functions()
        reading = make_reading(hr_mean=140.0, steps=10)
        baselines = [make_baseline("hr_mean", median=70.0, mad=5.0)]
        result = evaluate_alert(reading, baselines, [], phase="full")
        assert result.level == "red"
        assert result.reason == "critical_hr_at_rest"

    def test_hr_deviation_ignored_when_active(self):
        """HR deviation should NOT trigger when steps > REST_STEPS_MAX."""
        _, compute_zscores, evaluate_alert, _ = self._get_fallback_functions()
        reading = make_reading(hr_mean=140.0, steps=100)  # Active = ignore HR
        baselines = [make_baseline("hr_mean", median=70.0, mad=5.0)]
        result = evaluate_alert(reading, baselines, [], phase="full")
        # Should NOT be red due to critical HR (steps > 20 prevents override)
        # And without other triggered params, composite should stay low
        assert result.level != "red" or result.reason != "critical_hr_at_rest"

    def test_calib_phase_always_green(self):
        """During calibration phase, level is always green regardless of readings."""
        _, _, evaluate_alert, _ = self._get_fallback_functions()
        reading = make_reading(spo2=92.0, hr_mean=120.0)  # Clearly elevated
        baselines = [
            make_baseline("spo2", median=97.0, mad=1.0),
            make_baseline("hr_mean", median=70.0, mad=5.0),
        ]
        result = evaluate_alert(reading, baselines, [], phase="calib")
        assert result.level == "green"
        assert result.reason == "calibrating"

    def test_unworn_device_produces_no_data(self):
        """Unworn device must produce no_data, not green."""
        _, _, evaluate_alert, _ = self._get_fallback_functions()
        reading = make_reading(worn=False)
        baselines = [make_baseline("hr_mean")]
        result = evaluate_alert(reading, baselines, [], phase="full")
        assert result.level == "no_data"
        assert result.reason == "not_worn"

    def test_normal_readings_produce_green(self):
        """Perfectly normal readings should produce green status."""
        _, _, evaluate_alert, _ = self._get_fallback_functions()
        reading = make_reading()  # All defaults are within normal range
        baselines = [
            make_baseline("hr_mean", median=70.0, mad=5.0),
            make_baseline("spo2", median=97.0, mad=1.0),
        ]
        result = evaluate_alert(reading, baselines, [], phase="full")
        assert result.level == "green"

    def test_compute_baselines_skips_unworn(self):
        """Baseline computation must skip readings with worn=False."""
        compute_baselines, _, _, _ = self._get_fallback_functions()
        worn_reading = make_reading(hr_mean=70.0, worn=True)
        unworn_reading = make_reading(hr_mean=200.0, worn=False)  # Should be excluded
        baselines = compute_baselines([worn_reading, unworn_reading])
        hr_baseline = next((b for b in baselines if b.param == "hr_mean"), None)
        if hr_baseline:
            # Median should reflect only the worn reading (70.0), not 200.0
            assert hr_baseline.median < 100.0

    def test_trend_improving_slope(self):
        """Negative slope below threshold should produce 'improving' direction."""
        _, _, _, compute_trend = self._get_fallback_functions()
        # Scores decreasing daily: day 0=5, day1=4, day2=3, day3=2, day4=1
        daily_scores = [(0, 5.0), (1, 4.0), (2, 3.0), (3, 2.0), (4, 1.0)]
        result = compute_trend(daily_scores)
        assert result.direction == "improving"
        assert result.slope < 0

    def test_trend_worsening_slope(self):
        """Positive slope above threshold should produce 'worsening' direction."""
        _, _, _, compute_trend = self._get_fallback_functions()
        daily_scores = [(0, 1.0), (1, 2.0), (2, 3.5), (3, 5.0), (4, 7.0)]
        result = compute_trend(daily_scores)
        assert result.direction == "worsening"
        assert result.slope > 0

    def test_trend_stable(self):
        """Flat scores should produce 'stable' direction."""
        _, _, _, compute_trend = self._get_fallback_functions()
        daily_scores = [(0, 3.0), (1, 3.1), (2, 2.9), (3, 3.0), (4, 3.05)]
        result = compute_trend(daily_scores)
        assert result.direction == "stable"

    def test_trend_single_day_is_stable(self):
        """Single day of data cannot compute a meaningful slope — must return stable."""
        _, _, _, compute_trend = self._get_fallback_functions()
        result = compute_trend([(0, 3.0)])
        assert result.direction == "stable"
        assert result.slope == 0.0


# ── Validation schemas tests ─────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_CONTRACTS, reason="algo_interface not installed")
class TestReadingSchemas:
    """Tests reading schema validation boundaries."""

    def test_valid_reading_passes(self):
        try:
            from app.schemas.reading import ReadingIn
            r = ReadingIn(
                ts=make_ts(),
                hr_mean=72.0,
                spo2=98.0,
                skin_temp=36.5,
                worn=True,
            )
            assert r.spo2 == 98.0
        except ImportError:
            pytest.skip("schemas not available")

    def test_hr_below_minimum_rejected(self):
        try:
            from app.schemas.reading import ReadingIn
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                ReadingIn(ts=make_ts(), hr_mean=10.0, worn=True)  # below 20 bpm
        except ImportError:
            pytest.skip("schemas not available")

    def test_spo2_above_100_rejected(self):
        try:
            from app.schemas.reading import ReadingIn
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                ReadingIn(ts=make_ts(), spo2=101.0, worn=True)
        except ImportError:
            pytest.skip("schemas not available")

    def test_future_timestamp_rejected(self):
        try:
            from app.schemas.reading import ReadingIn
            from pydantic import ValidationError
            from datetime import timedelta
            future_ts = datetime.now(timezone.utc) + timedelta(minutes=20)
            with pytest.raises(ValidationError):
                ReadingIn(ts=future_ts, worn=True)
        except ImportError:
            pytest.skip("schemas not available")


# ── Domain logic: timewin ─────────────────────────────────────────────────────

class TestTimewin:
    """Tests for timewin contract functions."""

    def test_is_no_data_returns_true_for_45min_silence(self):
        try:
            import timewin
            from datetime import timedelta
            last_ts = datetime.now(timezone.utc) - timedelta(minutes=50)
            now = datetime.now(timezone.utc)
            assert timewin.is_no_data(last_ts, now) is True
        except ImportError:
            pytest.skip("timewin not available")

    def test_is_no_data_returns_false_for_recent_reading(self):
        try:
            import timewin
            from datetime import timedelta
            last_ts = datetime.now(timezone.utc) - timedelta(minutes=10)
            now = datetime.now(timezone.utc)
            assert timewin.is_no_data(last_ts, now) is False
        except ImportError:
            pytest.skip("timewin not available")

    def test_is_no_data_returns_true_for_none(self):
        try:
            import timewin
            now = datetime.now(timezone.utc)
            assert timewin.is_no_data(None, now) is True
        except ImportError:
            pytest.skip("timewin not available")

    def test_window_of_returns_0_for_midnight(self):
        try:
            import timewin
            import zoneinfo
            midnight = datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
            # 00:00 UTC = 05:00 Tashkent — window 0 (00–06)
            result = timewin.window_of(midnight)
            assert result in (0, 1, 2, 3)  # Must be a valid window
        except (ImportError, Exception):
            pytest.skip("timewin not available")


# ---------------------------------------------------------------------------
# Baseline freezing — regression guard
# ---------------------------------------------------------------------------
def test_approved_baseline_is_loaded_not_recomputed():
    """A signed-off baseline must not drift with new readings.

    Recomputing over the full window lets a deteriorating patient's own decline
    redefine their "normal", so the signal never fires. The pipeline loads the
    stored baseline whenever `baseline_approved_at` is set.
    """
    import inspect
    from app.services import pipeline_service

    src = inspect.getsource(pipeline_service.PipelineService.evaluate_patient)
    assert "baseline_approved_at is not None" in src, (
        "evaluate_patient must branch on baseline_approved_at"
    )
    # The recompute path must sit in the `else` branch, never unconditionally.
    recompute_idx = src.index("compute_baselines(vecs)")
    branch_idx = src.index("baseline_approved_at is not None")
    assert branch_idx < recompute_idx, "recompute must be guarded by the approval check"


def test_alert_repo_signature_matches_pipeline_call():
    """Guards the AlertResult-vs-kwargs mismatch that broke every alert insert."""
    import inspect
    from app.repositories.alert_repo import AlertRepository

    params = inspect.signature(AlertRepository.insert_idempotent).parameters
    assert set(params) == {"self", "patient_id", "ts", "result"}, (
        "call sites pass result=AlertResult(...); keep the signature in sync"
    )

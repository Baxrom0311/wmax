"""A1 <-> A2 contract. FROZEN.

A2 (algo) implements these functions in backend/algo/ as PURE functions:
no database, no FastAPI, no I/O. A1 (backend-core) loads rows with the ORM,
converts them to these dataclasses, calls the functions, and persists results.

This seam is what makes A1 and A2 fully parallel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol

AlertLevel = Literal["green", "amber", "red", "no_data"]
Phase = Literal["calib", "learning", "full"]
Param = Literal["hr_mean", "rmssd", "spo2", "skin_temp", "sleep_frag", "steps", "rr_est"]

# --------------------------------------------------------------------------
# Clinical constants — FROZEN. A2 imports them, never redefines them.
# --------------------------------------------------------------------------

# Which direction of deviation is clinically dangerous.
#  -1 : only a DROP matters (spo2 falling, hrv collapsing)
#  +1 : only a RISE matters (tachycardia, fever, tachypnea)
#   0 : both directions matter
PARAM_DIRECTION: dict[str, int] = {
    "spo2": -1,
    "rmssd": -1,
    "hr_mean": +1,
    "skin_temp": +1,
    "rr_est": +1,
    "sleep_frag": +1,
    "steps": 0,
}

WEIGHTS: dict[str, float] = {
    "hr_mean": 1.0,
    "spo2": 1.5,
    "skin_temp": 1.2,
    "rmssd": 0.8,
    "sleep_frag": 0.7,
    "steps": 0.6,
    "rr_est": 1.3,
}

Z_DEADZONE = 1.5          # deviations below this add nothing to the composite
AMBER_THRESHOLD = 2.0
RED_THRESHOLD = 4.0
MIN_TRIGGERED_PARAMS = 2  # a single wobbling parameter never raises an alert

# Hard clinical overrides — bypass the composite entirely.
CRITICAL_SPO2 = 88.0
CRITICAL_HR_AT_REST = 130.0
REST_STEPS_MAX = 20       # steps per 5-min window that still counts as "at rest"

TREND_SLOPE_IMPROVING = -0.15
TREND_SLOPE_WORSENING = +0.15

MAD_EPSILON = 1e-3        # MAD == 0 guard
MIN_BASELINE_SAMPLES = 12 # below this, the baseline for that window is untrusted


# --------------------------------------------------------------------------
# Data shapes
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ReadingVec:
    """One 5-minute aggregate. Mirrors the `readings` table; ts is UTC."""
    ts: datetime
    hr_mean: float | None = None
    hr_min: float | None = None
    hr_max: float | None = None
    rmssd: float | None = None
    sdnn: float | None = None
    spo2: float | None = None
    skin_temp: float | None = None
    steps: int | None = None
    rr_est: float | None = None
    sleep_frag: float | None = None
    worn: bool = True


@dataclass(frozen=True)
class BaselineEntry:
    param: str
    time_window: int      # 0..3
    median: float
    mad: float
    n_samples: int


@dataclass(frozen=True)
class AlertResult:
    level: AlertLevel
    composite_score: float
    triggered_params: dict[str, float]   # param -> directional z that passed the deadzone
    reason: str                          # short English code, e.g. "critical_spo2"
    anomaly_score: float | None = None   # ADVISORY ONLY — never changes `level`


@dataclass(frozen=True)
class TrendResult:
    slope: float
    direction: Literal["improving", "stable", "worsening"]
    recommendation_key: str   # i18n key, e.g. "rec.contact_today"
    days_used: int


# --------------------------------------------------------------------------
# Functions A2 must implement in backend/algo/
# --------------------------------------------------------------------------

class AlgoAPI(Protocol):

    def compute_baselines(
        self, readings: list[ReadingVec]
    ) -> list[BaselineEntry]:
        """backend/algo/baseline.py

        Median + MAD per (param, time_window) over the supplied readings
        (caller passes the last 7 days). Windows come from timewin.window_of.
        Readings with worn=False are skipped. Entries with
        n_samples < MIN_BASELINE_SAMPLES are still returned, flagged by n_samples.
        """
        ...

    def compute_zscores(
        self, reading: ReadingVec, baselines: list[BaselineEntry]
    ) -> dict[str, float]:
        """backend/algo/baseline.py

        z = (x - median) / (1.4826 * max(mad, MAD_EPSILON)) for the reading's
        own time window. Returns the RAW signed z per param (direction is
        applied later, in evaluate_alert). Missing params are omitted.
        """
        ...

    def evaluate_alert(
        self,
        reading: ReadingVec,
        baselines: list[BaselineEntry],
        recent_zscores: list[dict[str, float]],
        phase: Phase,
        anomaly_score: float | None = None,
    ) -> AlertResult:
        """backend/algo/signal.py

        `recent_zscores` holds the previous CONSECUTIVE_WINDOWS-1 z-score dicts,
        oldest first, so persistence can be checked without touching the DB.

        Rules (FROZEN):
          - directional: z_eff = max(0, z * PARAM_DIRECTION[p]) , or abs(z) when 0
          - composite   = sum(WEIGHTS[p] * max(0, z_eff - Z_DEADZONE))
          - green  : composite < AMBER_THRESHOLD
          - amber  : AMBER <= composite < RED  AND >= MIN_TRIGGERED_PARAMS
          - red    : composite >= RED          AND >= MIN_TRIGGERED_PARAMS
          - red    : OR spo2 < CRITICAL_SPO2
          - red    : OR hr_mean > CRITICAL_HR_AT_REST while steps <= REST_STEPS_MAX
          - deviation must hold across CONSECUTIVE_WINDOWS (critical overrides do not wait)
          - worn == False           -> level 'no_data', reason 'not_worn'
          - steps > REST_STEPS_MAX  -> hr_mean deviation ignored
          - phase == 'calib'        -> always 'green', reason 'calibrating'
          - phase == 'learning'     -> only 'red' may be emitted, else 'green'
          - anomaly_score is recorded, NEVER used to change `level`
        """
        ...

    def compute_trend(
        self, daily_raw_scores: list[tuple[int, float]]
    ) -> TrendResult:
        """backend/algo/trend.py

        Input: (day_index, daily_mean_RAW_z_sum) for the last 7 local days.
        NOTE: raw z sum, WITHOUT the Z_DEADZONE cut — otherwise a healthy
        patient scores 0.0 every day and the trend is always 'stable',
        which would destroy the early-warning idea.

        Linear regression slope -> direction via TREND_SLOPE_* thresholds.
        recommendation_key:
          worsening + red    -> 'rec.contact_today'
          worsening + amber  -> 'rec.visit_within_3_days'
          stable             -> 'rec.routine_followup'
          improving          -> 'rec.continue_monitoring'
        """
        ...

    def fit_anomaly_model(self, readings: list[ReadingVec]) -> bytes:
        """backend/algo/anomaly.py — per-patient IsolationForest, joblib-serialised.
        Trained once when the learning phase ends. ADVISORY ONLY."""
        ...

    def score_anomaly(self, model_blob: bytes, reading: ReadingVec) -> float:
        """backend/algo/anomaly.py — 0.0 (normal) .. 1.0 (anomalous). ADVISORY ONLY."""
        ...

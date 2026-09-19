"""Baseline model calculation and z-score computation.

Implements AlgoAPI baseline functions as pure functions:
- compute_baselines: Median + MAD per (param, time_window)
- compute_zscores: Raw signed z-score per param
"""
from __future__ import annotations

import statistics

import timewin
from algo_interface import (
    MAD_EPSILON,
    BaselineEntry,
    ReadingVec,
)

MONITORED_PARAMS = ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]


def compute_baselines(readings: list[ReadingVec]) -> list[BaselineEntry]:
    """Calculates median and MAD per (param, time_window) across supplied readings.

    Windows come from timewin.window_of (0..3).
    Readings with worn=False are skipped.
    """
    entries: list[BaselineEntry] = []

    for param in MONITORED_PARAMS:
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


def compute_zscores(
    reading: ReadingVec, baselines: list[BaselineEntry]
) -> dict[str, float]:
    """Calculates raw signed z-scores for the reading's own local time window.

    z = (x - median) / (1.4826 * max(mad, MAD_EPSILON))
    Directional adjustment is NOT applied here; it is applied in evaluate_alert.
    """
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

"""Clinical trend evaluation engine.

Implements AlgoAPI trend calculation:
- compute_trend: Linear regression slope over daily raw z-score sums.
"""
from __future__ import annotations

from algo_interface import (
    TREND_SLOPE_IMPROVING,
    TREND_SLOPE_WORSENING,
    TrendResult,
)


def compute_trend(daily_raw_scores: list[tuple[int, float]]) -> TrendResult:
    """Computes linear regression slope over daily raw scores (up to 7 local days).

    daily_raw_scores: list of (day_index, daily_mean_raw_z_sum)
    """
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
        direction=direction,  # type: ignore[arg-type]
        recommendation_key=rec,
        days_used=n,
    )

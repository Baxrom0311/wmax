"""WMAX Algorithm Module (A2).

Pure mathematical and clinical signal functions implementing AlgoAPI:
- baseline: compute_baselines, compute_zscores
- signal: evaluate_alert
- trend: compute_trend
- anomaly: fit_anomaly_model, score_anomaly
"""
from __future__ import annotations

from .anomaly import fit_anomaly_model, score_anomaly
from .baseline import compute_baselines, compute_zscores
from .signal import evaluate_alert
from .trend import compute_trend

__all__ = [
    "compute_baselines",
    "compute_zscores",
    "evaluate_alert",
    "compute_trend",
    "fit_anomaly_model",
    "score_anomaly",
]

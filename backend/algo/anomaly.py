"""IsolationForest anomaly scoring (ADVISORY ONLY).

Trained per-patient once when learning phase finishes.
Results are recorded in AlertResult.anomaly_score (0.0 normal .. 1.0 anomalous)
and NEVER affect the clinical AlertLevel (domain decision: advisory only).
"""
from __future__ import annotations

import io
from typing import Any

from algo_interface import ReadingVec

FEATURE_NAMES = ["hr_mean", "spo2", "skin_temp", "rmssd", "rr_est", "steps", "sleep_frag"]


def _extract_features(reading: ReadingVec) -> list[float]:
    """Extracts normalized numerical features with clinical defaults for missing readings."""
    defaults = {
        "hr_mean": 70.0,
        "spo2": 97.0,
        "skin_temp": 36.4,
        "rmssd": 35.0,
        "rr_est": 16.0,
        "steps": 0.0,
        "sleep_frag": 0.0,
    }
    feats: list[float] = []
    for f in FEATURE_NAMES:
        val = getattr(reading, f, None)
        feats.append(float(val) if val is not None else defaults[f])
    return feats


def fit_anomaly_model(readings: list[ReadingVec]) -> bytes:
    """Fits an IsolationForest model on worn readings and serializes it with joblib."""
    worn_readings = [r for r in readings if r.worn]
    if len(worn_readings) < 10:
        return b""

    try:
        from sklearn.ensemble import IsolationForest
        import joblib

        x = [_extract_features(r) for r in worn_readings]
        model = IsolationForest(n_estimators=50, random_state=42, contamination=0.05)
        model.fit(x)

        buf = io.BytesIO()
        joblib.dump(model, buf)
        return buf.getvalue()
    except Exception:
        return b""


def score_anomaly(model_blob: bytes, reading: ReadingVec) -> float:
    """Calculates 0.0 (normal) .. 1.0 (anomalous) anomaly score using the serialized model."""
    if not model_blob:
        return 0.0

    try:
        import joblib

        buf = io.BytesIO(model_blob)
        model = joblib.load(buf)
        feats = [_extract_features(reading)]
        # decision_function returns negative values for anomalies
        raw_score = float(model.decision_function(feats)[0])
        # Map roughly from [-0.5, +0.5] to [1.0, 0.0]
        normalized = max(0.0, min(1.0, 0.5 - raw_score))
        return round(normalized, 2)
    except Exception:
        return 0.0

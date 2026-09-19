"""Prometheus metrics exposed on /metrics.

Metric names here are fixed by the existing dashboards and alert rules:
`monitoring/grafana/dashboards/wmax-enterprise.json` and
`monitoring/prometheus/alerts.yml` query them by name. Renaming one silently
blanks a panel, so change both sides together.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("wmax.metrics")

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without the dependency
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _NoOpMetric:
        """Stand-in so call sites need no availability checks."""

        def labels(self, *_args, **_kwargs) -> "_NoOpMetric":
            return self

        def inc(self, *_args, **_kwargs) -> None:
            return None

        def observe(self, *_args, **_kwargs) -> None:
            return None

        def set(self, *_args, **_kwargs) -> None:
            return None

    Counter = Gauge = Histogram = lambda *a, **k: _NoOpMetric()  # type: ignore[assignment]

    def generate_latest() -> bytes:  # type: ignore[misc]
        return b"# prometheus_client not installed\napp_up 1\n"


# ── HTTP ─────────────────────────────────────────────────────────────────────
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 2.5, 5.0, 10.0),
)

# ── AI provider (Gemini, DeepSeek, …) ────────────────────────────────────────
# Labelled by provider so switching the backing LLM does not blank the panels.
ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "LLM API call latency in seconds",
    ["provider"],
    buckets=(0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 30.0),
)
ai_tokens_total = Counter(
    "ai_tokens_total",
    "Approximate LLM tokens consumed",
    ["provider", "direction"],
)
ai_circuit_breaker_state = Gauge(
    "ai_circuit_breaker_state",
    "Circuit breaker state per provider: 0=closed (normal), 1=open (tripped)",
    ["provider"],
)

# ── Clinical domain ──────────────────────────────────────────────────────────
alerts_total = Counter(
    "wmax_alerts_total",
    "Clinical alerts raised, by level",
    ["level"],
)
notifications_total = Counter(
    "wmax_notifications_total",
    "Outbound notifications, by channel and outcome",
    ["channel", "outcome"],
)
readings_ingested_total = Counter(
    "wmax_readings_ingested_total",
    "Physiological readings accepted by the ingest endpoint",
)


def render_metrics() -> tuple[bytes, str]:
    """Returns (body, content_type) for the Prometheus exposition endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST

"""Resilient Google Gemini AI Integration Service for NAZORAT.

Features:
- Configurable timeout
- Exponential backoff with jitter retry
- Circuit breaker pattern (CLOSED -> OPEN -> HALF_OPEN)
- Token bucket rate limiting
- Request latency and token usage metrics (Prometheus)
- Rule-based clinical heuristic fallback architecture
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger("nazorat.gemini")

# Metrics placeholder or prometheus_client integration
try:
    from prometheus_client import Counter, Gauge, Histogram

    GEMINI_REQUESTS = Counter(
        "gemini_requests_total",
        "Total requests to Google Gemini AI API",
        ["status"],
    )
    GEMINI_LATENCY = Histogram(
        "gemini_request_duration_seconds",
        "Gemini request duration in seconds",
        buckets=[0.2, 0.5, 1.0, 2.0, 4.0, 8.0, 15.0],
    )
    GEMINI_TOKENS = Counter(
        "gemini_tokens_total",
        "Estimated tokens consumed by Gemini",
    )
    GEMINI_CB_STATE = Gauge(
        "gemini_circuit_breaker_state",
        "Circuit breaker state: 0=Closed (Normal), 1=Open (Tripped)",
    )
except ImportError:
    GEMINI_REQUESTS = None  # type: ignore
    GEMINI_LATENCY = None  # type: ignore
    GEMINI_TOKENS = None  # type: ignore
    GEMINI_CB_STATE = None  # type: ignore


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenException(Exception):
    """Raised when the circuit breaker is open and fast-failing."""


class GeminiService:
    """Production-grade resilient client for Google Gemini API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
        timeout_seconds: float = 12.0,
        max_retries: int = 3,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.timeout = timeout_seconds
        self.max_retries = max_retries

        # Circuit Breaker state
        self.state = CircuitBreakerState.CLOSED
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.failure_count = 0
        self.last_state_change = time.time()

        # Rate Limiting (Token Bucket: 60 rpm)
        self.rate_limit_tokens = 60.0
        self.rate_limit_capacity = 60.0
        self.rate_limit_refill_rate = 1.0  # 1 token per second
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    def _acquire_rate_limit(self) -> bool:
        """Simple in-memory token bucket rate limiter."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.rate_limit_tokens = min(
            self.rate_limit_capacity,
            self.rate_limit_tokens + elapsed * self.rate_limit_refill_rate,
        )

        if self.rate_limit_tokens >= 1.0:
            self.rate_limit_tokens -= 1.0
            return True
        return False

    def _check_circuit_breaker(self) -> None:
        """Evaluates circuit breaker state."""
        now = time.time()
        if self.state == CircuitBreakerState.OPEN:
            if now - self.last_state_change > self.recovery_timeout:
                logger.info("Gemini Circuit Breaker transition: OPEN -> HALF_OPEN")
                self.state = CircuitBreakerState.HALF_OPEN
                self.last_state_change = now
                if GEMINI_CB_STATE:
                    GEMINI_CB_STATE.set(0)
            else:
                raise CircuitBreakerOpenException("Gemini Circuit Breaker is OPEN.")

    def _record_success(self) -> None:
        if self.state in (CircuitBreakerState.HALF_OPEN, CircuitBreakerState.OPEN):
            logger.info("Gemini Circuit Breaker recovered: -> CLOSED")
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_state_change = time.time()
            if GEMINI_CB_STATE:
                GEMINI_CB_STATE.set(0)

    def _record_failure(self) -> None:
        self.failure_count += 1
        logger.warning(
            "Gemini failure recorded (%s/%s)",
            self.failure_count,
            self.failure_threshold,
        )
        if self.failure_count >= self.failure_threshold:
            logger.error("Gemini Circuit Breaker TRIP -> OPEN")
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = time.time()
            if GEMINI_CB_STATE:
                GEMINI_CB_STATE.set(1)

    async def generate_clinical_summary(
        self,
        patient_name: str,
        vital_signs: dict[str, Any],
        alert_level: str,
    ) -> dict[str, Any]:
        """Generates AI clinical explanation with automatic heuristic fallback."""
        # 1. Fallback if no API key configured
        if not self.api_key or self.api_key.startswith("change_me"):
            logger.info("No Gemini API key provided. Executing deterministic fallback.")
            return self._heuristic_fallback(patient_name, vital_signs, alert_level)

        # 2. Check Circuit Breaker & Rate Limiter
        try:
            self._check_circuit_breaker()
        except CircuitBreakerOpenException:
            logger.warning("Gemini circuit breaker open. Switching to heuristic fallback.")
            return self._heuristic_fallback(patient_name, vital_signs, alert_level)

        if not self._acquire_rate_limit():
            logger.warning("Gemini rate limit exceeded locally. Switching to fallback.")
            return self._heuristic_fallback(patient_name, vital_signs, alert_level)

        # 3. Call Gemini REST API with Exponential Backoff Retry
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        prompt = (
            f"Bemor: {patient_name}. Holat darajasi: {alert_level}. "
            f"So'nggi o'lchovlar: {vital_signs}. "
            f"Shifokor uchun 2 gapdan iborat qisqa klinik xulosa va tavsiya ber (o'zbek tilida)."
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200},
        }

        start_time = time.time()
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)

                    if resp.status_code == 200:
                        duration = time.time() - start_time
                        if GEMINI_LATENCY:
                            GEMINI_LATENCY.observe(duration)
                        if GEMINI_REQUESTS:
                            GEMINI_REQUESTS.labels(status="success").inc()

                        data = resp.json()
                        text = (
                            data.get("candidates", [{}])[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        token_count = len(text.split()) * 2  # rough token approximation
                        if GEMINI_TOKENS:
                            GEMINI_TOKENS.inc(token_count)

                        self._record_success()
                        return {
                            "source": "gemini_ai",
                            "model": self.model,
                            "summary": text.strip(),
                            "latency_sec": round(duration, 3),
                        }

                    logger.warning(
                        "Gemini API returned status %s on attempt %s: %s",
                        resp.status_code,
                        attempt,
                        resp.text[:200],
                    )

            except Exception as err:
                logger.warning("Gemini request exception on attempt %s: %s", attempt, err)

            # Exponential backoff with jitter
            backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
            await asyncio.sleep(backoff)

        # 4. If all retries failed, record failure and trigger fallback
        self._record_failure()
        if GEMINI_REQUESTS:
            GEMINI_REQUESTS.labels(status="failure").inc()

        logger.error("All Gemini API attempts failed. Falling back to clinical heuristics.")
        return self._heuristic_fallback(patient_name, vital_signs, alert_level)

    def _heuristic_fallback(
        self,
        patient_name: str,
        vital_signs: dict[str, Any],
        alert_level: str,
    ) -> dict[str, Any]:
        """Deterministic clinical heuristic engine (zero external dependency)."""
        spo2 = vital_signs.get("spo2")
        hr = vital_signs.get("hr_mean")

        if alert_level == "red":
            if spo2 and spo2 < 90:
                summary = (
                    f"Bemor {patient_name}da kislorod saturatsiyasi kritik pasaygan (SpO2 {spo2}%). "
                    f"Zudlik bilan kislorod terapiyasi va shifokor ko'rigi talab etiladi."
                )
            elif hr and hr > 120:
                summary = (
                    f"Bemor {patient_name}da xavfli taxikardiya (yurak urishi {hr} zarb/daq) kuzatilmoqda. "
                    f"EKG tekshiruvi tavsiya etiladi."
                )
            else:
                summary = (
                    f"Bemor {patient_name} ko'rsatkichlarida kritik og'ish qayd etildi. "
                    f"Aktiv chaqiruv holati faollashtirildi."
                )
        elif alert_level == "amber":
            summary = (
                f"Bemor {patient_name}da shaxsiy bazaviy normadan barqaror og'ish kuzatilmoqda. "
                f"Patronaj hamshirasining rejaviy ko'rigi tavsiya etiladi."
            )
        else:
            summary = f"Bemor {patient_name}ning barcha fiziologik ko'rsatkichlari barqaror va shaxsiy norma doirasida."

        return {
            "source": "deterministic_clinical_rules",
            "model": "rule_based_v1",
            "summary": summary,
            "latency_sec": 0.001,
        }


# Global singleton instance
gemini_service = GeminiService()

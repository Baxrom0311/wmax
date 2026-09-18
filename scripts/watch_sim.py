#!/usr/bin/env python3
"""NAZORAT — Smartwatch & Ingest Simulator.

Simulates the Wear OS smartwatch and phone companion ingestion pipeline.
Sends 5-minute aggregated biometric readings to the backend API:
    POST /api/v1/ingest
Strictly matches the schema in `contracts/openapi.yaml` (IngestBatch / ReadingIn).

Supports:
- Live streaming simulation with customizable interval.
- Single-batch one-shot mode (--once).
- Idempotency verification (--test-idempotent): tests duplicate detection.
- Offline queue simulation (--test-offline): tests local queueing when server is unreachable.
- Clinical profile presets (--profile: healthy, worsening, recovering).
"""
from __future__ import annotations

import argparse
import logging
import math
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("watch_sim")

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_PATIENT_ID = "11111111-1111-1111-1111-111111111111"
DEVICE_ID_PREFIX = "GALAXY-WATCH5-"


class VitalsGenerator:
    """Generates synthetic 5-minute aggregate biometric readings."""

    def __init__(self, patient_id: str, profile: str = "healthy") -> None:
        self.patient_id = patient_id
        self.profile = profile
        self.step_counter = 0
        self.battery = 100
        self.tick = 0

    def generate_reading(self, ts: datetime) -> dict[str, Any]:
        """Generate a single ReadingIn object matching openapi.yaml."""
        self.tick += 1
        hour = ts.hour

        # Base circadian rhythm for heart rate
        # Lower at night (00:00 - 06:00), higher during the day
        is_night = 0 <= hour < 6
        circadian_hr = 62.0 if is_night else 74.0

        # Profile adjustments
        if self.profile == "worsening":
            # Progressive tachycardia, desaturation, elevated RR
            severity = min(1.0, self.tick / 30.0)
            hr_mean = circadian_hr + severity * 28.0 + random.uniform(-2, 3)
            spo2 = max(86.0, 97.5 - severity * 7.5 + random.uniform(-0.5, 0.5))
            rmssd = max(12.0, 38.0 - severity * 22.0 + random.uniform(-2, 2))
            rr_est = min(28.0, 16.0 + severity * 8.0 + random.uniform(-0.5, 0.5))
            skin_temp = 36.6 + severity * 1.2 + random.uniform(-0.1, 0.1)
        elif self.profile == "recovering":
            severity = max(0.0, 1.0 - self.tick / 30.0)
            hr_mean = circadian_hr + severity * 18.0 + random.uniform(-2, 2)
            spo2 = 94.0 + (1.0 - severity) * 4.0 + random.uniform(-0.4, 0.4)
            rmssd = 22.0 + (1.0 - severity) * 18.0 + random.uniform(-2, 2)
            rr_est = 20.0 - (1.0 - severity) * 4.0 + random.uniform(-0.5, 0.5)
            skin_temp = 36.6 + severity * 0.4 + random.uniform(-0.1, 0.1)
        else:  # "healthy"
            hr_mean = circadian_hr + random.uniform(-4, 6)
            spo2 = min(99.0, max(95.0, 97.8 + random.uniform(-0.8, 0.8)))
            rmssd = max(24.0, 42.0 + random.uniform(-5, 6))
            rr_est = max(12.0, min(18.0, 15.0 + random.uniform(-1.0, 1.0)))
            skin_temp = 36.6 + random.uniform(-0.2, 0.2)

        hr_min = max(45.0, hr_mean - random.uniform(4, 10))
        hr_max = min(160.0, hr_mean + random.uniform(6, 16))
        sdnn = rmssd * 1.35 + random.uniform(-3, 3)

        # Activity steps
        if is_night:
            steps_in_window = random.randint(0, 5) if random.random() < 0.15 else 0
        else:
            steps_in_window = random.randint(10, 180)

        self.step_counter += steps_in_window

        # Battery drain (approx 1% every 30 mins -> ~0.16% per 5-min window)
        self.battery = max(5, self.battery - (1 if self.tick % 6 == 0 else 0))

        # Format ts in ISO 8601 UTC with 'Z' suffix
        ts_utc = ts.astimezone(timezone.utc)
        ts_iso = ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "ts": ts_iso,
            "hr_mean": round(hr_mean, 1),
            "hr_min": round(hr_min, 1),
            "hr_max": round(hr_max, 1),
            "rmssd": round(rmssd, 1),
            "sdnn": round(sdnn, 1),
            "spo2": round(spo2, 1),
            "skin_temp": round(skin_temp, 2),
            "steps": steps_in_window,
            "rr_est": round(rr_est, 1),
            "sleep_frag": round(random.uniform(0.05, 0.25), 2) if is_night else None,
            "worn": True,
            "battery": self.battery,
        }


class OfflineQueueBuffer:
    """Emulates the companion phone Room DB offline buffer.

    When network requests fail, readings stay in this buffer.
    When network recovers, queued readings are flushed in batches (up to 500 items).
    """

    def __init__(self, max_batch_size: int = 500) -> None:
        self.queue: list[dict[str, Any]] = []
        self.max_batch_size = max_batch_size

    def add(self, reading: dict[str, Any]) -> None:
        self.queue.append(reading)

    def add_batch(self, readings: list[dict[str, Any]]) -> None:
        self.queue.extend(readings)

    def drain_batch(self) -> list[dict[str, Any]]:
        """Extract up to max_batch_size readings from buffer."""
        batch = self.queue[: self.max_batch_size]
        return batch

    def acknowledge_sent(self, count: int) -> None:
        """Remove successfully acknowledged readings from the queue."""
        del self.queue[:count]

    @property
    def size(self) -> int:
        return len(self.queue)


class IngestClient:
    """Client for uploading IngestBatch payloads to NAZORAT backend."""

    def __init__(self, base_url: str, patient_id: str, device_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.ingest_url = f"{self.base_url}/api/v1/ingest"
        self.patient_id = patient_id
        self.device_id = device_id
        self.client = httpx.Client(timeout=10.0)

    def send_batch(self, readings: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Send IngestBatch. Returns IngestResult dict or None if request failed."""
        payload = {
            "patient_id": self.patient_id,
            "device_id": self.device_id,
            "readings": readings,
        }
        try:
            resp = self.client.post(self.ingest_url, json=payload)
            if resp.status_code == 200:
                return resp.json()
            logger.error(
                "Ingest failed with status %d: %s",
                resp.status_code,
                resp.text[:200],
            )
            return None
        except httpx.RequestError as exc:
            logger.warning("Network connection failed to %s: %s", self.ingest_url, exc)
            return None

    def close(self) -> None:
        self.client.close()


def run_idempotency_test(client: IngestClient, gen: VitalsGenerator) -> bool:
    """Verifies backend idempotency: resending the same timestamps must be accepted on first try,

    and reported as duplicates on second try with 0 newly accepted rows.
    """
    logger.info("=== STARTING IDEMPOTENCY TEST ===")
    now = datetime.now(timezone.utc)
    # Generate 5 test readings with distinct timestamps
    test_readings = [
        gen.generate_reading(now - timedelta(minutes=5 * i)) for i in range(5, 0, -1)
    ]

    logger.info("Step 1: Sending initial batch of %d readings...", len(test_readings))
    res1 = client.send_batch(test_readings)
    if res1 is None:
        logger.error("❌ Step 1 failed: Could not connect to backend.")
        return False
    logger.info("Step 1 response: %s", res1)

    logger.info(
        "Step 2: Resending the EXACT SAME batch of %d readings...", len(test_readings)
    )
    res2 = client.send_batch(test_readings)
    if res2 is None:
        logger.error("❌ Step 2 failed: Resend request failed.")
        return False
    logger.info("Step 2 response: %s", res2)

    duplicates = res2.get("duplicates", 0)
    accepted = res2.get("accepted", -1)

    if duplicates == len(test_readings) and accepted == 0:
        logger.info(
            "✅ IDEMPOTENCY TEST PASSED! All %d readings recognized as duplicates (accepted=0).",
            duplicates,
        )
        return True
    else:
        logger.error(
            "❌ IDEMPOTENCY TEST FAILED! Expected accepted=0, duplicates=%d. Got accepted=%d, duplicates=%d",
            len(test_readings),
            accepted,
            duplicates,
        )
        return False


def run_offline_test(client: IngestClient, gen: VitalsGenerator) -> bool:
    """Verifies offline queue buffer behavior.

    Simulates network blackout, buffers readings, then flushes them once restored.
    """
    logger.info("=== STARTING OFFLINE QUEUE TEST ===")
    buffer = OfflineQueueBuffer(max_batch_size=500)
    now = datetime.now(timezone.utc)

    # 1. Generate 6 readings while simulating offline state
    logger.info("Step 1: Simulating offline mode (watch collecting 6 windows)...")
    for i in range(6, 0, -1):
        ts = now - timedelta(minutes=5 * i)
        reading = gen.generate_reading(ts)
        buffer.add(reading)
        logger.info("  Buffered reading at %s | Queue size: %d", reading["ts"], buffer.size)

    if buffer.size != 6:
        logger.error("❌ Buffer size mismatch: expected 6, got %d", buffer.size)
        return False

    # 2. Simulate network restored: drain buffer and flush to server
    logger.info("Step 2: Network restored! Flushing queue buffer to backend...")
    batch_to_send = buffer.drain_batch()
    res = client.send_batch(batch_to_send)
    if res is None:
        logger.error("❌ Offline flush failed: Server unreachable.")
        return False

    logger.info("Flush response: %s", res)
    buffer.acknowledge_sent(len(batch_to_send))
    logger.info("Remaining queue size after ACK: %d", buffer.size)

    if buffer.size == 0 and (res.get("accepted", 0) + res.get("duplicates", 0)) == 6:
        logger.info("✅ OFFLINE QUEUE TEST PASSED! All buffered items sent and queue drained.")
        return True
    else:
        logger.error("❌ OFFLINE QUEUE TEST FAILED!")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NAZORAT Smartwatch & Ingest Simulator (A5)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--patient-id",
        type=str,
        default=DEFAULT_PATIENT_ID,
        help="Target patient UUID (must exist in database)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help="Backend base URL",
    )
    parser.add_argument(
        "--device-id",
        type=str,
        default=f"{DEVICE_ID_PREFIX}SIM01",
        help="Emulated device identifier",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Delay in seconds between simulated 5-minute windows in live mode",
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["healthy", "worsening", "recovering"],
        default="healthy",
        help="Clinical trend profile for generated vitals",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Send a single 5-minute reading and exit",
    )
    parser.add_argument(
        "--batch-count",
        type=int,
        default=1,
        help="Number of readings to bundle into a single batch in --once mode",
    )
    parser.add_argument(
        "--test-idempotent",
        action="store_true",
        help="Run idempotency verification test and exit",
    )
    parser.add_argument(
        "--test-offline",
        action="store_true",
        help="Run offline queueing simulation test and exit",
    )

    args = parser.parse_args()

    logger.info("--------------------------------------------------")
    logger.info("NAZORAT Watch Simulator (A5)")
    logger.info("Target Patient: %s", args.patient_id)
    logger.info("Target URL:     %s/api/v1/ingest", args.base_url)
    logger.info("Device ID:      %s", args.device_id)
    logger.info("Profile:        %s", args.profile)
    logger.info("--------------------------------------------------")

    client = IngestClient(
        base_url=args.base_url,
        patient_id=args.patient_id,
        device_id=args.device_id,
    )
    gen = VitalsGenerator(patient_id=args.patient_id, profile=args.profile)

    try:
        # 1. Idempotency test mode
        if args.test_idempotent:
            ok = run_idempotency_test(client, gen)
            return 0 if ok else 1

        # 2. Offline buffer queue test mode
        if args.test_offline:
            ok = run_offline_test(client, gen)
            return 0 if ok else 1

        # 3. Single shot mode (--once)
        if args.once:
            now = datetime.now(timezone.utc)
            readings = [
                gen.generate_reading(now - timedelta(minutes=5 * i))
                for i in range(args.batch_count - 1, -1, -1)
            ]
            logger.info("Sending one-shot batch with %d reading(s)...", len(readings))
            res = client.send_batch(readings)
            if res is not None:
                logger.info("✅ Result: accepted=%d, duplicates=%d, latest_level=%s",
                            res.get("accepted"), res.get("duplicates"), res.get("latest_level"))
                return 0
            else:
                logger.error("❌ Failed to send one-shot batch.")
                return 1

        # 4. Continuous live streaming mode with offline buffer support
        logger.info("Starting live simulator (Interval: %.1fs per 5-min window). Press Ctrl+C to stop.", args.interval)
        buffer = OfflineQueueBuffer()
        current_time = datetime.now(timezone.utc)

        while True:
            reading = gen.generate_reading(current_time)
            buffer.add(reading)
            logger.info(
                "⌚ Watch sample at %s: HR=%.1f SpO2=%.1f RR=%.1f Temp=%.2f Steps=%d Batt=%d%%",
                reading["ts"],
                reading["hr_mean"],
                reading["spo2"],
                reading["rr_est"],
                reading["skin_temp"],
                reading["steps"],
                reading["battery"],
            )

            # Attempt to send all buffered items
            batch = buffer.drain_batch()
            res = client.send_batch(batch)

            if res is not None:
                buffer.acknowledge_sent(len(batch))
                logger.info(
                    "  📡 Synced %d reading(s) -> accepted=%d, duplicates=%d, level=%s (Queue: %d)",
                    len(batch),
                    res.get("accepted", 0),
                    res.get("duplicates", 0),
                    res.get("latest_level", "unknown"),
                    buffer.size,
                )
            else:
                logger.warning(
                    "  ⚠️ Network send failed. %d reading(s) retained in offline buffer (Total queued: %d)",
                    len(batch),
                    buffer.size,
                )

            current_time += timedelta(minutes=5)
            time.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("\nSimulation stopped by user.")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())

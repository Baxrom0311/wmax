#!/usr/bin/env python3
"""Seeds demo data directly into the database through the ORM.

Replaces the old `gen_seed.py` + `contracts/seed.sql` pair. Schema comes from
Alembic, data comes from here — there is no hand-maintained SQL in either path,
so a column rename in a model can never leave a stale INSERT behind.

Timestamps are anchored to "now", so the seed is never stale: a rebuild on demo
day still produces 14 days of history ending a few minutes ago rather than
leaving every patient in `no_data`.

Usage:
    python scripts/seed_demo.py              # skips if patients already exist
    python scripts/seed_demo.py --force      # wipes demo rows and reseeds

Refuses to run against ENV=production unless --force is given explicitly.
"""
from __future__ import annotations

import argparse
import asyncio
import math
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT, _ROOT / "backend", _ROOT / "contracts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.db import get_sessionmaker
from app.core.security import hash_password
from app.models import Patient, Reading, Relative, Task, User
from app.repositories.baseline_repo import BaselineRepository
from app.services.pipeline_service import PipelineService
from algo.baseline import compute_baselines
from algo_interface import ReadingVec

random.seed(20260918)
TZ = ZoneInfo(settings.TZ_LOCAL)

DAYS = 14
STEP_MIN = 5
N = DAYS * 24 * 60 // STEP_MIN  # 4032 readings per patient
# Days of monitoring after the doctor signs off the baseline.
LEARNING_DAYS = 6

DOCTOR_PASSWORD = "wmax123"
RELATIVE_PIN = "112233"

DOC_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
NURSE_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

PATIENTS = [
    # id, name, birth_year, sex, diagnosis, district, trajectory
    (uuid.UUID("11111111-1111-1111-1111-111111111111"), "Otabek Ro'zmetov", 1958, "m",
     "Yurak yetishmovchiligi (NYHA III)", "Urganch", "worsening"),
    (uuid.UUID("22222222-2222-2222-2222-222222222222"), "Gulnora Matyoqubova", 1954, "f",
     "O'pka surunkali obstruktiv kasalligi", "Xiva", "improving"),
    (uuid.UUID("33333333-3333-3333-3333-333333333333"), "Rustam Qurbonov", 1967, "m",
     "Miokard infarktidan keyingi holat", "Xonqa", "stable"),
]

RELATIVES = [
    (uuid.UUID("aaaaaaaa-1111-1111-1111-111111111111"), PATIENTS[0][0],
     "Dilnoza Ro'zmetova", "+998901110011"),
    (uuid.UUID("aaaaaaaa-2222-2222-2222-222222222222"), PATIENTS[1][0],
     "Sardor Matyoqubov", "+998901110022"),
    (uuid.UUID("aaaaaaaa-3333-3333-3333-333333333333"), PATIENTS[2][0],
     "Malika Qurbonova", "+998901110033"),
]


def severity(trajectory: str, day: float) -> float:
    """0.0 = healthy, 1.0 = clearly decompensating, as a function of day (0..14)."""
    if trajectory == "stable":
        return 0.0
    if trajectory == "worsening":
        # Silent drift from day 9, clearly abnormal by day 13-14. This is the
        # window the early-warning engine is supposed to catch.
        return 0.0 if day < 9 else min(1.0, (day - 9) / 4.5)
    # improving: starts rough, normalises by day 8
    return max(0.0, 1.0 - day / 8.0) * 0.7


def generate_readings(patient_id: uuid.UUID, trajectory: str) -> list[dict]:
    """Builds 14 days of 5-minute aggregates with circadian shape and a charging gap."""
    now = datetime.now(timezone.utc)
    hr_base, spo2_base, temp_base, rmssd_base, rr_base = 66.0, 97.0, 34.2, 38.0, 15.5
    rows: list[dict] = []

    for i in range(N):
        minutes_ago = (N - 1 - i) * STEP_MIN
        ts = now - timedelta(minutes=minutes_ago)
        local = ts.astimezone(TZ)
        sev = severity(trajectory, i * STEP_MIN / 1440.0)

        hour = local.hour + local.minute / 60.0
        asleep = hour >= 23 or hour < 6.5
        circadian = -6.0 if asleep else 6.0 * math.sin((hour - 6) / 24 * 2 * math.pi)

        # The watch comes off to charge 03:00-04:00 local — this is what makes
        # the `no_data` path exercisable with realistic data.
        worn = not (3.0 <= hour < 4.0)
        battery = 100 - int((minutes_ago % 1440) / 1440 * 45)

        if not worn:
            # Every row must carry the same keys: a multi-row INSERT renders one
            # VALUES clause, so a missing column in one dict breaks the whole batch.
            rows.append({
                "patient_id": patient_id, "ts": ts,
                "hr_mean": None, "hr_min": None, "hr_max": None,
                "rmssd": None, "sdnn": None, "spo2": None, "skin_temp": None,
                "steps": None, "rr_est": None, "sleep_frag": None,
                "worn": False, "battery": battery,
            })
            continue

        hr = hr_base + circadian + random.gauss(0, 2.2) + sev * hr_base * 0.14
        spo2 = spo2_base + random.gauss(0, 0.6) - sev * 3.2
        temp = temp_base + (-0.4 if asleep else 0.2) + random.gauss(0, 0.15) + sev * 0.7
        rmssd = max(
            4.0,
            rmssd_base + (8 if asleep else 0) + random.gauss(0, 4) - sev * rmssd_base * 0.33,
        )
        rr = rr_base + (-1.5 if asleep else 0.5) + random.gauss(0, 0.8) + sev * 3.0

        rows.append({
            "patient_id": patient_id,
            "ts": ts,
            "hr_mean": round(hr, 1),
            "hr_min": round(hr - random.uniform(3, 7), 1),
            "hr_max": round(hr + random.uniform(4, 12), 1),
            "rmssd": round(rmssd, 1),
            "sdnn": round(rmssd * random.uniform(1.4, 1.8), 1),
            "spo2": round(spo2, 1),
            "skin_temp": round(temp, 2),
            "steps": 0 if asleep else max(0, int(random.gauss(55, 45) * (1 - 0.5 * sev))),
            "rr_est": round(rr, 1),
            "sleep_frag": round(random.uniform(0.4, 1.2) + sev * 2.4, 2) if asleep else 0.0,
            "worn": True,
            "battery": battery,
        })

    return rows


async def clear_demo_rows(session) -> None:
    """Removes the demo fixtures only — never touches other rows."""
    patient_ids = [p[0] for p in PATIENTS]
    await session.execute(delete(Task).where(Task.patient_id.in_(patient_ids)))
    await session.execute(delete(Reading).where(Reading.patient_id.in_(patient_ids)))
    await session.execute(delete(Relative).where(Relative.patient_id.in_(patient_ids)))
    await session.execute(delete(Patient).where(Patient.id.in_(patient_ids)))
    await session.execute(delete(User).where(User.id.in_([DOC_ID, NURSE_ID])))
    await session.commit()


async def seed(force: bool) -> None:
    session_factory = get_sessionmaker()

    async with session_factory() as session:
        existing = (
            await session.execute(select(Patient.id).where(Patient.id == PATIENTS[0][0]))
        ).scalar_one_or_none()

        if existing and not force:
            print("Demo ma'lumotlari allaqachon mavjud — o'tkazib yuborildi (--force bilan qayta yozing).")
            return

        if existing:
            print("Eski demo qatorlari o'chirilmoqda...")
            await clear_demo_rows(session)

        password_hash = hash_password(DOCTOR_PASSWORD)
        pin_hash = hash_password(RELATIVE_PIN)

        session.add_all([
            User(id=DOC_ID, full_name="Doktor Islom Yusupov", phone="+998901234567",
                 password_hash=password_hash, role="doctor", district="Urganch"),
            User(id=NURSE_ID, full_name="Hamshira Zilola Otajonova", phone="+998901234568",
                 password_hash=password_hash, role="nurse", district="Urganch"),
        ])
        await session.flush()

        today = date.today()
        for pid, name, birth_year, sex, diagnosis, district, _traj in PATIENTS:
            session.add(Patient(
                id=pid,
                full_name=name,
                birth_date=date(birth_year, 6, 15),
                age=today.year - birth_year,
                sex=sex,
                diagnosis=diagnosis,
                district=district,
                discharge_date=today - timedelta(days=13),
                phase="full",
                doctor_id=DOC_ID,
                nurse_id=NURSE_ID,
                device_id=f"GW5-{str(pid)[:4]}",
            ))

        for rid, pid, name, phone in RELATIVES:
            session.add(Relative(
                id=rid,
                patient_id=pid,
                full_name=name,
                phone=phone,
                pin_hash=pin_hash,
                access_token="r_" + str(rid).replace("-", "")[:24] + "x7k2",
            ))
        await session.flush()

        total = 0
        readings_by_patient: dict[uuid.UUID, list[dict]] = {}
        for pid, name, *_rest, trajectory in PATIENTS:
            rows = generate_readings(pid, trajectory)
            readings_by_patient[pid] = rows
            # Ingest is idempotent on (patient_id, ts); reseeding must behave the same.
            for chunk_start in range(0, len(rows), 1000):
                chunk = rows[chunk_start:chunk_start + 1000]
                await session.execute(
                    pg_insert(Reading)
                    .values(chunk)
                    .on_conflict_do_nothing(index_elements=["patient_id", "ts"])
                )
            total += len(rows)
            print(f"  {name}: {len(rows)} o'lchov ({trajectory})")

        # One open active-call task so the doctor panel is not empty on day one.
        now = datetime.now(timezone.utc)
        session.add(Task(
            patient_id=PATIENTS[0][0],
            doctor_id=DOC_ID,
            type="active_call",
            status="sent",
            created_at=now - timedelta(hours=6),
            due_at=now + timedelta(hours=18),
        ))

        await session.commit()

        # Run the clinical pipeline once per patient. Without this the seed
        # leaves every patient at `green` with no baselines: the signal engine
        # only learns a personal norm when it actually evaluates readings, so a
        # freshly seeded demo would show the deteriorating patient as healthy.
        print("\nKlinik dvigatel ishga tushirilmoqda (baseline + signal)...")
        pipeline = PipelineService(session)
        baseline_repo = BaselineRepository(session)

        # Reproduce the real timeline: the first week after discharge is the
        # learning window, the doctor signs the baseline off, and only then does
        # monitoring begin. Learning from all 14 days instead would let the
        # deteriorating patient's own decline define their "normal" — the
        # baseline would absorb the very signal we need to catch.
        learning_end = datetime.now(timezone.utc) - timedelta(days=LEARNING_DAYS)

        for pid, name, *_rest in PATIENTS:
            learning_vecs = [
                ReadingVec(
                    ts=r["ts"], hr_mean=r["hr_mean"], hr_min=r["hr_min"],
                    hr_max=r["hr_max"], rmssd=r["rmssd"], sdnn=r["sdnn"],
                    spo2=r["spo2"], skin_temp=r["skin_temp"], steps=r["steps"],
                    rr_est=r["rr_est"], sleep_frag=r["sleep_frag"], worn=r["worn"],
                )
                for r in readings_by_patient[pid]
                if r["ts"] < learning_end
            ]
            await baseline_repo.upsert_baselines(pid, compute_baselines(learning_vecs))

            patient = await session.get(Patient, pid)
            patient.baseline_approved_by = DOC_ID
            patient.baseline_approved_at = learning_end
            await session.flush()

            result = await pipeline.evaluate_patient(pid)
            icon = {"red": "🔴", "amber": "🟡", "green": "🟢"}.get(result.level, "⚪")
            print(
                f"  {icon} {name}: {result.level} "
                f"(ball {result.composite_score:.2f}, sabab: {result.reason or '—'})"
            )
        await session.commit()

        print(f"\n✓ Seed tugadi · {len(PATIENTS)} bemor · {total} o'lchov")
        print(f"  Shifokor: +998901234567 / {DOCTOR_PASSWORD}")
        print(f"  Qarovchi: +998901110011 / PIN {RELATIVE_PIN}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data via the ORM.")
    parser.add_argument("--force", action="store_true",
                        help="Wipe existing demo rows and reseed; also required in production.")
    args = parser.parse_args()

    if settings.ENV == "production" and not args.force:
        print("ENV=production — demo ma'lumot kiritish rad etildi. Ataylab bo'lsa --force bering.")
        raise SystemExit(1)

    asyncio.run(seed(force=args.force))


if __name__ == "__main__":
    main()

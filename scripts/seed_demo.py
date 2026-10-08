#!/usr/bin/env python3
"""Seeds demo data directly into the database through the ORM.

Replaces the old `gen_seed.py` + `contracts/seed.sql` pair. Schema comes from
Alembic, data comes from here — there is no hand-maintained SQL in either path.
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
from app.models import (
    Account,
    Device,
    DeviceAssignment,
    Patient,
    PatientAccess,
    PatientMembership,
    Reading,
    Task,
    Tenant,
    TenantMember,
)
from app.repositories.baseline_repo import BaselineRepository
from app.services.pipeline_service import PipelineService
from algo.baseline import compute_baselines
from algo_interface import ReadingVec

random.seed(20260918)
TZ = ZoneInfo(settings.TZ_LOCAL)

DAYS = 14
STEP_MIN = 5
N = DAYS * 24 * 60 // STEP_MIN  # 4032 readings per patient
LEARNING_DAYS = 6

DOCTOR_PASSWORD = "wmax123"
RELATIVE_PIN = "112233"

TENANT_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
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
    if trajectory == "stable":
        return 0.0
    if trajectory == "worsening":
        return 0.0 if day < 9 else min(1.0, (day - 9) / 4.5)
    return max(0.0, 1.0 - day / 8.0) * 0.7


def generate_readings(patient_id: uuid.UUID, device_id: uuid.UUID, trajectory: str) -> list[dict]:
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

        worn = not (3.0 <= hour < 4.0)
        battery = 100 - int((minutes_ago % 1440) / 1440 * 45)

        if not worn:
            rows.append({
                "patient_id": patient_id,
                "device_id": device_id,
                "window_start": ts,
                "window_end": ts + timedelta(minutes=STEP_MIN),
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
            "device_id": device_id,
            "window_start": ts,
            "window_end": ts + timedelta(minutes=STEP_MIN),
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
    patient_ids = [p[0] for p in PATIENTS]
    device_ids = [uuid.uuid5(uuid.NAMESPACE_DNS, f"device_{pid}") for pid in patient_ids]
    caregiver_account_ids = [
        uuid.uuid5(uuid.NAMESPACE_DNS, f"caregiver_{phone}")
        for _rid, _pid, _name, phone in RELATIVES
    ]
    await session.execute(delete(Task).where(Task.patient_id.in_(patient_ids)))
    await session.execute(delete(Reading).where(Reading.patient_id.in_(patient_ids)))
    await session.execute(delete(DeviceAssignment).where(DeviceAssignment.patient_id.in_(patient_ids)))
    await session.execute(delete(Device).where(Device.id.in_(device_ids)))
    await session.execute(delete(PatientAccess).where(PatientAccess.patient_id.in_(patient_ids)))
    await session.execute(delete(PatientMembership).where(PatientMembership.patient_id.in_(patient_ids)))
    await session.execute(delete(Patient).where(Patient.id.in_(patient_ids)))
    await session.execute(delete(TenantMember).where(TenantMember.account_id.in_([DOC_ID, NURSE_ID])))
    await session.execute(delete(Tenant).where(Tenant.id == TENANT_ID))
    await session.execute(delete(Account).where(Account.id.in_([DOC_ID, NURSE_ID] + caregiver_account_ids)))
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

        session.add(Tenant(
            id=TENANT_ID,
            kind="polyclinic",
            name="Urganch Shahar Ko'p Tarmoqli Poliklinikasi",
            region="Xorazm",
            district="Urganch",
            is_active=True,
        ))
        session.add_all([
            Account(id=DOC_ID, full_name="Doktor Islom Yusupov", phone="+998901234567",
                    password_hash=password_hash, is_active=True),
            Account(id=NURSE_ID, full_name="Hamshira Zilola Otajonova", phone="+998901234568",
                    password_hash=password_hash, is_active=True),
        ])
        session.add_all([
            TenantMember(tenant_id=TENANT_ID, account_id=DOC_ID, role="doctor"),
            TenantMember(tenant_id=TENANT_ID, account_id=NURSE_ID, role="nurse"),
        ])
        await session.flush()

        today = date.today()
        patient_devices: dict[uuid.UUID, uuid.UUID] = {}
        for pid, name, birth_year, sex, diagnosis, district, _traj in PATIENTS:
            dev_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"device_{pid}")
            patient_devices[pid] = dev_id
            session.add(Device(
                id=dev_id,
                serial=f"GW5-{str(pid)[:4]}",
                model="Galaxy Watch 5",
                tier="tier1_wearos",
                owner_tenant_id=TENANT_ID,
                status="assigned",
            ))
            session.add(Patient(
                id=pid,
                full_name=name,
                birth_date=date(birth_year, 6, 15),
                sex=sex,
                diagnosis=diagnosis,
                district=district,
                discharge_date=today - timedelta(days=13),
                phase="full",
                device_id=f"GW5-{str(pid)[:4]}",
            ))

        for rid, pid, name, phone in RELATIVES:
            caregiver_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"caregiver_{phone}")
            session.add(Account(
                id=caregiver_account_id,
                full_name=name,
                phone=phone,
                password_hash=pin_hash,
                is_active=True,
            ))
            session.add(PatientAccess(
                id=rid,
                patient_id=pid,
                account_id=caregiver_account_id,
                role="caregiver",
                relation="qarovchi",
            ))
        await session.flush()

        for pid, name, *_rest in PATIENTS:
            dev_id = patient_devices[pid]
            session.add(PatientMembership(
                patient_id=pid,
                tenant_id=TENANT_ID,
                kind="care",
                granted_by=DOC_ID,
            ))
            session.add(DeviceAssignment(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, f"assign_{pid}"),
                device_id=dev_id,
                patient_id=pid,
                assigned_at=datetime.now(timezone.utc) - timedelta(days=14),
            ))
        await session.flush()

        total = 0
        readings_by_patient: dict[uuid.UUID, list[dict]] = {}
        for pid, name, *_rest, trajectory in PATIENTS:
            dev_id = patient_devices[pid]
            rows = generate_readings(pid, dev_id, trajectory)
            readings_by_patient[pid] = rows
            for chunk_start in range(0, len(rows), 1000):
                chunk = rows[chunk_start:chunk_start + 1000]
                await session.execute(
                    pg_insert(Reading.__table__)
                    .values(chunk)
                    .on_conflict_do_nothing(index_elements=["device_id", "window_start"])
                )
            total += len(rows)
            print(f"  {name}: {len(rows)} o'lchov ({trajectory})")

        now = datetime.now(timezone.utc)
        session.add(Task(
            patient_id=PATIENTS[0][0],
            tenant_id=TENANT_ID,
            assignee_account_id=DOC_ID,
            kind="clinical",
            status="open",
            created_at=now - timedelta(hours=6),
            due_at=now + timedelta(hours=18),
        ))

        await session.commit()

        print("\nKlinik dvigatel ishga tushirilmoqda (baseline + signal)...")
        pipeline = PipelineService(session)
        baseline_repo = BaselineRepository(session)
        learning_end = datetime.now(timezone.utc) - timedelta(days=LEARNING_DAYS)

        for pid, name, *_rest in PATIENTS:
            learning_vecs = [
                ReadingVec(
                    ts=r["window_start"], hr_mean=r["hr_mean"], hr_min=r["hr_min"],
                    hr_max=r["hr_max"], rmssd=r["rmssd"], sdnn=r["sdnn"],
                    spo2=r["spo2"], skin_temp=r["skin_temp"], steps=r["steps"],
                    rr_est=r["rr_est"], sleep_frag=r["sleep_frag"], worn=r["worn"],
                )
                for r in readings_by_patient[pid]
                if r["window_start"] < learning_end
            ]
            await baseline_repo.upsert_baselines(pid, compute_baselines(learning_vecs))

        for pid, name, *_rest, trajectory in PATIENTS:
            eval_result = await pipeline.evaluate_patient(patient_id=pid)
            print(f"  {name} ({trajectory}) -> {eval_result.level.upper()}")

        print(f"\nTayyor: {len(PATIENTS)} bemor, {total} o'lchov, baselinelar hisoblandi.")


def main() -> None:
    parser = argparse.ArgumentParser(description="WMAX demo ma'lumotlarini yuklash")
    parser.add_argument("--force", action="store_true", help="Mavjud ma'lumotlarni o'chirib qayta yuklash")
    args = parser.parse_args()

    asyncio.run(seed(force=args.force))


if __name__ == "__main__":
    main()

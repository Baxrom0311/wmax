#!/usr/bin/env python3
"""Task 0 tool: generate contracts/seed.sql — 3 patients x 14 days of 5-min readings.

Timestamps are emitted as `now() - interval 'N minutes'`, so the seed is always
fresh no matter when the database is initialised. Without this, a rebuild on
demo day would leave every patient in `no_data`.

This is NOT the demo simulator. A2 owns scripts/simulate.py (--live) separately.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

random.seed(20260918)
TZ = ZoneInfo("Asia/Tashkent")

DAYS = 14
STEP_MIN = 5
N = DAYS * 24 * 60 // STEP_MIN          # 4032 readings per patient

DOC_ID = "00000000-0000-0000-0000-000000000001"
NURSE_ID = "00000000-0000-0000-0000-000000000002"
PATIENTS = [
    # id, name, age, sex, diagnosis, district, profile
    ("11111111-1111-1111-1111-111111111111", "Otabek Ro'zmetov", 68, "m",
     "Yurak yetishmovchiligi (NYHA III)", "Urganch", "worsening"),
    ("22222222-2222-2222-2222-222222222222", "Gulnora Matyoqubova", 72, "f",
     "O'pka surunkali obstruktiv kasalligi", "Xiva", "improving"),
    ("33333333-3333-3333-3333-333333333333", "Rustam Qurbonov", 59, "m",
     "Miokard infarktidan keyingi holat", "Xonqa", "stable"),
]
RELATIVES = [
    ("aaaaaaaa-1111-1111-1111-111111111111", PATIENTS[0][0], "Dilnoza Ro'zmetova", "+998901110011"),
    ("aaaaaaaa-2222-2222-2222-222222222222", PATIENTS[1][0], "Sardor Matyoqubov",  "+998901110022"),
    ("aaaaaaaa-3333-3333-3333-333333333333", PATIENTS[2][0], "Malika Qurbonova",   "+998901110033"),
]


def bcrypt_hash(raw: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(raw.encode(), bcrypt.gensalt(12)).decode()
    except ImportError:
        # bcrypt yo'q bo'lsa — oldindan hisoblangan "nazorat123" hash'i
        return "$2b$12$SU4dFgp9aTPQpIT9d6tVre7b.3S7dq9ZGI5Z.pMh7x/nDZxe1fxP."


def sev(profile: str, day: float) -> float:
    """0.0 = healthy .. 1.0 = clearly decompensating, as a function of day (0..14)."""
    if profile == "stable":
        return 0.0
    if profile == "worsening":
        # silent drift from day 9, clearly abnormal by day 13-14
        return 0.0 if day < 9 else min(1.0, (day - 9) / 4.5)
    # improving: starts rough, normalises by day 8
    return max(0.0, 1.0 - day / 8.0) * 0.7


def q(s: str) -> str:
    """Escape a single quote for SQL literals: O'pka -> O''pka."""
    return s.replace("'", "''")


def f(x: float, nd: int = 1) -> str:
    return f"{round(x, nd)}"


def gen_patient(pid: str, profile: str) -> list[str]:
    rows: list[str] = []
    now = datetime.now(timezone.utc)
    hr_base, spo2_base, temp_base, rmssd_base, rr_base = 66.0, 97.0, 34.2, 38.0, 15.5

    for i in range(N):
        minutes_ago = (N - 1 - i) * STEP_MIN
        ts = now - timedelta(minutes=minutes_ago)
        loc = ts.astimezone(TZ)
        day = (N - 1 - (N - 1 - i)) * STEP_MIN / 1440.0
        day = i * STEP_MIN / 1440.0
        s = sev(profile, day)

        hour = loc.hour + loc.minute / 60.0
        asleep = hour >= 23 or hour < 6.5
        circ = -6.0 if asleep else 6.0 * math.sin((hour - 6) / 24 * 2 * math.pi)

        # charging gap: 03:00-04:00 local, watch off the wrist
        worn = not (3.0 <= hour < 4.0)

        hr = hr_base + circ + random.gauss(0, 2.2) + s * hr_base * 0.14
        spo2 = spo2_base + random.gauss(0, 0.6) - s * 3.2
        temp = temp_base + ((-0.4) if asleep else 0.2) + random.gauss(0, 0.15) + s * 0.7
        rmssd = max(4.0, rmssd_base + (8 if asleep else 0) + random.gauss(0, 4) - s * rmssd_base * 0.33)
        sdnn = rmssd * random.uniform(1.4, 1.8)
        rr = rr_base + (-1.5 if asleep else 0.5) + random.gauss(0, 0.8) + s * 3.0
        steps = 0 if asleep else max(0, int(random.gauss(55, 45) * (1 - 0.5 * s)))
        sleep_frag = (random.uniform(0.4, 1.2) + s * 2.4) if asleep else 0.0
        battery = 100 - int((minutes_ago % 1440) / 1440 * 45)

        if not worn:
            rows.append(
                f"('{pid}', now() - interval '{minutes_ago} minutes', "
                f"NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL, false, {battery})"
            )
            continue

        rows.append(
            f"('{pid}', now() - interval '{minutes_ago} minutes', "
            f"{f(hr)},{f(hr-random.uniform(3,7))},{f(hr+random.uniform(4,12))},"
            f"{f(rmssd)},{f(sdnn)},{f(spo2)},{f(temp,2)},{steps},{f(rr)},{f(sleep_frag,2)}, true, {battery})"
        )
    return rows


def main() -> None:
    out: list[str] = [
        "-- AVTOMATIK GENERATSIYA: scripts/gen_seed.py. Qo'lda tahrirlamang.",
        "-- 3 bemor x 14 kun x 5 daqiqa. Vaqtlar now() ga nisbatan — seed hech qachon eskirmaydi.",
        "",
    ]
    pw = bcrypt_hash("nazorat123")
    pin = bcrypt_hash("112233")

    out.append("INSERT INTO users (id, full_name, phone, password_hash, role, district) VALUES")
    out.append(f"  ('{DOC_ID}', '{q('Doktor Islom Yusupov')}', '+998901234567', '{pw}', 'doctor', 'Urganch'),")
    out.append(f"  ('{NURSE_ID}', '{q('Hamshira Zilola Otajonova')}', '+998901234568', '{pw}', 'nurse', 'Urganch');")
    out.append("")

    out.append("INSERT INTO patients (id, full_name, age, sex, diagnosis, district, discharge_date, phase, doctor_id, nurse_id, device_id) VALUES")
    vals = []
    for pid, name, age, sex, dx, dist, _ in PATIENTS:
        vals.append(
            f"  ('{pid}', '{q(name)}', {age}, '{sex}', '{q(dx)}', '{q(dist)}', "
            f"current_date - 13, 'full', '{DOC_ID}', '{NURSE_ID}', 'GW5-{pid[:4]}')"
        )
    out.append(",\n".join(vals) + ";")
    out.append("")

    out.append("INSERT INTO relatives (id, patient_id, full_name, phone, pin_hash, access_token) VALUES")
    vals = []
    for rid, pid, name, phone in RELATIVES:
        token = "r_" + rid.replace("-", "")[:24] + "x7k2"
        vals.append(f"  ('{rid}', '{pid}', '{q(name)}', '{phone}', '{pin}', '{token}')")
    out.append(",\n".join(vals) + ";")
    out.append("")

    cols = ("patient_id, ts, hr_mean, hr_min, hr_max, rmssd, sdnn, spo2, "
            "skin_temp, steps, rr_est, sleep_frag, worn, battery")
    for pid, name, *_rest, profile in PATIENTS:
        rows = gen_patient(pid, profile)
        out.append(f"-- {q(name)}: {profile}")
        for c in range(0, len(rows), 500):
            chunk = rows[c:c + 500]
            out.append(f"INSERT INTO readings ({cols}) VALUES")
            out.append(",\n".join(chunk) + "\nON CONFLICT (patient_id, ts) DO NOTHING;")
        out.append("")

    # One open active-call task so the doctor panel has something on day one.
    out.append(
        "INSERT INTO tasks (patient_id, doctor_id, type, status, created_at, due_at) VALUES\n"
        f"  ('{PATIENTS[0][0]}', '{DOC_ID}', 'active_call', 'sent', now() - interval '6 hours', now() + interval '18 hours');"
    )
    out.append("")

    with open("contracts/seed.sql", "w") as fh:
        fh.write("\n".join(out))
    print(f"contracts/seed.sql yozildi · bemor: {len(PATIENTS)} · o'lchov/bemor: {N}")


if __name__ == "__main__":
    main()

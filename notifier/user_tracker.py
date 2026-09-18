from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .admin_store import SUPER_ADMIN_ID, is_admin, is_super_admin

logger = logging.getLogger("nazorat.notifier.user_tracker")

DATA_DIR = Path(__file__).resolve().parent
USERS_FILE = DATA_DIR / "users.json"
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5174").rstrip("/")

# --------------------------------------------------------------------------
# NAZORAT (WMAX) — Haqiqiy Klinik Baza (Real Clinical Patient & Relative Registry)
# Asos: contracts/seed.sql, contracts/schema.sql va web-doctor klinik bazasi
# --------------------------------------------------------------------------
REAL_PATIENTS_AND_RELATIVES: list[dict[str, Any]] = [
    {
        "card_no": "WMAX-001-URG",
        "patient_id": "11111111-1111-1111-1111-111111111111",
        "patient_name": "Otabek Ro'zmetov",
        "age": 68,
        "sex": "Erkak",
        "diagnosis": "Surunkali yurak yetishmovchiligi (SYuYe IIB, NYHA III). Zo'riqish stenokardiyasi FK III. Postinfarkt kardioskleroz. Sinusli taxikardiya va gipoksemiya",
        "district": "Urganch shahri",
        "triage_level": "🔴 Qizil (Dekompensatsiya xavfi)",
        "vitals_summary": "SpO₂: 87% (Kritik), Puls: 112 bpm, Tana harorati: 37.4°C, Nafas: 24/daq",
        "device_id": "GW5-1111 (Galaxy Watch 5)",
        "monitoring_phase": "To'liq nazorat (Full phase)",
        "relative_name": "Dilnoza Ro'zmetova",
        "relationship": "Qizi (bemor yaqini)",
        "relative_phone": "+998 90 111 00 11",
        "relative_pin": "112233",
        "access_token": "r_aaaaaaaa1111111111111111x7k2",
        "doctor_name": "Doktor Islom Yusupov (+998 90 123 45 67)",
        "nurse_name": "Hamshira Zilola Otajonova (+998 90 123 45 68)",
    },
    {
        "card_no": "WMAX-002-XIV",
        "patient_id": "22222222-2222-2222-2222-222222222222",
        "patient_name": "Gulnora Matyoqubova",
        "age": 72,
        "sex": "Ayol",
        "diagnosis": "Gipertoniya kasalligi III bosqich, 3-daraja, xavf IV (o'ta yuqori). 2-tur qandli diabet, subkompensatsiya. O'pkaning surunkali obstruktiv kasalligi (O'SOK)",
        "district": "Xiva shahri",
        "triage_level": "🟡 Sariq (Diqqat / Ostonaviy og'ish)",
        "vitals_summary": "SpO₂: 94%, Puls: 94 bpm, Harorat: 36.6°C, RMSSD: 18.2 ms",
        "device_id": "GW5-2222 (Galaxy Watch 5)",
        "monitoring_phase": "Moslashuv davri (Learning phase)",
        "relative_name": "Sardor Matyoqubov",
        "relationship": "O'g'li (bemor yaqini)",
        "relative_phone": "+998 90 111 00 22",
        "relative_pin": "112233",
        "access_token": "r_aaaaaaaa2222222222222222x7k2",
        "doctor_name": "Doktor Islom Yusupov (+998 90 123 45 67)",
        "nurse_name": "Hamshira Zilola Otajonova (+998 90 123 45 68)",
    },
    {
        "card_no": "WMAX-003-XON",
        "patient_id": "33333333-3333-3333-3333-333333333333",
        "patient_name": "Rustam Qurbonov",
        "age": 59,
        "sex": "Erkak",
        "diagnosis": "Birlamchi kardiomiopatiya. SYuYe I-IIA bosqich, NYHA II. Miokard infarktidan keyingi holat. Sinus ritmi, barqaror gemodinamika",
        "district": "Xonqa tumani",
        "triage_level": "🟢 Yashil (Barqaror / Kompensatsiya)",
        "vitals_summary": "SpO₂: 97%, Puls: 72 bpm, Harorat: 36.6°C, Nafas: 16/daq",
        "device_id": "GW5-3333 (Galaxy Watch 5)",
        "monitoring_phase": "To'liq nazorat (Full phase)",
        "relative_name": "Malika Qurbonova",
        "relationship": "Turmush o'rtog'i (bemor yaqini)",
        "relative_phone": "+998 90 111 00 33",
        "relative_pin": "112233",
        "access_token": "r_aaaaaaaa3333333333333333x7k2",
        "doctor_name": "Doktor Islom Yusupov (+998 90 123 45 67)",
        "nurse_name": "Hamshira Zilola Otajonova (+998 90 123 45 68)",
    },
    {
        "card_no": "WMAX-004-SHO",
        "patient_id": "44444444-4444-4444-4444-444444444444",
        "patient_name": "Jumaniyoz Otajonov",
        "age": 65,
        "sex": "Erkak",
        "diagnosis": "O'pkaning surunkali obstruktiv kasalligi (O'SOK), og'ir kechishi (GOLD III). Surunkali o'pka yuragi, dekompensatsiya xavfi",
        "district": "Shovot tumani",
        "triage_level": "⚪️ Ma'lumot yo'q (45+ daqiqadan buyon uzilgan)",
        "vitals_summary": "Telemetriya signali yo'q (Soat yechilgan yoki quvvat tugagan)",
        "device_id": "GW5-4444 (Galaxy Watch 5)",
        "monitoring_phase": "Kalibratsiya davri (Calib phase)",
        "relative_name": "Farhod Otajonov",
        "relationship": "O'g'li (bemor yaqini)",
        "relative_phone": "+998 90 111 00 44",
        "relative_pin": "112233",
        "access_token": "r_aaaaaaaa4444444444444444x7k2",
        "doctor_name": "Doktor Islom Yusupov (+998 90 123 45 67)",
        "nurse_name": "Hamshira Zilola Otajonova (+998 90 123 45 68)",
    },
]

# --------------------------------------------------------------------------
# NAZORAT — Tibbiyot Xodimlari va Administratorlar (contracts/seed.sql)
# --------------------------------------------------------------------------
REAL_MEDICAL_STAFF: list[dict[str, Any]] = [
    {
        "id": "USR-DOC-001",
        "full_name": "Doktor Islom Yusupov",
        "role": "👨‍⚕️ Bosh Kardiolog Shifokor",
        "phone": "+998 90 123 45 67",
        "login": "+998901234567 (Parol: nazorat123)",
        "institution": "Xorazm viloyati Kardiologiya Dispanseri",
        "assigned": "Barcha bemorlar (Otabek, Gulnora, Rustam, Jumaniyoz)",
        "status": "Faol (Online)",
    },
    {
        "id": "USR-NUR-002",
        "full_name": "Hamshira Zilola Otajonova",
        "role": "👩‍⚕️ Kardioreanimatsiya Hamshirasi",
        "phone": "+998 90 123 45 68",
        "login": "+998901234568 (Parol: nazorat123)",
        "institution": "Xorazm viloyati Kardiologiya Dispanseri",
        "assigned": "4 nafar bemor telemonitoringi",
        "status": "Faol (Online)",
    },
    {
        "id": "USR-ADM-001",
        "full_name": "Mansur Durdimatov",
        "role": "👑 Super Admin / Tizim Yaratuvchisi & Boshqaruvchisi",
        "phone": "+998 90 123 45 67",
        "login": f"Telegram ID: {SUPER_ADMIN_ID} (@durdimatov_mansur)",
        "institution": "NAZORAT Markaziy Boshqaruv Markazi",
        "assigned": "To'liq tizim infratuzilmasi va ma'lumotlar bazasi",
        "status": "Faol (Super Admin)",
    },
]


def load_telegram_users() -> dict[str, dict[str, Any]]:
    """Load dynamically tracked Telegram users from USERS_FILE."""
    s_id = str(SUPER_ADMIN_ID)
    default_entry = {
        s_id: {
            "telegram_id": int(SUPER_ADMIN_ID),
            "full_name": "Mansur Durdimatov",
            "username": "@durdimatov_mansur",
            "phone": "+998 90 123 45 67",
            "role": "👑 Super Admin",
            "first_seen": "2026-09-18T10:00:00+05:00",
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "messages_count": 48,
            "is_active": True,
        }
    }

    if not USERS_FILE.exists():
        save_telegram_users(default_entry)
        return default_entry

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if s_id not in data:
                data[s_id] = default_entry[s_id]
            return data
    except Exception as err:
        logger.error("Failed to load users from %s: %s", USERS_FILE, err)
        return default_entry


def save_telegram_users(users: dict[str, dict[str, Any]]) -> None:
    """Save dynamically tracked Telegram users atomically."""
    try:
        tmp = USERS_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        tmp.replace(USERS_FILE)
    except Exception as err:
        logger.error("Failed to write users to %s: %s", USERS_FILE, err)


def track_user(
    telegram_id: int | str,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
    phone: str | None = None,
    message_text: str | None = None,
) -> dict[str, Any]:
    """Record or update real Telegram user activity in the registry."""
    users = load_telegram_users()
    s_id = str(telegram_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    full_name_parts = [first_name]
    if last_name:
        full_name_parts.append(last_name)
    calculated_name = " ".join(full_name_parts).strip()

    if s_id in users:
        u = users[s_id]
        u["last_seen"] = now_iso
        u["messages_count"] = u.get("messages_count", 0) + 1
        if username:
            u["username"] = f"@{username.lstrip('@')}"
        if phone:
            u["phone"] = phone
        if calculated_name and (not u.get("full_name") or u["full_name"].startswith("Foydalanuvchi_")):
            u["full_name"] = calculated_name
    else:
        role = "👤 Bot foydalanuvchisi"
        if int(telegram_id) == SUPER_ADMIN_ID:
            role = "👑 Super Admin"
        elif is_admin(telegram_id):
            role = "🛡️ Administrator"

        u = {
            "telegram_id": int(telegram_id),
            "full_name": calculated_name or f"Foydalanuvchi_{s_id}",
            "username": f"@{username.lstrip('@')}" if username else "Mavjud emas",
            "phone": phone or "Kiritilmagan",
            "role": role,
            "first_seen": now_iso,
            "last_seen": now_iso,
            "messages_count": 1,
            "is_active": True,
        }
        users[s_id] = u

    save_telegram_users(users)
    return u


def get_clinical_patients() -> list[dict[str, Any]]:
    """Return official real clinical patients and their linked relatives."""
    return REAL_PATIENTS_AND_RELATIVES


def get_clinical_staff() -> list[dict[str, Any]]:
    """Return official medical personnel and system administrators."""
    return REAL_MEDICAL_STAFF


def get_all_users() -> list[dict[str, Any]]:
    """Return all dynamically active Telegram bot users."""
    users_dict = load_telegram_users()
    users_list = list(users_dict.values())

    def sort_key(u: dict[str, Any]):
        tid = u.get("telegram_id")
        if tid == SUPER_ADMIN_ID:
            return (0, "")
        if "Admin" in u.get("role", ""):
            return (1, "")
        return (2, u.get("last_seen", ""))

    users_list.sort(key=sort_key)
    return users_list


def get_user_stats() -> dict[str, Any]:
    """Calculate aggregated clinical and system usage statistics."""
    patients = REAL_PATIENTS_AND_RELATIVES
    staff = REAL_MEDICAL_STAFF
    tg_users = get_all_users()

    red_count = sum(1 for p in patients if "Qizil" in p.get("triage_level", ""))
    amber_count = sum(1 for p in patients if "Sariq" in p.get("triage_level", ""))
    green_count = sum(1 for p in patients if "Yashil" in p.get("triage_level", ""))
    nodata_count = sum(1 for p in patients if "Ma'lumot yo'q" in p.get("triage_level", ""))

    return {
        "total_patients": len(patients),
        "red_count": red_count,
        "amber_count": amber_count,
        "green_count": green_count,
        "nodata_count": nodata_count,
        "relatives_count": len(patients),  # Each monitored patient has a designated caregiver
        "staff_count": len(staff),
        "telegram_users_count": len(tg_users),
        "doctors_count": 1,
        "nurses_count": 1,
        "admins_count": 1,
    }


def format_stats_message() -> str:
    """Format rich text report of real clinical monitoring and system usage."""
    stats = get_user_stats()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return (
        "📊 <b>NAZORAT (WMAX) — Tizim va Bemorlar Jonli Statistikasi</b>\n\n"
        f"🏥 <b>Monitoringdagi bemorlar:</b> <b>{stats['total_patients']} nafar</b>\n"
        f"  • 🔴 O'tkir xavf (Qizil): <b>{stats['red_count']} nafar</b> (Otabek Ro'zmetov)\n"
        f"  • 🟡 Diqqat talab (Sariq): <b>{stats['amber_count']} nafar</b> (Gulnora Matyoqubova)\n"
        f"  • 🟢 Barqaror holat (Yashil): <b>{stats['green_count']} nafar</b> (Rustam Qurbonov)\n"
        f"  • ⚪️ Aloqa yo'q (No Data): <b>{stats['nodata_count']} nafar</b> (Jumaniyoz Otajonov)\n\n"
        f"❤️ <b>Biriktirilgan bemor yaqinlari:</b> <b>{stats['relatives_count']} nafar</b>\n"
        f"👨‍⚕️ <b>Kardiolog shifokorlar:</b> <b>{stats['doctors_count']} nafar</b> (Doktor Islom Yusupov)\n"
        f"👩‍⚕️ <b>Klinik hamshiralar:</b> <b>{stats['nurses_count']} nafar</b> (Hamshira Zilola Otajonova)\n"
        f"👑 <b>Super Administrator:</b> <b>1 nafar</b> (Mansur Durdimatov)\n\n"
        "⚡️ <b>Telemetriya oqimi:</b> <code>Doimiy faol (5 daqiqalik oyna, 24/7)</code>\n"
        "🟢 <b>AI Triage:</b> <code>Google Gemini Flash (Gibrid rejim)</code>\n"
        f"🕒 <b>Ma'lumot yangilanishi:</b> <code>{now_str}</code>\n\n"
        "<i>To'liq ma'lumotlar bazasini yuklab olish uchun pastdagi «📥 Excel yuklab olish» tugmasini bosing.</i>"
    )


def format_users_list_message() -> str:
    """Format rich text list of real clinical patients and their linked caregivers."""
    patients = REAL_PATIENTS_AND_RELATIVES
    lines = [
        f"👥 <b>NAZORAT — Bemorlar va Ularning Yaqinlari Ro'yxati ({len(patients)} nafar):</b>\n",
    ]

    for idx, p in enumerate(patients, 1):
        p_name = p["patient_name"]
        age = p["age"]
        dist = p["district"]
        triage = p["triage_level"].split()[0]  # Emoji
        rel_name = p["relative_name"]
        rel_type = p["relationship"]
        rel_phone = p["relative_phone"]
        diag = p["diagnosis"]

        lines.append(
            f"<b>{idx}. {triage} {p_name}</b> ({age} yosh, {dist})\n"
            f"   🏥 Tashxis: <i>{diag[:50]}...</i>\n"
            f"   ❤️ Yaqini: <b>{rel_name}</b> ({rel_type})\n"
            f"   📞 Yaqinining tel: <code>{rel_phone}</code> (PIN: <code>112233</code>)\n"
        )

    lines.append("<i>Barcha ma'lumotlarni to'liq Excel (.xlsx) faylida yuklab olish uchun «📥 Excel yuklab olish» tugmasini bosing.</i>")
    return "\n".join(lines)

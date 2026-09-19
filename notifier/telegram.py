from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("wmax.notifier.telegram")

from .admin_store import (
    SUPER_ADMIN_ID,
    add_admin,
    get_all_admins,
    is_admin,
    is_super_admin,
    remove_admin,
)
from .ai_assistant import handle_user_query
from .api_manager import (
    SUPPORTED_MODELS,
    add_api_key,
    delete_api_key,
    delete_api_key_by_id,
    get_active_api_key,
    get_all_api_keys,
    get_model,
    get_system_mode,
    get_thresholds,
    mask_key,
    set_active_api_key,
    set_api_key,
    set_model,
    set_system_mode,
    set_threshold,
    test_gemini_api,
)
from .excel_exporter import generate_users_excel
from .user_tracker import (
    format_stats_message,
    format_users_list_message,
    get_all_users,
    get_user_stats,
    track_user,
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5174").rstrip("/")

# Admin interactive input session state {chat_id: state_name}
admin_input_state: dict[int | str, str] = {}


async def send_telegram_message(chat_id: int | str, text: str, reply_markup: dict | None = None) -> bool:
    """Send Telegram message or log it if token is not configured."""
    if not TELEGRAM_BOT_TOKEN:
        logger.info(
            "[TELEGRAM MOCK SEND] To chat_id=%s:\n%s",
            chat_id,
            text,
        )
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram message successfully sent to chat_id=%s", chat_id)
                return True
            logger.error(
                "Failed to send Telegram message to %s: HTTP %s - %s",
                chat_id,
                resp.status_code,
                resp.text,
            )
            return False
    except Exception as err:
        logger.exception("Exception sending Telegram message to %s: %s", chat_id, err)
        return False


async def send_telegram_document(chat_id: int | str, file_path: str | Path, caption: str = "") -> bool:
    """Send document (Excel, PDF, etc.) via Telegram sendDocument API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.info("[TELEGRAM MOCK SEND DOC] chat_id=%s, file=%s", chat_id, file_path)
        return True

    p = Path(file_path)
    if not p.exists():
        logger.error("File does not exist: %s", p)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            with open(p, "rb") as f:
                files = {"document": (p.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
                resp = await client.post(url, data=data, files=files)
                if resp.status_code == 200:
                    logger.info("Telegram document successfully sent to chat_id=%s: %s", chat_id, p.name)
                    return True
                logger.error("Failed to send document to %s: HTTP %s - %s", chat_id, resp.status_code, resp.text)
                return False
    except Exception as err:
        logger.exception("Exception sending document to %s: %s", chat_id, err)
        return False


def _persistent_reply_keyboard(user_id: int | str | None = None) -> dict:
    """Persistent reply keyboard — always visible at the bottom where user types.
    Strict Role-based separation:
    - Admins get a pure, dedicated Administrator Workspace (no patient/user buttons).
    - Ordinary users/relatives get clinical monitoring buttons."""
    if user_id and is_admin(user_id):
        rows = [
            [
                {"text": "📊 Tizim statistikasi"},
                {"text": "👥 Foydalanuvchilar"},
            ],
            [
                {"text": "📥 Excel yuklab olish"},
                {"text": "⚙️ Admin panel"},
            ],
        ]
    else:
        rows = [
            [
                {"text": "📊 Ko'rsatkichlar"},
                {"text": "☎️ Shifokor"},
                {"text": "❓ Yordam"},
            ],
        ]

    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


def format_admin_welcome(user_name: str, user_id: int | str) -> str:
    """Welcome greeting for system administrators."""
    is_super = is_super_admin(user_id)
    role_badge = "👑 <b>Super Admin</b>" if is_super else "🛡️ <b>Administrator</b>"
    stats = get_user_stats()

    return (
        f"Assalomu alaykum, <b>{user_name}</b>!\n\n"
        f"🏛 <b>NAZORAT (WMAX) — Administrator Boshqaruv Markazi</b>\n\n"
        f"👤 Sizning rolingiz: {role_badge}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        f"📊 <b>Klinik monitoring holati:</b>\n"
        f"• Monitoringdagi bemorlar: <b>{stats['total_patients']} nafar</b> (🔴 {stats['red_count']} ta og'ir)\n"
        f"• Bemor yaqinlari (vasiylar): <b>{stats['relatives_count']} nafar</b>\n"
        f"• Kardiolog shifokorlar: <b>{stats['doctors_count']} nafar</b>\n\n"
        "Quyidagi boshqaruv menyusidan foydalanishingiz mumkin:\n"
        "• <b>📊 Tizim statistikasi</b> — batafsil ko'rsatkichlar\n"
        "• <b>👥 Foydalanuvchilar</b> — bemorlar va ularning yaqinlari ro'yxati\n"
        "• <b>📥 Excel yuklab olish</b> — to'liq ma'lumotlarni 4 varaqli .xlsx da olish\n"
        "• <b>⚙️ Admin panel</b> — API kalitlar va klinik ostonalarni boshqarish"
    )


def format_admin_panel(user_id: int | str) -> tuple[str, dict]:
    """Format main interactive admin panel for Super Admin and appointed admins."""
    is_super = is_super_admin(user_id)
    role_badge = "👑 <b>Super Admin</b>" if is_super else "🛡️ <b>Administrator</b>"
    admins_cnt = len(get_all_admins())
    active_key = get_active_api_key()
    model = get_model()
    mode = get_system_mode()
    stats = get_user_stats()

    text = (
        f"⚙️ <b>WMAX — Boshqaruv paneli</b>\n\n"
        f"👤 Sizning rolingiz: {role_badge}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"🏥 Bemorlar: <b>{stats['total_patients']} nafar</b> (Yaqinlar: {stats['relatives_count']} ta)\n"
        f"🔴 Og'ir holatda: <b>{stats['red_count']} nafar</b> (Otabek Ro'zmetov)\n"
        f"🤖 AI Model: <code>{model}</code>\n"
        f"🔑 Gemini Kalit: <code>{mask_key(active_key)}</code>\n"
        f"⚡️ Tizim rejimi: <b>{mode.capitalize()}</b>\n"
        f"👥 Adminlar soni: <b>{admins_cnt} nafar</b>\n\n"
        f"<i>Quyidagi bo'limlardan birini tanlang:</i>"
    )

    markup = {
        "inline_keyboard": [
            [
                {"text": "📊 Tizim statistikasi", "callback_data": "adm_user_stats"},
                {"text": "👥 Foydalanuvchilar", "callback_data": "adm_user_list"},
            ],
            [
                {"text": "📥 Excel yuklab olish", "callback_data": "adm_export_excel"},
                {"text": "🔑 API kalitlar", "callback_data": "adm_keys"},
            ],
            [
                {"text": "⚙️ Klinik ostonalar", "callback_data": "adm_thresh"},
                {"text": "🤖 AI Model", "callback_data": "adm_models"},
            ],
            [
                {"text": "👥 Adminlar", "callback_data": "adm_list"},
                {"text": "📊 Tizim holati", "callback_data": "adm_sysinfo"},
            ],
            [
                {"text": "🔄 Yangilash", "callback_data": "adm_refresh"},
                {"text": "📖 Qo'llanma", "callback_data": "adm_help"},
            ],
        ]
    }
    return text, markup


def format_api_keys_panel() -> tuple[str, dict]:
    """Format API Key & Model management submenu with key list."""
    keys = get_all_api_keys()
    model = get_model()
    mode = get_system_mode()

    lines = [
        "🔑 <b>Gemini AI API Kalitlar Boshqaruvi</b>\n",
        f"📋 <b>Mavjud API kalitlar ({len(keys)} ta):</b>",
    ]
    if keys:
        for idx, k in enumerate(keys, 1):
            badge = "✅ (Faol / Active)" if k.get("is_active") else "◻️"
            name_str = f" <i>[{k.get('name')}]</i>" if k.get("name") else ""
            lines.append(f"{idx}. {badge} <code>{mask_key(k['key'])}</code>{name_str}")
    else:
        lines.append("<i>Hech qanday API kalit mavjud emas.</i>")

    lines.append(f"\n🤖 <b>Joriy model:</b> <code>{model}</code>")
    lines.append(f"⚡️ <b>Tizim rejimi:</b> <b>{mode.capitalize()}</b>")
    lines.append(
        "\n<i>O'chirish uchun «🗑 Kalitni o'chirish» tugmasini bosing — kalitlar ro'yxatidan tanlab o'chiriladi.</i>"
    )

    markup = {
        "inline_keyboard": [
            [
                {"text": "⚡️ Ulanishni tekshirish (Ping)", "callback_data": "adm_testkey"},
            ],
            [
                {"text": "➕ Yangi kalit kiritish", "callback_data": "adm_setkey_prompt"},
                {"text": f"🗑 Kalitni o'chirish ({len(keys)})", "callback_data": "adm_delkey_menu"},
            ],
            [
                {"text": "🔘 Faol kalitni tanlash", "callback_data": "adm_selectkey_menu"},
                {"text": "🤖 Model tanlash", "callback_data": "adm_models"},
            ],
            [
                {"text": f"🔄 Rejim: {mode.capitalize()}", "callback_data": "adm_toggle_mode"},
                {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
            ],
        ]
    }
    return "\n".join(lines), markup


def format_delete_keys_panel() -> tuple[str, dict]:
    """Format submenu for selecting which API key to delete."""
    keys = get_all_api_keys()
    if not keys:
        text = "🗑 <b>API kalitlar ro'yxati bo'sh</b>\n\nO'chirish uchun hech qanday kalit mavjud emas."
        markup = {"inline_keyboard": [[{"text": "⬅️ Orqaga", "callback_data": "adm_keys"}]]}
        return text, markup

    text = (
        "🗑 <b>O'chirish uchun API kalitni tanlang:</b>\n\n"
        f"Tizimda <b>{len(keys)} ta</b> API kalit mavjud.\n"
        "Qaysi kalitni o'chirmoqchisiz? Quyidagi ro'yxatdan tanlang:"
    )

    rows = []
    for idx, k in enumerate(keys, 1):
        active_tag = " [Faol]" if k.get("is_active") else ""
        btn_text = f"🗑 {idx}. {mask_key(k['key'])}{active_tag}"
        rows.append([{"text": btn_text, "callback_data": f"adm_delkey_{k['id']}"}])

    rows.append([{"text": "⬅️ Orqaga", "callback_data": "adm_keys"}])
    return text, {"inline_keyboard": rows}


def format_select_active_key_panel() -> tuple[str, dict]:
    """Format submenu for selecting which API key should be active."""
    keys = get_all_api_keys()
    if not keys:
        text = "🔘 <b>API kalitlar ro'yxati bo'sh</b>\n\nIltimos, avval kalit qo'shing."
        markup = {"inline_keyboard": [[{"text": "⬅️ Orqaga", "callback_data": "adm_keys"}]]}
        return text, markup

    text = (
        "🔘 <b>Faol API kalitni tanlash:</b>\n\n"
        "AI so'rovlari uchun qaysi kalit ishlatilishini xohlaysiz? Kerakli kalit ustiga bosing:"
    )

    rows = []
    for idx, k in enumerate(keys, 1):
        prefix = "✅ " if k.get("is_active") else "◻️ "
        btn_text = f"{prefix}{idx}. {mask_key(k['key'])}"
        rows.append([{"text": btn_text, "callback_data": f"adm_setactive_{k['id']}"}])

    rows.append([{"text": "⬅️ Orqaga", "callback_data": "adm_keys"}])
    return text, {"inline_keyboard": rows}


def format_thresholds_panel() -> tuple[str, dict]:
    """Format clinical thresholds management submenu."""
    t = get_thresholds()
    spo2 = t.get("spo2_min", 90.0)
    hr = t.get("hr_max", 100.0)
    temp = t.get("temp_max", 37.8)
    rr = t.get("rr_max", 24.0)

    text = (
        f"⚙️ <b>Klinik Ostonalar va Me'yorlar (Triage Thresholds)</b>\n\n"
        f"• 🫁 <b>SpO₂ minimal:</b> <code>{spo2}%</code> (past bo'lsa subkompensatsiya / sariq)\n"
        f"• ❤️ <b>Puls maksimal:</b> <code>{hr} bpm</code> (yuqori bo'lsa taxikardiya)\n"
        f"• 🌡 <b>Harorat maksimal:</b> <code>{temp}°C</code> (gipertermiya / subfebril)\n"
        f"• 🌬 <b>Nafas maksimal:</b> <code>{rr}/daq</code> (taxipnoe)\n\n"
        f"<i>Tugmalar orqali tezkor o'zgartirishingiz yoki <code>/setthreshold &lt;param&gt; &lt;qiymat&gt;</code> (masalan: <code>/setthreshold spo2 92</code>) yozishingiz mumkin.</i>"
    )

    markup = {
        "inline_keyboard": [
            [
                {"text": "🫁 SpO₂ -1", "callback_data": "adm_th_spo2_-1"},
                {"text": "🫁 SpO₂ +1", "callback_data": "adm_th_spo2_1"},
            ],
            [
                {"text": "❤️ Puls -5", "callback_data": "adm_th_hr_-5"},
                {"text": "❤️ Puls +5", "callback_data": "adm_th_hr_5"},
            ],
            [
                {"text": "🌡 Temp -0.2", "callback_data": "adm_th_temp_-0.2"},
                {"text": "🌡 Temp +0.2", "callback_data": "adm_th_temp_0.2"},
            ],
            [
                {"text": "🌬 Nafas -1", "callback_data": "adm_th_rr_-1"},
                {"text": "🌬 Nafas +1", "callback_data": "adm_th_rr_1"},
            ],
            [
                {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
            ],
        ]
    }
    return text, markup


def format_models_panel() -> tuple[str, dict]:
    """Format AI model switcher submenu."""
    current = get_model()
    text = (
        f"🤖 <b>AI Modelini Tanlash</b>\n\n"
        f"Joriy faol model: <b>{current}</b>\n\n"
        f"Quyidagi modellardan birini tanlang:\n"
        f"• <b>gemini-3.5-flash-lite</b> — tezkor va tejamkor (tavsiya etiladi)\n"
        f"• <b>gemini-2.5-flash</b> — yuqori aniqlik\n"
        f"• <b>gemini-1.5-flash</b> — barqaror\n"
        f"• <b>gemini-1.5-pro</b> — chuqur klinik tahlil"
    )

    rows = []
    for m in SUPPORTED_MODELS:
        prefix = "✅ " if m == current else "◻️ "
        rows.append([{"text": f"{prefix}{m}", "callback_data": f"adm_setmod_{m}"}])

    rows.append([
        {"text": "⬅️ API menyusi", "callback_data": "adm_keys"},
        {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
    ])

    return text, {"inline_keyboard": rows}


def format_admins_panel(user_id: int | str) -> tuple[str, dict]:
    """Format administrators management submenu."""
    admins = get_all_admins()
    lines = [f"👥 <b>Administratorlar ro'yxati ({len(admins)} nafar):</b>\n"]
    for a in admins:
        role = "👑 Super Admin" if a.get("role") == "super_admin" else "🛡️ Admin"
        lines.append(f"• <b>{a.get('name')}</b> — {role}\n  ID: <code>{a.get('id')}</code>")

    lines.append(
        "\n<i>Yangi admin qo'shish uchun tugmani bosing yoki <code>/addadmin &lt;id&gt; [ism]</code> yozing.</i>"
    )

    markup = {
        "inline_keyboard": [
            [
                {"text": "➕ Admin qo'shish", "callback_data": "adm_addadmin_prompt"},
                {"text": "🔄 Yangilash", "callback_data": "adm_list"},
            ],
            [
                {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
            ],
        ]
    }
    return "\n".join(lines), markup


def format_admin_help() -> tuple[str, dict]:
    text = (
        "📖 <b>NAZORAT — Admin buyruqlari qo'llanmasi:</b>\n\n"
        "📊 <b>Foydalanuvchilar va Statistika:</b>\n"
        "• <code>/stats</code> — Tizim jonli statistikasi\n"
        "• <code>/users</code> — Foydalanuvchilar va yaqinlar ro'yxati\n"
        "• <code>/excel</code> — To'liq bazani Excel (.xlsx) formatida yuklab olish\n\n"
        "🔑 <b>API kalit va AI boshqaruvi:</b>\n"
        "• <code>/setkey &lt;kalit&gt;</code> — Yangi Gemini API kalitini o'rnatish\n"
        "• <code>/delkey</code> — Maxsus API kalitni tozalash\n"
        "• <code>/testkey</code> — API ulanishini tekshirish (Ping)\n"
        "• <code>/setmodel &lt;nom&gt;</code> — Model almashtirish (masalan: gemini-2.5-flash)\n"
        "• <code>/mode &lt;hybrid|offline&gt;</code> — AI rejimini o'zgartirish\n\n"
        "⚙️ <b>Klinik ostonalar:</b>\n"
        "• <code>/setthreshold &lt;param&gt; &lt;qiymat&gt;</code> — Ostonani yangilash\n"
        "  (Masalan: <code>/setthreshold spo2 92</code>, <code>/setthreshold hr 110</code>)\n\n"
        "👥 <b>Adminlar boshqaruvi:</b>\n"
        "• <code>/addadmin &lt;id&gt; [ism]</code> — Yangi admin qo'shish\n"
        "• <code>/deladmin &lt;id&gt;</code> — Adminni o'chirish\n"
        "• <code>/admins</code> — Adminlar ro'yxati\n\n"
        "📊 <b>Tizim:</b>\n"
        "• <code>/sysinfo</code> — Server va telemetriya holati\n"
        "• <code>/broadcast &lt;xabar&gt;</code> — Barcha adminlarga rasmiy xabar"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "⬅️ Asosiy panel", "callback_data": "adm_main"}]
        ]
    }
    return text, markup


def format_sysinfo() -> tuple[str, dict]:
    """Format system diagnostics report with action buttons."""
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    admins_cnt = len(get_all_admins())
    model = get_model()
    mode = get_system_mode()
    has_key = bool(get_active_api_key())
    key_status = "O'rnatilgan ✅" if has_key else "O'rnatilmagan ❌"

    text = (
        f"📊 <b>WMAX — Tizim holati</b>\n\n"
        f"🟢 API Server: <code>Faol (Online)</code>\n"
        f"🟢 AI Assistent: <code>{model} ({mode.capitalize()})</code>\n"
        f"🔑 AI Kalit: <code>{key_status}</code>\n"
        f"🟢 Telemetriya oqimi: <code>Sinxronizatsiyada</code>\n"
        f"👥 Ro'yxatdagi adminlar: <b>{admins_cnt} nafar</b>\n"
        f"👑 Super Admin ID: <code>{SUPER_ADMIN_ID}</code>\n"
        f"🕒 Server vaqti: <code>{now_str}</code>"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "⚡️ Test AI API", "callback_data": "adm_testkey"}],
            [{"text": "⬅️ Asosiy panel", "callback_data": "adm_main"}],
        ]
    }
    return text, markup


# ---- MESSAGE TEMPLATES ----

def format_relative_alert(patient_name: str, access_token: str, level: str) -> str:
    """Relative message template — clinical diagnosis is never disclosed."""
    link = f"{PUBLIC_BASE_URL}/r/{access_token}"
    if level == "red":
        prefix = "\U0001f6a8 <b>DIQQAT: ZUDLIK BILAN E'TIBOR TALAB ETILADI</b>"
    elif level == "amber":
        prefix = "\u26a0\ufe0f <b>Eslatma</b>"
    else:
        prefix = "\u2139\ufe0f <b>Ma'lumot</b>"

    return (
        f"{prefix}\n\n"
        f"Hurmatli fuqaro, <b>{patient_name}</b>ning salomatlik ko'rsatkichlarida e'tibor talab qiluvchi o'zgarishlar kuzatilmoqda.\n\n"
        f"Holatni ko'rish: <a href=\"{link}\">{link}</a>"
    )


def format_doctor_alert(
    patient_name: str,
    age: int,
    district: str,
    diagnosis: str,
    reason: str,
    triggered_params: dict[str, Any],
    patient_id: str,
) -> str:
    """Doctor alert template — rich structured format."""
    params_lines = []
    param_icons = {
        "spo2": "\u2b07 SpO\u2082",
        "hr_mean": "\u2b06 Puls",
        "skin_temp": "\U0001f321 Harorat",
        "rr": "\U0001f32c Nafas",
        "rmssd": "\u2b07 HRV",
    }
    for k, v in triggered_params.items():
        icon_label = param_icons.get(k, k)
        params_lines.append(f"  {icon_label}: <b>{v}</b>")

    params_str = "\n".join(params_lines) if params_lines else "  Ma'lumot yo'q"

    return (
        f"\U0001f6a8 <b>WMAX: QIZIL SIGNAL</b>\n\n"
        f"\U0001f464 <b>Bemor:</b> {patient_name} ({age} yosh)\n"
        f"\U0001f4cd {district}\n"
        f"\U0001f3e5 <b>Tashxis:</b> {diagnosis}\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"<b>Ko'rsatkichlar:</b>\n{params_str}\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f4cb <b>Sabab:</b> {reason or 'Chetlanishlar aniqlandi'}\n\n"
        f"Aktiv chaqiruv vazifasi yaratildi (24 soatlik taymer)."
    )


def format_active_call_reminder(patient_name: str, due_in_hours: int) -> str:
    return (
        f"\u26a0\ufe0f <b>ESLATMA: AKTIV CHAQIRUV</b>\n\n"
        f"Bemor <b>{patient_name}</b> bo'yicha belgilangan 24 soatlik patronaj muddati "
        f"<b>{due_in_hours} soatdan so'ng</b> yakunlanadi.\n"
        f"Iltimos, tashrifni amalga oshiring va tizimda tasdiqlang."
    )


def format_overdue_escalation(patient_name: str, doctor_name: str | None, district: str) -> str:
    return (
        f"\u26d4 <b>ESKALATSIYA (MUDDATI O'TDI)</b>\n\n"
        f"Bemor <b>{patient_name}</b> ({district}) bo'yicha 24 soatlik aktiv chaqiruv "
        f"o'z vaqtida tasdiqlanmadi.\n"
        f"Mas'ul: {doctor_name or 'Biriktirilgan shifokor'}"
    )


def format_no_data_alert(patient_name: str, access_token: str) -> str:
    link = f"{PUBLIC_BASE_URL}/r/{access_token}"
    return (
        f"\u2139\ufe0f <b>Soat aloqasi yo'q</b>\n\n"
        f"Bemor <b>{patient_name}</b>ning aqlli soati 45 daqiqadan beri ma'lumot yubormayapti.\n"
        f"Iltimos, soat qo'lga taqilgani va quvvati borligini tekshirib ko'ring.\n\n"
        f"Holat: <a href=\"{link}\">{link}</a>"
    )


def format_daily_summary(patient_name: str, vitals: dict) -> str:
    """Morning daily summary message."""
    hr = vitals.get("hr", "—")
    spo2 = vitals.get("spo2", "—")
    sleep = vitals.get("sleep_hours", "—")
    level = vitals.get("level", "green")

    level_emoji = {
        "green": "\u2705 YASHIL (Barqaror)",
        "amber": "\u26a0\ufe0f SARIQ (E'tibor)",
        "red": "\U0001f6a8 QIZIL (Xavfli)",
        "no_data": "\U0001f4e1 Ma'lumot yo'q",
    }
    status = level_emoji.get(level, level)

    return (
        f"\U0001f305 <b>Xayrli tong!</b> {patient_name} bugungi holati:\n\n"
        f"\u2764\ufe0f Puls: <b>{hr} bpm</b>\n"
        f"\U0001f9ec SpO\u2082: <b>{spo2}%</b>\n"
        f"\U0001f319 Uyqu: <b>{sleep} soat</b>\n\n"
        f"\U0001f4ca Holat: <b>{status}</b>"
    )


def format_status_response(patient_name: str, vitals: dict) -> str:
    """Inline clinical status response with medical terms and Sentence case."""
    hr = vitals.get("hr", "—")
    spo2 = vitals.get("spo2", "—")
    temp = vitals.get("skin_temp", "—")
    rr = vitals.get("rr", "—")
    sleep = vitals.get("sleep_hours", "—")
    steps = vitals.get("steps", "—")

    return (
        f"📋 <b>{patient_name} — Hozirgi klinik ko'rsatkichlar</b>\n\n"
        f"❤️ Yurak urishi (ChSS / Puls): <b>{hr} bpm</b> (fiziologik me'yor: 60-90)\n"
        f"🫁 Qondagi kislorod (SpO₂): <b>{spo2}%</b> (klinik me'yor: 95-100%)\n"
        f"🌡 Tana harorati: <b>{temp}°C</b> (me'yor: 36.0-37.2)\n"
        f"🌬 Nafas chastotasi (ChDD): <b>{rr}/daq</b> (me'yor: 12-20)\n"
        f"🌙 Tungi uyqu: <b>{sleep} soat</b> (klinik norma: 7-8 soat)\n"
        f"👟 Kunlik harakat: <b>{steps} qadam</b>\n\n"
        f"🕒 Yangilangan: hozir"
    )


# ---- WELCOME & HELP MESSAGES ----

WELCOME_TEXT = (
    "Assalomu alaykum, <b>{user_name}</b>! 🏥\n\n"
    "Bu <b>WMAX</b> — Masofaviy klinik telemonitoring va erta ogohlantirish tizimining rasmiy boti.\n\n"
    "📱 <b>Imkoniyatlar:</b>\n"
    "• Bemor portalini to'g'ridan-to'g'ri Telegram ichida ochish\n"
    "• Real vaqt klinik ogohlantirishlari\n"
    "• AI assistenti orqali 3 tilda (Uz/Ru/En) savol-javob\n"
    "• Shifokor bilan tezkor aloqa\n\n"
    "💬 <b>Buyruqlar:</b>\n"
    "/status — Joriy klinik ko'rsatkichlar\n"
    "/help — Yordam va qo'llanma\n\n"
    "🆔 Sizning Telegram Chat ID: <code>{chat_id}</code>"
)

HELP_TEXT = (
    "❓ <b>WMAX Bot — Yordam va imkoniyatlar</b>\n\n"
    "<b>Asosiy buyruqlar:</b>\n"
    "/start — Botni ishga tushirish\n"
    "/status — Bemorning joriy klinik ko'rsatkichlari\n"
    "/help — Ushbu yordam sahifasi\n\n"
    "<b>3 tilda erkin muloqot (AI assistenti):</b>\n"
    "Botga O'zbekcha, Ruscha yoki Inglizcha savollaringizni erkin yozishingiz mumkin (masalan: <i>«Dadamning pulsi yaxshimi?»</i> yoki <i>«How is the patient?»</i>).\n\n"
    "<b>Klinik signallar:</b>\n"
    "🚨 Qizil signal — o'tkir dekompensatsiya xavfi\n"
    "⚠️ Sariq signal — subkompensatsiya, dinamik kuzatuv\n"
    "ℹ️ Telemetriya uzilgan — 45 daqiqadan ortiq\n\n"
    "<b>Mini App:</b>\n"
    "Pastki chap burchakdagi <b>📱 Bemor portali</b> tugmasini bosing — barcha grafiklar va kardiolog tavsiyalari ochiladi."
)


# ---- DEMO VITALS (for status command when no DB is connected) ----

DEMO_VITALS = {
    "hr": 86, "spo2": 92, "skin_temp": 36.6, "rr": 19,
    "sleep_hours": 5.4, "steps": 1840, "level": "amber",
}


async def answer_callback_query(callback_query_id: str, text: str = "") -> None:
    """Answer a callback query to remove loading indicator."""
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"callback_query_id": callback_query_id, "text": text})
    except Exception:
        pass


async def poll_telegram_messages() -> None:
    """Poll Telegram updates: /start, /status, /help, and callback buttons."""
    if not TELEGRAM_BOT_TOKEN:
        logger.info("Telegram bot token not configured. Skipping poll.")
        return

    logger.info("Telegram polling started for bot @WMAX_uz_bot...")
    offset = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    async with httpx.AsyncClient(timeout=25.0) as client:
        while True:
            try:
                resp = await client.get(url, params={"offset": offset, "timeout": 15})
                if resp.status_code != 200:
                    await asyncio.sleep(3)
                    continue

                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    # Handle callback queries (inline button presses)
                    callback = update.get("callback_query")
                    if callback:
                        cb_data = callback.get("data", "")
                        cb_chat_id = callback["message"]["chat"]["id"]
                        cb_user = callback.get("from", {}).get("first_name", "Foydalanuvchi")

                        await answer_callback_query(callback["id"])

                        if cb_data == "cmd_status":
                            status_text = format_status_response("Otabek Rahimov", DEMO_VITALS)
                            await send_telegram_message(cb_chat_id, status_text)
                        elif cb_data == "cmd_help":
                            await send_telegram_message(cb_chat_id, HELP_TEXT)
                        elif cb_data == "cmd_call_doctor":
                            await send_telegram_message(
                                cb_chat_id,
                                "\u260e\ufe0f <b>Shifokor bilan bog'lanish:</b>\n\n"
                                "\U0001f468\u200d\u2695\ufe0f Dr. Bahrom Alimov\n"
                                "\U0001f4de +998 90 123 45 67\n"
                                "\U0001f4cd Xorazm viloyati Kardiologiya Dispanseri\n\n"
                                "Ish vaqti: 08:00 \u2014 17:00 (Du-Ju)",
                            )
                        elif cb_data == "cmd_main_menu":
                            welcome = WELCOME_TEXT.format(user_name=cb_user, chat_id=cb_chat_id)
                            await send_telegram_message(cb_chat_id, welcome)
                        elif cb_data == "adm_main":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            text_p, markup_p = format_admin_panel(cb_chat_id)
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_user_stats":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            stats_text = format_stats_message()
                            markup_stats = {
                                "inline_keyboard": [
                                    [
                                        {"text": "👥 Foydalanuvchilar ro'yxati", "callback_data": "adm_user_list"},
                                        {"text": "📥 Excel yuklab olish", "callback_data": "adm_export_excel"},
                                    ],
                                    [
                                        {"text": "🔄 Yangilash", "callback_data": "adm_user_stats"},
                                        {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
                                    ],
                                ]
                            }
                            await send_telegram_message(cb_chat_id, stats_text, markup_stats)
                        elif cb_data == "adm_user_list":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            list_text = format_users_list_message()
                            markup_list = {
                                "inline_keyboard": [
                                    [
                                        {"text": "📥 To'liq Excel yuklab olish", "callback_data": "adm_export_excel"},
                                    ],
                                    [
                                        {"text": "📊 Statistika", "callback_data": "adm_user_stats"},
                                        {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
                                    ],
                                ]
                            }
                            await send_telegram_message(cb_chat_id, list_text, markup_list)
                        elif cb_data == "adm_export_excel":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            await send_telegram_message(cb_chat_id, "⏳ <i>Excel (.xlsx) hisoboti tayyorlanmoqda...</i>")
                            try:
                                file_path = generate_users_excel()
                                caption = (
                                    "📊 <b>NAZORAT (WMAX) — Foydalanuvchilar va Bemorlar Hisoboti</b>\n\n"
                                    "Ushbu jadvalda barcha ro'yxatga olingan foydalanuvchilar, telefon raqamlari, "
                                    "rollari, biriktirilgan bemorlari, qarindoshlik darajasi va kasallik tashxislari "
                                    "to'liq jamlangan."
                                )
                                sent_doc = await send_telegram_document(cb_chat_id, file_path, caption)
                                if not sent_doc:
                                    await send_telegram_message(cb_chat_id, "❌ Excel faylini yuborishda xatolik yuz berdi.")
                            except Exception as exc:
                                logger.exception("Error generating/sending excel: %s", exc)
                                await send_telegram_message(cb_chat_id, f"❌ Xatolik yuz berdi: {exc}")
                        elif cb_data == "adm_keys":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            text_p, markup_p = format_api_keys_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_thresh":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            text_p, markup_p = format_thresholds_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_models":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            text_p, markup_p = format_models_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_list":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            text_p, markup_p = format_admins_panel(cb_chat_id)
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_sysinfo":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            text_s, markup_s = format_sysinfo()
                            await send_telegram_message(cb_chat_id, text_s, markup_s)
                        elif cb_data == "adm_help":
                            text_p, markup_p = format_admin_help()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_refresh":
                            text_p, markup_p = format_admin_panel(cb_chat_id)
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_testkey":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            await send_telegram_message(cb_chat_id, "⏳ <i>Gemini API ulanishi tekshirilmoqda...</i>")
                            ok, lat, test_msg = await test_gemini_api()
                            icon = "✅" if ok else "❌"
                            res_text = (
                                f"{icon} <b>Gemini API ulanish testi:</b>\n\n"
                                f"• Holat: {test_msg}\n"
                                f"• Model: <code>{get_model()}</code>\n"
                                f"• Kalit: <code>{mask_key(get_active_api_key())}</code>\n"
                                f"• Javob vaqti: <b>{lat}s</b>"
                            )
                            markup_res = {
                                "inline_keyboard": [
                                    [{"text": "⚡️ Qayta tekshirish", "callback_data": "adm_testkey"}],
                                    [{"text": "⬅️ API menyusi", "callback_data": "adm_keys"}, {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"}],
                                ]
                            }
                            await send_telegram_message(cb_chat_id, res_text, markup_res)
                        elif cb_data == "adm_setkey_prompt":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            admin_input_state[cb_chat_id] = "awaiting_api_key"
                            await send_telegram_message(
                                cb_chat_id,
                                "🔑 <b>Yangi Gemini API kalitini kiriting:</b>\n\n"
                                "Google AI Studio kalitingizni shu yerga oddiy xabar sifatida yuboring.\n"
                                "Masalan: <code>AIzaSy...</code> yoki <code>AQ.Ab8RN...</code>\n\n"
                                "<i>Bekor qilish uchun /cancel deb yozing.</i>",
                            )
                        elif cb_data == "adm_delkey_menu":
                            if not is_super_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Faqat Super Admin API kalitlarni o'chira oladi.")
                                continue
                            text_p, markup_p = format_delete_keys_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_selectkey_menu":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            text_p, markup_p = format_select_active_key_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data.startswith("adm_delkey_"):
                            if not is_super_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Faqat Super Admin API kalitni o'chira oladi.")
                                continue
                            target_id = cb_data.replace("adm_delkey_", "").strip()
                            ok, msg_res = delete_api_key_by_id(target_id)
                            await send_telegram_message(cb_chat_id, msg_res)
                            text_p, markup_p = format_api_keys_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data.startswith("adm_setactive_"):
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            target_id = cb_data.replace("adm_setactive_", "").strip()
                            ok, msg_res = set_active_api_key(target_id)
                            await send_telegram_message(cb_chat_id, msg_res)
                            text_p, markup_p = format_api_keys_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_toggle_mode":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            cur_mode = get_system_mode()
                            new_mode = "offline" if cur_mode == "hybrid" else "hybrid"
                            set_system_mode(new_mode)
                            await send_telegram_message(cb_chat_id, f"🔄 Tizim rejimi o'zgartirildi: <b>{new_mode.capitalize()}</b>")
                            text_p, markup_p = format_api_keys_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data.startswith("adm_setmod_"):
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            chosen_mod = cb_data.replace("adm_setmod_", "").strip()
                            set_model(chosen_mod)
                            await send_telegram_message(cb_chat_id, f"✅ AI modeli o'zgartirildi: <b>{chosen_mod}</b>")
                            text_p, markup_p = format_models_panel()
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data.startswith("adm_th_"):
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            parts = cb_data.split("_")
                            if len(parts) >= 4:
                                p_name = parts[2]
                                delta = float(parts[3])
                                cur_th = get_thresholds()
                                target_key = {
                                    "spo2": "spo2_min",
                                    "hr": "hr_max",
                                    "temp": "temp_max",
                                    "rr": "rr_max",
                                }.get(p_name, f"{p_name}_max")
                                old_v = cur_th.get(target_key, 0.0)
                                new_v = round(old_v + delta, 1)
                                set_threshold(p_name, new_v)
                                text_p, markup_p = format_thresholds_panel()
                                await send_telegram_message(cb_chat_id, text_p, markup_p)
                        elif cb_data == "adm_addadmin_prompt":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            admin_input_state[cb_chat_id] = "awaiting_admin_id"
                            await send_telegram_message(
                                cb_chat_id,
                                "👥 <b>Yangi admin qo'shish:</b>\n\n"
                                "Foydalanuvchining Telegram ID raqamini (yoki ID va ismini) yuboring:\n"
                                "Masalan: <code>123456789 Dr. Sardor</code>\n\n"
                                "<i>Bekor qilish uchun /cancel deb yozing.</i>",
                            )
                        continue

                    # Handle text messages
                    msg = update.get("message") or update.get("edited_message")
                    if not msg:
                        continue

                    chat_id = msg["chat"]["id"]
                    user_name = msg.get("from", {}).get("first_name", "Foydalanuvchi")
                    last_name = msg.get("from", {}).get("last_name")
                    username = msg.get("from", {}).get("username")
                    raw_text = (msg.get("text") or "").strip()
                    text = raw_text.lower()

                    # Real-time activity and user registry tracking
                    contact = msg.get("contact")
                    phone = contact.get("phone_number") if contact else None
                    track_user(
                        telegram_id=chat_id,
                        first_name=user_name,
                        last_name=last_name,
                        username=username,
                        phone=phone,
                        message_text=raw_text,
                    )

                    logger.info("Received Telegram message from '%s' (chat_id=%s): %s", user_name, chat_id, text)

                    # Check for active stateful admin input
                    if is_admin(chat_id) and chat_id in admin_input_state:
                        state = admin_input_state.pop(chat_id)
                        if text in ("/cancel", "cancel", "bekor"):
                            await send_telegram_message(chat_id, "❌ Amal bekor qilindi.", _persistent_reply_keyboard(chat_id))
                            continue
                        if state == "awaiting_api_key":
                            new_key = raw_text.strip()
                            await send_telegram_message(chat_id, "⏳ <i>Yangi API kalit tekshirilmoqda...</i>")
                            ok, lat, test_msg = await test_gemini_api(api_key=new_key)
                            set_api_key(new_key)
                            if ok:
                                await send_telegram_message(
                                    chat_id,
                                    f"✅ <b>Yangi Gemini API kaliti saqlandi va faollashtirildi!</b>\n\n"
                                    f"• Kalit: <code>{mask_key(new_key)}</code>\n"
                                    f"• Model: <b>{get_model()}</b>\n"
                                    f"• Natija: {test_msg}\n"
                                    f"• Javob vaqti: {lat}s",
                                )
                            else:
                                await send_telegram_message(
                                    chat_id,
                                    f"⚠️ <b>API kalit saqlandi, ammo ulanish testida xatolik aniqlandi:</b>\n\n"
                                    f"• Kalit: <code>{mask_key(new_key)}</code>\n"
                                    f"• Xatolik: {test_msg}\n\n"
                                    f"<i>Kalitni qayta tekshirib ko'rishingiz yoki yangisini kiritishingiz mumkin.</i>",
                                )
                            text_p, markup_p = format_api_keys_panel()
                            await send_telegram_message(chat_id, text_p, markup_p)
                            continue
                        elif state == "awaiting_admin_id":
                            parts = raw_text.split(maxsplit=1)
                            target_id = parts[0]
                            target_name = parts[1] if len(parts) > 1 else f"Admin_{target_id}"
                            success, msg_res = add_admin(target_id, target_name)
                            await send_telegram_message(chat_id, msg_res)
                            if success:
                                try:
                                    await send_telegram_message(
                                        target_id,
                                        f"🎉 Assalomu alaykum, <b>{target_name}</b>!\n\n"
                                        f"Sizga <b>NAZORAT (WMAX)</b> tizimida administratorlik huquqi berildi.\n"
                                        f"Admin panelni ochish uchun /admin buyrug'ini yuboring.",
                                        _persistent_reply_keyboard(target_id),
                                    )
                                except Exception:
                                    pass
                            text_p, markup_p = format_admins_panel(chat_id)
                            await send_telegram_message(chat_id, text_p, markup_p)
                            continue

                    if text in ("/cancel", "cancel"):
                        admin_input_state.pop(chat_id, None)
                        await send_telegram_message(chat_id, "❌ Hech qanday faol buyruq yo'q.", _persistent_reply_keyboard(chat_id))
                    elif text in ("/start", "/start@wmax_uz_bot"):
                        if is_admin(chat_id):
                            welcome = format_admin_welcome(user_name, chat_id)
                            text_p, markup_p = format_admin_panel(chat_id)
                            await send_telegram_message(chat_id, welcome, _persistent_reply_keyboard(chat_id))
                            await send_telegram_message(chat_id, text_p, markup_p)
                        else:
                            welcome = WELCOME_TEXT.format(user_name=user_name, chat_id=chat_id)
                            await send_telegram_message(chat_id, welcome, _persistent_reply_keyboard(chat_id))
                    elif text in ("📊 tizim statistikasi", "tizim statistikasi", "/stats"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            stats_text = format_stats_message()
                            markup_stats = {
                                "inline_keyboard": [
                                    [
                                        {"text": "👥 Foydalanuvchilar ro'yxati", "callback_data": "adm_user_list"},
                                        {"text": "📥 Excel yuklab olish", "callback_data": "adm_export_excel"},
                                    ],
                                    [
                                        {"text": "🔄 Yangilash", "callback_data": "adm_user_stats"},
                                        {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
                                    ],
                                ]
                            }
                            await send_telegram_message(chat_id, stats_text, markup_stats)
                    elif text in ("👥 foydalanuvchilar", "foydalanuvchilar", "/users"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            list_text = format_users_list_message()
                            markup_list = {
                                "inline_keyboard": [
                                    [
                                        {"text": "📥 To'liq Excel yuklab olish", "callback_data": "adm_export_excel"},
                                    ],
                                    [
                                        {"text": "📊 Statistika", "callback_data": "adm_user_stats"},
                                        {"text": "⬅️ Asosiy panel", "callback_data": "adm_main"},
                                    ],
                                ]
                            }
                            await send_telegram_message(chat_id, list_text, markup_list)
                    elif text in ("📥 excel yuklab olish", "excel yuklab olish", "/excel", "/export"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            await send_telegram_message(chat_id, "⏳ <i>Excel (.xlsx) hisoboti tayyorlanmoqda...</i>")
                            try:
                                file_path = generate_users_excel()
                                caption = (
                                    "📊 <b>NAZORAT (WMAX) — Foydalanuvchilar va Bemorlar Hisoboti</b>\n\n"
                                    "Ushbu jadvalda barcha ro'yxatga olingan foydalanuvchilar, telefon raqamlari, "
                                    "rollari, biriktirilgan bemorlari, qarindoshlik darajasi va kasallik tashxislari "
                                    "to'liq jamlangan."
                                )
                                sent_doc = await send_telegram_document(chat_id, file_path, caption)
                                if not sent_doc:
                                    await send_telegram_message(chat_id, "❌ Excel faylini yuborishda xatolik yuz berdi.")
                            except Exception as exc:
                                logger.exception("Error generating/sending excel: %s", exc)
                                await send_telegram_message(chat_id, f"❌ Xatolik yuz berdi: {exc}")
                    elif text in ("/status", "/status@wmax_uz_bot", "📊 ko'rsatkichlar", "ko'rsatkichlar"):
                        if is_admin(chat_id):
                            text_p, markup_p = format_admin_panel(chat_id)
                            await send_telegram_message(
                                chat_id,
                                "ℹ️ Siz administrator hisoblanasiz. Bemor monitoringi va tizim boshqaruvi quyidagi paneldan amalga oshiriladi:",
                                markup_p,
                            )
                        else:
                            status_text = format_status_response("Otabek Rahimov", DEMO_VITALS)
                            await send_telegram_message(chat_id, status_text)
                    elif text in ("/help", "/help@wmax_uz_bot", "❓ yordam", "yordam"):
                        if is_admin(chat_id):
                            text_p, markup_p = format_admin_help()
                            await send_telegram_message(chat_id, text_p, markup_p)
                        else:
                            await send_telegram_message(chat_id, HELP_TEXT)
                    elif text in ("☎️ shifokor", "shifokor"):
                        if is_admin(chat_id):
                            await send_telegram_message(
                                chat_id,
                                "ℹ️ Siz administrator sifatida tizimdasiz. Shifokor va xodimlar ro'yxatini ko'rish uchun <code>/users</code> buyrug'idan foydalaning.",
                            )
                        else:
                            await send_telegram_message(
                                chat_id,
                                "☎️ <b>Shifokor bilan bog'lanish:</b>\n\n"
                                "👨‍⚕️ Dr. Bahrom Alimov\n"
                                "📞 +998 90 123 45 67\n"
                                "📍 Xorazm viloyati Kardiologiya Dispanseri\n\n"
                                "Ish vaqti: 08:00 — 17:00 (Du-Ju)",
                            )
                    elif text.startswith("/admin") or text in ("⚙️ admin panel", "admin"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Kechirasiz, ushbu bo'lim faqat tizim administratorlari uchun mo'ljallangan.")
                        else:
                            text_p, markup_p = format_admin_panel(chat_id)
                            await send_telegram_message(chat_id, text_p, markup_p)
                    elif text.startswith("/setkey"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            parts = raw_text.split(maxsplit=1)
                            if len(parts) < 2:
                                await send_telegram_message(chat_id, "ℹ️ Foydalanish: <code>/setkey &lt;gemini_api_key&gt;</code>")
                            else:
                                new_key = parts[1].strip()
                                await send_telegram_message(chat_id, "⏳ <i>API kalit tekshirilmoqda...</i>")
                                ok, lat, test_msg = await test_gemini_api(api_key=new_key)
                                set_api_key(new_key)
                                if ok:
                                    await send_telegram_message(
                                        chat_id,
                                        f"✅ <b>Yangi Gemini API kaliti saqlandi va faollashtirildi!</b>\n\n"
                                        f"• Kalit: <code>{mask_key(new_key)}</code>\n"
                                        f"• Model: <b>{get_model()}</b>\n"
                                        f"• Natija: {test_msg}\n"
                                        f"• Javob vaqti: {lat}s",
                                    )
                                else:
                                    await send_telegram_message(
                                        chat_id,
                                        f"⚠️ <b>API kalit saqlandi, ammo testda xatolik aniqlandi:</b>\n\n"
                                        f"• Kalit: <code>{mask_key(new_key)}</code>\n"
                                        f"• Xatolik: {test_msg}",
                                    )
                    elif text.startswith("/delkey"):
                        if not is_super_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Faqat Super Admin API kalitlarni o'chira oladi.")
                        else:
                            parts = raw_text.split(maxsplit=1)
                            if len(parts) == 1:
                                text_p, markup_p = format_delete_keys_panel()
                                await send_telegram_message(chat_id, text_p, markup_p)
                            else:
                                arg = parts[1].strip()
                                keys = get_all_api_keys()
                                target_id = None
                                if arg.isdigit():
                                    idx = int(arg) - 1
                                    if 0 <= idx < len(keys):
                                        target_id = keys[idx]["id"]
                                else:
                                    for k in keys:
                                        if k["id"] == arg or k["key"] == arg:
                                            target_id = k["id"]
                                            break
                                if target_id:
                                    ok, msg_res = delete_api_key_by_id(target_id)
                                    await send_telegram_message(chat_id, msg_res)
                                    text_p, markup_p = format_api_keys_panel()
                                    await send_telegram_message(chat_id, text_p, markup_p)
                                else:
                                    await send_telegram_message(
                                        chat_id,
                                        f"❌ Bunday kalit topilmadi. Mavjud kalitlar soni: {len(keys)} ta.",
                                    )
                    elif text.startswith("/testkey"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            await send_telegram_message(chat_id, "⏳ <i>Gemini API ulanishi tekshirilmoqda...</i>")
                            ok, lat, test_msg = await test_gemini_api()
                            icon = "✅" if ok else "❌"
                            await send_telegram_message(
                                chat_id,
                                f"{icon} <b>Gemini API ulanish testi:</b>\n\n"
                                f"• Holat: {test_msg}\n"
                                f"• Model: <code>{get_model()}</code>\n"
                                f"• Kalit: <code>{mask_key(get_active_api_key())}</code>\n"
                                f"• Javob vaqti: <b>{lat}s</b>",
                            )
                    elif text.startswith("/setmodel"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            parts = raw_text.split(maxsplit=1)
                            if len(parts) < 2:
                                models_str = ", ".join(SUPPORTED_MODELS)
                                await send_telegram_message(
                                    chat_id,
                                    f"ℹ️ Foydalanish: <code>/setmodel &lt;model_nomi&gt;</code>\n\nMavjud modellar: {models_str}",
                                )
                            else:
                                new_mod = parts[1].strip()
                                set_model(new_mod)
                                await send_telegram_message(chat_id, f"✅ AI modeli o'zgartirildi: <b>{new_mod}</b>")
                    elif text.startswith("/setthreshold"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            parts = raw_text.split()
                            if len(parts) < 3:
                                await send_telegram_message(
                                    chat_id,
                                    "ℹ️ Foydalanish: <code>/setthreshold &lt;parametr&gt; &lt;qiymat&gt;</code>\n"
                                    "Masalan: <code>/setthreshold spo2 92</code> yoki <code>/setthreshold hr 110</code>",
                                )
                            else:
                                try:
                                    val = float(parts[2])
                                    ok, msg_res = set_threshold(parts[1], val)
                                    await send_telegram_message(chat_id, msg_res)
                                except ValueError:
                                    await send_telegram_message(chat_id, "❌ Qiymat raqam ko'rinishida bo'lishi kerak.")
                    elif text.startswith("/mode"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            parts = raw_text.split(maxsplit=1)
                            if len(parts) < 2:
                                await send_telegram_message(
                                    chat_id,
                                    f"ℹ️ Joriy rejim: <b>{get_system_mode().capitalize()}</b>\n"
                                    "O'zgartirish uchun: <code>/mode hybrid</code> yoki <code>/mode offline</code>",
                                )
                            else:
                                m = parts[1].strip().lower()
                                if m in ("hybrid", "offline"):
                                    set_system_mode(m)
                                    await send_telegram_message(chat_id, f"✅ Tizim rejimi o'rnatildi: <b>{m.capitalize()}</b>")
                                else:
                                    await send_telegram_message(chat_id, "❌ Rejim faqat 'hybrid' yoki 'offline' bo'lishi mumkin.")
                    elif text.startswith("/admins"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            text_p, markup_p = format_admins_panel(chat_id)
                            await send_telegram_message(chat_id, text_p, markup_p)
                    elif text.startswith("/addadmin"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            parts = raw_text.split(maxsplit=2)
                            if len(parts) < 2:
                                await send_telegram_message(chat_id, "ℹ️ Foydalanish: <code>/addadmin &lt;telegram_id&gt; [ism]</code>\nMasalan: <code>/addadmin 123456789 Dr. Sardor</code>")
                            else:
                                target_id = parts[1]
                                target_name = parts[2] if len(parts) > 2 else f"Admin_{target_id}"
                                success, msg_res = add_admin(target_id, target_name)
                                await send_telegram_message(chat_id, msg_res)
                                if success:
                                    try:
                                        await send_telegram_message(
                                            target_id,
                                            f"🎉 Assalomu alaykum, <b>{target_name}</b>!\n\n"
                                            f"Sizga <b>WMAX</b> tizimida administratorlik huquqi berildi.\n"
                                            f"Admin panelni ochish uchun /admin buyrug'ini yuboring.",
                                            _persistent_reply_keyboard(target_id),
                                        )
                                    except Exception:
                                        pass
                    elif text.startswith("/deladmin"):
                        if not is_super_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Faqat Super Admin boshqa administratorlarni o'chirish huquqiga ega.")
                        else:
                            parts = raw_text.split(maxsplit=1)
                            if len(parts) < 2:
                                await send_telegram_message(chat_id, "ℹ️ Foydalanish: <code>/deladmin &lt;telegram_id&gt;</code>")
                            else:
                                target_id = parts[1]
                                success, msg_res = remove_admin(target_id)
                                await send_telegram_message(chat_id, msg_res)
                    elif text.startswith("/sysinfo"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            text_s, markup_s = format_sysinfo()
                            await send_telegram_message(chat_id, text_s, markup_s)
                    elif text.startswith("/broadcast"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            parts = raw_text.split(maxsplit=1)
                            if len(parts) < 2:
                                await send_telegram_message(chat_id, "ℹ️ Foydalanish: <code>/broadcast &lt;xabar matni&gt;</code>")
                            else:
                                broadcast_msg = f"📢 <b>Rasmiy xabarnoma (WMAX):</b>\n\n{parts[1]}"
                                admins = get_all_admins()
                                sent_cnt = 0
                                for a in admins:
                                    aid = a.get("id")
                                    if aid:
                                        res = await send_telegram_message(aid, broadcast_msg)
                                        if res:
                                            sent_cnt += 1
                                await send_telegram_message(chat_id, f"✅ Xabar {sent_cnt} nafar administratorga yetkazildi.")
                    else:
                        # Process natural query via Hybrid AI (Gemini) + Algorithmic Triage
                        ai_reply = await handle_user_query(
                            text=raw_text,
                            patient_name="Otabek Rahimov",
                            vitals=DEMO_VITALS,
                        )
                        await send_telegram_message(chat_id, ai_reply)

            except Exception as err:
                logger.debug("Telegram polling transient error: %s", err)
                await asyncio.sleep(4)

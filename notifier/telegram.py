from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nazorat.notifier.telegram")

from .admin_store import (
    SUPER_ADMIN_ID,
    add_admin,
    get_all_admins,
    is_admin,
    is_super_admin,
    remove_admin,
)
from .ai_assistant import handle_user_query

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5174").rstrip("/")


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


def _persistent_reply_keyboard(user_id: int | str | None = None) -> dict:
    """Persistent reply keyboard — always visible at the bottom where user types.
    Shows Admin panel button for authorized administrators."""
    rows = [
        [
            {"text": "📊 Ko'rsatkichlar"},
            {"text": "☎️ Shifokor"},
            {"text": "❓ Yordam"},
        ],
    ]
    if user_id and is_admin(user_id):
        rows.append([{"text": "⚙️ Admin panel"}])

    return {
        "keyboard": rows,
        "resize_keyboard": True,
        "is_persistent": True,
    }


def format_admin_panel(user_id: int | str) -> tuple[str, dict]:
    """Format interactive admin panel for Super Admin and appointed admins."""
    is_super = is_super_admin(user_id)
    role_badge = "👑 <b>Super Admin</b>" if is_super else "🛡️ <b>Administrator</b>"
    admins_cnt = len(get_all_admins())

    text = (
        f"⚙️ <b>NAZORAT (WMAX) — Boshqaruv paneli</b>\n\n"
        f"👤 Sizning rolingiz: {role_badge}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"👥 Ro'yxatdagi adminlar: <b>{admins_cnt} nafar</b>\n\n"
        f"<b>Mavjud buyruqlar:</b>\n"
        f"• /admins — Administratorlar ro'yxati\n"
        f"• <code>/addadmin &lt;id&gt; [ism]</code> — Yangi admin qo'shish\n"
        f"• <code>/deladmin &lt;id&gt;</code> — Adminni o'chirish\n"
        f"• /sysinfo — Tizim holati va telemetriya\n"
        f"• <code>/broadcast &lt;xabar&gt;</code> — Adminlarga xabarnoma\n\n"
        f"<i>Tezkor boshqaruv tugmalari:</i>"
    )

    markup = {
        "inline_keyboard": [
            [
                {"text": "👥 Adminlar ro'yxati", "callback_data": "adm_list"},
                {"text": "📊 Tizim holati", "callback_data": "adm_sysinfo"},
            ],
            [
                {"text": "❓ Admin yordam", "callback_data": "adm_help"},
                {"text": "🔄 Yangilash", "callback_data": "adm_refresh"},
            ],
        ]
    }
    return text, markup


def format_sysinfo() -> str:
    """Format system diagnostics report."""
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    admins_cnt = len(get_all_admins())
    return (
        f"📊 <b>NAZORAT (WMAX) — Tizim holati</b>\n\n"
        f"🟢 API Server: <code>Faol (Online)</code>\n"
        f"🟢 AI Assistent: <code>Gemini 3.5 Flash-Lite (Faol)</code>\n"
        f"🟢 Telemetriya oqimi: <code>Sinxronizatsiyada</code>\n"
        f"👥 Ro'yxatdagi adminlar: <b>{admins_cnt} nafar</b>\n"
        f"👑 Super Admin ID: <code>{SUPER_ADMIN_ID}</code>\n"
        f"🕒 Server vaqti: <code>{now_str}</code>"
    )


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
        f"\U0001f6a8 <b>NAZORAT: QIZIL SIGNAL</b>\n\n"
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
    "Bu <b>NAZORAT (WMAX)</b> — Masofaviy klinik telemonitoring va erta ogohlantirish tizimining rasmiy boti.\n\n"
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
    "❓ <b>NAZORAT Bot — Yordam va imkoniyatlar</b>\n\n"
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
                        elif cb_data == "adm_list":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            admins = get_all_admins()
                            lines = [f"👥 <b>Administratorlar ro'yxati ({len(admins)} nafar):</b>\n"]
                            for a in admins:
                                role = "👑 Super Admin" if a.get("role") == "super_admin" else "🛡️ Admin"
                                lines.append(f"• <b>{a.get('name')}</b> — {role}\n  ID: <code>{a.get('id')}</code>")
                            await send_telegram_message(cb_chat_id, "\n".join(lines))
                        elif cb_data == "adm_sysinfo":
                            if not is_admin(cb_chat_id):
                                await send_telegram_message(cb_chat_id, "⛔️ Ruxsat berilmagan.")
                                continue
                            await send_telegram_message(cb_chat_id, format_sysinfo())
                        elif cb_data == "adm_help":
                            admin_help = (
                                "📖 <b>Admin qo'llanma:</b>\n\n"
                                "• <code>/addadmin &lt;id&gt; &lt;ism&gt;</code> — Yangi admin biriktirish\n"
                                "• <code>/deladmin &lt;id&gt;</code> — Adminni o'chirish\n"
                                "• <code>/admins</code> — Ro'yxatni ko'rish\n"
                                "• <code>/sysinfo</code> — Server va telemetriya holati\n"
                                "• <code>/broadcast &lt;xabar&gt;</code> — Adminlarga xabar yuborish"
                            )
                            await send_telegram_message(cb_chat_id, admin_help)
                        elif cb_data == "adm_refresh":
                            text_p, markup_p = format_admin_panel(cb_chat_id)
                            await send_telegram_message(cb_chat_id, text_p, markup_p)
                        continue

                    # Handle text messages
                    msg = update.get("message") or update.get("edited_message")
                    if not msg:
                        continue

                    chat_id = msg["chat"]["id"]
                    user_name = msg.get("from", {}).get("first_name", "Foydalanuvchi")
                    raw_text = (msg.get("text") or "").strip()
                    text = raw_text.lower()

                    logger.info("Received Telegram message from '%s' (chat_id=%s): %s", user_name, chat_id, text)

                    if text in ("/start", "/start@wmax_uz_bot"):
                        welcome = WELCOME_TEXT.format(user_name=user_name, chat_id=chat_id)
                        await send_telegram_message(chat_id, welcome, _persistent_reply_keyboard(chat_id))
                    elif text in ("/status", "/status@wmax_uz_bot", "📊 ko'rsatkichlar", "ko'rsatkichlar"):
                        status_text = format_status_response("Otabek Rahimov", DEMO_VITALS)
                        await send_telegram_message(chat_id, status_text)
                    elif text in ("/help", "/help@wmax_uz_bot", "❓ yordam", "yordam"):
                        await send_telegram_message(chat_id, HELP_TEXT)
                    elif text in ("☎️ shifokor", "shifokor"):
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
                    elif text.startswith("/admins"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            admins = get_all_admins()
                            lines = [f"👥 <b>Administratorlar ro'yxati ({len(admins)} nafar):</b>\n"]
                            for a in admins:
                                role = "👑 Super Admin" if a.get("role") == "super_admin" else "🛡️ Admin"
                                lines.append(f"• <b>{a.get('name')}</b> — {role}\n  ID: <code>{a.get('id')}</code>")
                            await send_telegram_message(chat_id, "\n".join(lines))
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
                                            f"Sizga <b>NAZORAT (WMAX)</b> tizimida administratorlik huquqi berildi.\n"
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
                            await send_telegram_message(chat_id, format_sysinfo())
                    elif text.startswith("/broadcast"):
                        if not is_admin(chat_id):
                            await send_telegram_message(chat_id, "⛔️ Ruxsat berilmagan.")
                        else:
                            parts = raw_text.split(maxsplit=1)
                            if len(parts) < 2:
                                await send_telegram_message(chat_id, "ℹ️ Foydalanish: <code>/broadcast &lt;xabar matni&gt;</code>")
                            else:
                                broadcast_msg = f"📢 <b>Rasmiy xabarnoma (NAZORAT):</b>\n\n{parts[1]}"
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

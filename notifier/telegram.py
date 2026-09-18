from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("nazorat.notifier.telegram")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5174").rstrip("/")


async def send_telegram_message(chat_id: int | str, text: str) -> bool:
    """Send Telegram message or log it if token is not configured."""
    if not TELEGRAM_BOT_TOKEN:
        logger.info(
            "[TELEGRAM MOCK SEND] To chat_id=%s:\n%s",
            chat_id,
            text,
        )
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

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


def format_relative_alert(patient_name: str, access_token: str, level: str) -> str:
    """Relative message template — clinical diagnosis is never disclosed."""
    link = f"{PUBLIC_BASE_URL}/r/{access_token}"
    if level == "red":
        prefix = "🚨 <b>DIQQAT: ZUDLIK BILAN E'TIBOR TALAB ETILADI</b>"
    elif level == "amber":
        prefix = "⚠️ <b>Eslatma</b>"
    else:
        prefix = "ℹ️ <b>Ma'lumot</b>"

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
    """Doctor alert template."""
    params_str = ", ".join(f"{k}: {v}" for k, v in triggered_params.items())
    return (
        f"🚨 <b>NAZORAT: QIZIL SIGNAL</b>\n\n"
        f"<b>Bemor:</b> {patient_name} ({age} yosh, {district})\n"
        f"<b>Tashxis:</b> {diagnosis}\n"
        f"<b>Sabab:</b> {reason or 'Chetlanishlar aniqlandi'}\n"
        f"<b>Ko'rsatkichlar:</b> {params_str}\n\n"
        f"Aktiv chaqiruv vazifasi yaratildi (24 soatlik taymer)."
    )


def format_active_call_reminder(patient_name: str, due_in_hours: int) -> str:
    return (
        f"⚠️ <b>ESLATMA: AKTIV CHAQIRUV</b>\n\n"
        f"Bemor <b>{patient_name}</b> bo'yicha belgilangan 24 soatlik patronaj muddati "
        f"<b>{due_in_hours} soatdan so'ng</b> yakunlanadi.\n"
        f"Iltimos, tashrifni amalga oshiring va tizimda tasdiqlang."
    )


def format_overdue_escalation(patient_name: str, doctor_name: str | None, district: str) -> str:
    return (
        f"⛔ <b>ESKALATSIYA (MUDDATI O'TDI)</b>\n\n"
        f"Bemor <b>{patient_name}</b> ({district}) bo'yicha 24 soatlik aktiv chaqiruv "
        f"o'z vaqtida tasdiqlanmadi.\n"
        f"Mas'ul: {doctor_name or 'Biriktirilgan shifokor'}"
    )


def format_no_data_alert(patient_name: str, access_token: str) -> str:
    link = f"{PUBLIC_BASE_URL}/r/{access_token}"
    return (
        f"ℹ️ <b>Soat aloqasi yo'q</b>\n\n"
        f"Bemor <b>{patient_name}</b>ning aqlli soati 45 daqiqadan beri ma'lumot yubormayapti.\n"
        f"Iltimos, soat qo'lga taqilgani va quvvati borligini tekshirib ko'ring.\n\n"
        f"Holat: <a href=\"{link}\">{link}</a>"
    )

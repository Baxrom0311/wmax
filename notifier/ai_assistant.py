from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nazorat.notifier.ai")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

EMERGENCY_KEYWORDS = [
    "sanchyapti", "yurak sanch", "hushidan ketdi", "hushsiz", "nafas qisyapti",
    "nafas ololmayapti", "tez yordam", "qon bosimi baland", "infarkt", "insult",
    "og'riyapti", "yordam bering", "103", "jonim og'riyapti", "hushdan",
    "скорая", "болит сердце", "потерял сознание", "задыхается", "инфаркт", "высокое давление"
]

GIBBERISH_PATTERNS = [
    r"^[bcdfghjklmnpqrstvwxyz]{5,}$",  # no vowels, 5+ letters
    r"^(.)\1{4,}$",                     # repeated same character 5+ times
    r"^(asdf|qwer|zxcv|ghjk|hjkl|nsif)",# keyboard smashes
]


def is_emergency(text: str) -> bool:
    """Check for acute medical emergencies that require immediate 103 ambulance triage."""
    normalized = text.lower().strip()
    return any(keyword in normalized for keyword in EMERGENCY_KEYWORDS)


def is_gibberish(text: str) -> bool:
    """Detect accidental keystrokes, noise or keyboard smashes."""
    normalized = text.lower().strip()
    if len(normalized) <= 2:
        return False
    # Check regex patterns
    for pat in GIBBERISH_PATTERNS:
        if re.search(pat, normalized):
            return True
    # Count vowels in long words
    vowels = set("aeiouo'уеыаоэяию")
    if len(normalized) >= 7:
        vowel_count = sum(1 for ch in normalized if ch in vowels)
        if vowel_count == 0:
            return True
    return False


def format_emergency_response() -> str:
    """Deterministic immediate SOS alert."""
    return (
        "🚨 <b>DIQQAT: ZUDLIK BILAN CHORA KO'RING!</b>\n\n"
        "Bemorning ahvoli jiddiy ko'rinsa, vaqtni boy bermang:\n\n"
        "📞 <b>103 — Tez tibbiy yordam</b> (bepul va kechayu kunduz)\n"
        "📞 <b>+998 90 123 45 67</b> — Dr. Bahrom Alimov (Davolovchi kardiolog)\n\n"
        "<b>Birinchi yordam:</b>\n"
        "1. Bemorni qulay, tekis o'tqazing yoki yotqizing.\n"
        "2. Yoqa va tor kiyimlarni yechib, xonaga toza havo kiriting.\n"
        "3. O'zboshimchalik bilan dori bermang, shifokor ko'rsatmasini kuting."
    )


def format_gibberish_response(patient_name: str) -> str:
    """Polite guidance message when text is unreadable or gibberish."""
    return (
        "Kechirasiz, xabaringizni to'liq tushuna olmadim. 😊\n\n"
        f"Men <b>NAZORAT</b> tizimining shaxsiy tibbiy assistentiman va sizga <b>{patient_name}</b>ning "
        "salomatlik ko'rsatkichlari bo'yicha yordam bera olaman.\n\n"
        "<b>Sizga qanday yordam bera olaman?</b> Masalan, mendan quyidagilarni so'rashingiz mumkin:\n\n"
        "• 💬 <i>«Dadamning hozirgi ahvoli qanday?»</i>\n"
        "• 💬 <i>«Pulsi me'yordami?»</i>\n"
        "• 💬 <i>«Kislorodi nega 92 bo'lib qoldi?»</i>\n"
        "• 💬 <i>«Kechasi qanday uxladi?»</i>\n"
        "• 💬 <i>«Shifokor bilan bog'lanish kerak»</i>\n\n"
        "Yoki pastdagi tayyor tugmalardan foydalanishingiz mumkin."
    )


def build_system_prompt(patient_name: str, vitals: dict[str, Any]) -> str:
    """System prompt grounding Gemini with real patient status and clinical boundaries."""
    hr = vitals.get("hr", 86)
    spo2 = vitals.get("spo2", 92)
    temp = vitals.get("skin_temp", 36.6)
    rr = vitals.get("rr", 19)
    sleep = vitals.get("sleep_hours", 5.4)
    steps = vitals.get("steps", 1840)
    level = vitals.get("level", "amber")

    return (
        f"Sen — 'NAZORAT (WMAX)' aqlli klinik telemonitoring tizimining sun'iy intellekt assistentisan.\n"
        f"Bemor: {patient_name}, 62 yosh, kardiologik dispanser nazoratida.\n\n"
        f"Aqlli soatdan olingan eng so'nggi real ma'lumotlar:\n"
        f"- Puls: {hr} bpm (me'yor: 60-90 bpm)\n"
        f"- SpO2 (qondagi kislorod): {spo2}% (me'yor: 95-100%, hozir 92% bo'lgani uchun 'sariq' ehtiyot darajasida)\n"
        f"- Tana harorati: {temp}°C (me'yor: 36.0-37.2°C)\n"
        f"- Nafas chastotasi: {rr}/daq (me'yor: 12-20)\n"
        f"- Uyqu davomiyligi: {sleep} soat (kecha 5.4 soat, me'yordan kamroq)\n"
        f"- Qadamlar: {steps} qadam\n"
        f"- Umumiy holat signali: {level.upper()} (sariq e'tibor holati)\n"
        f"- Davolovchi shifokor: Dr. Bahrom Alimov (+998 90 123 45 67)\n\n"
        "SENING QAT'IY QOIDALARING:\n"
        "1. O'zbek tilida muloyim, tushunarli, samimiy va professional tilda javob ber.\n"
        "2. Agar foydalanuvchi tushunarsiz yoki tasodifiy matn yozsa, do'stona tarzda: "
        "'Kechirasiz, tushuna olmadim. Bemor bo'yicha qanday yordam bera olaman?' deb yo'naltiruvchi savollar taklif qil.\n"
        "3. Bemorning real ko'rsatkichlariga tayanib tushuntir (masalan, kislorod 92% bo'lsa, "
        "me'yordan biroz pastligi, xonani shamollatish va dam olish kerakligini ayt).\n"
        "4. HECH QACHON o'zboshimchalik bilan retseptli dori vositalarini tavsiya qilma! "
        "Har doim davolovchi shifokor bilan maslahatlashishni eslat.\n"
        "5. Javobing ixcham, aniq va Telegram formatida (HTML teglari <b>, <i> qo'llash mumkin) bo'lsin."
    )


async def ask_gemini(user_message: str, patient_name: str, vitals: dict[str, Any]) -> str | None:
    """Call Google Gemini Flash REST API with grounded patient context."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    system_prompt = build_system_prompt(patient_name, vitals)

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 600,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
            logger.error("Gemini API returned status %s: %s", resp.status_code, resp.text[:300])
            return None
    except Exception as err:
        logger.exception("Exception querying Gemini API: %s", err)
        return None


def rule_based_fallback(text: str, patient_name: str, vitals: dict[str, Any]) -> str:
    """Smart offline rule engine when Gemini API is unavailable or offline."""
    t = text.lower().strip()
    hr = vitals.get("hr", 86)
    spo2 = vitals.get("spo2", 92)
    sleep = vitals.get("sleep_hours", 5.4)
    temp = vitals.get("skin_temp", 36.6)

    if any(w in t for w in ["salom", "assalom", "qalesiz", "salomatmisiz"]):
        return (
            f"Assalomu alaykum! Men <b>{patient_name}</b>ning salomatlik assistentiman. 😊\n\n"
            f"Hozirgi holat: Yurak urishi <b>{hr} bpm</b>, kislorod <b>{spo2}%</b>.\n"
            "Bemoringiz holati yoki shifokor tavsiyalari bo'yicha qanday yordam bera olaman?"
        )

    if any(w in t for w in ["ahvol", "qanday", "yaxshimi", "holat"]):
        return (
            f"📋 <b>{patient_name} — Hozirgi umumiy holat:</b>\n\n"
            f"❤️ Puls: <b>{hr} bpm</b> (me'yorida)\n"
            f"⚠️ SpO₂: <b>{spo2}%</b> (me'yordan biroz past, dam olish kerak)\n"
            f"🌙 Uyqu: <b>{sleep} soat</b>\n"
            f"🌡 Harorat: <b>{temp}°C</b>\n\n"
            "Umumiy holat barqaror, ammo kislorod darajasini kuzatib boryapmiz."
        )

    if any(w in t for w in ["puls", "yurak", "urish"]):
        return (
            f"❤️ <b>Yurak urishi (Puls):</b> <b>{hr} zarba/daq</b>\n\n"
            "Me'yor: 60 — 90 bpm. Hozirda ko'rsatkich me'yor chegarasida."
        )

    if any(w in t for w in ["kislorod", "spo2", "nafas"]):
        return (
            f"🫁 <b>SpO₂ (Qondagi kislorod):</b> <b>{spo2}%</b>\n\n"
            "Oddiy me'yor: 95% - 100%. Hozirgi 92% biroz pastroq.\n"
            "Tavsiya: Xonani shamollating, bemorga toza havodan erkin nafas olishga imkon bering."
        )

    if any(w in t for w in ["uyqu", "dam", "uxladi"]):
        return (
            f"🌙 <b>Uyqu tahlili:</b> Bemor kechasi <b>{sleep} soat</b> uxlagan.\n\n"
            "Bu to'laqonli tiklanish uchun me'yordan biroz kamroq. Bugun tinch dam olishi maqsadga muvofiq."
        )

    if any(w in t for w in ["shifokor", "doktor", "vrach", "bog'lanish", "raqam"]):
        return (
            "👨‍⚕️ <b>Davolovchi shifokor:</b> Dr. Bahrom Alimov\n"
            "📞 <b>Telefon:</b> +998 90 123 45 67\n"
            "📍 <b>Manzil:</b> Xorazm viloyati Kardiologiya Dispanseri\n"
            "Ish vaqti: 08:00 — 17:00 (Du-Ju)"
        )

    return format_gibberish_response(patient_name)


async def handle_user_query(text: str, patient_name: str, vitals: dict[str, Any]) -> str:
    """Main routing pipeline:
    1. Emergency check -> instant SOS
    2. Gibberish check -> polite guidance
    3. Gemini AI assistant -> natural clinical conversation
    4. Offline rule engine fallback
    """
    # 1. Emergency
    if is_emergency(text):
        return format_emergency_response()

    # 2. Gibberish
    if is_gibberish(text):
        return format_gibberish_response(patient_name)

    # 3. Gemini AI
    ai_answer = await ask_gemini(text, patient_name, vitals)
    if ai_answer:
        return ai_answer

    # 4. Fallback
    return rule_based_fallback(text, patient_name, vitals)

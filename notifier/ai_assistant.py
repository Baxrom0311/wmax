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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

EMERGENCY_KEYWORDS = [
    # Uzbek
    "sanchyapti", "yurak sanch", "hushidan ketdi", "hushsiz", "nafas qisyapti",
    "nafas ololmayapti", "tez yordam", "qon bosimi baland", "infarkt", "insult",
    "og'riyapti", "yordam bering", "103", "jonim og'riyapti", "hushdan", "yurak to'xtadi",
    # Russian
    "скорая", "болит сердце", "потерял сознание", "задыхается", "инфаркт", "инсульт",
    "высокое давление", "приступ", "не дышит", "помогите", "103", "остановка сердца",
    # English
    "chest pain", "heart attack", "unconscious", "cannot breathe", "ambulance",
    "stroke", "emergency", "passed out", "severe pain", "911", "103"
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
    """Deterministic immediate SOS alert in 3 languages."""
    return (
        "🚨 <b>Diqqat: Zudlik bilan shoshilinch chora ko'ring! / Внимание: Срочные меры! / Emergency: Immediate Action Required!</b>\n\n"
        "Bemorning holati kritik bo'lsa, zudlik bilan shifokor yoki tez yordam bilan bog'laning:\n\n"
        "📞 <b>103 — Tez tibbiy yordam / Скорая помощь / Emergency</b>\n"
        "📞 <b>+998 90 123 45 67</b> — Dr. Bahrom Alimov (Kardiolog)\n\n"
        "<b>Shoshilinch ko'rsatmalar:</b>\n"
        "1. Bemorni qulay, bosh tomoni biroz ko'tarilgan tekis holatga yotqizing.\n"
        "2. Yoqa va tor kiyimlarni yechib, xonani shamollating.\n"
        "3. O'zboshimchalik bilan dori bermang, mutaxassis ko'rsatmasini kuting."
    )


def format_gibberish_response(patient_name: str) -> str:
    """Polite guidance message in Sentence Case."""
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
    """System prompt grounding Gemini with real patient status, clinical ICD diagnoses, and 3-language rules."""
    hr = vitals.get("hr", 86)
    spo2 = vitals.get("spo2", 92)
    temp = vitals.get("skin_temp", 36.6)
    rr = vitals.get("rr", 19)
    sleep = vitals.get("sleep_hours", 5.4)
    steps = vitals.get("steps", 1840)
    level = vitals.get("level", "amber")

    return (
        f"Sen — 'NAZORAT (WMAX)' aqlli klinik telemonitoring tizimining sun'iy intellekt assistentisan.\n"
        f"Bemor: {patient_name}, 62 yosh.\n"
        f"Klinik tashxis: Yurak ishemik kasalligi (YIK). Zo'riqish stenokardiyasi FK III. "
        f"Postinfarkt kardioskleroz (2024). Surunkali yurak yetishmovchiligi (SYuYe) IIB bosqich, NYHA III. "
        f"Sinusli taxikardiya va paroksizmal gipoksemiya epizodlari.\n\n"
        f"Aqlli soatdan olingan eng so'nggi real telemetrik ko'rsatkichlar:\n"
        f"- Yurak urishi (ChSS / Puls): {hr} bpm (fiziologik me'yor: 60-90 bpm)\n"
        f"- Arterial kislorod (SpO2): {spo2}% (klinik me'yor: 95-100%, 92% — yengil darajadagi gipoksemiya, sariq signal)\n"
        f"- Tana harorati: {temp}°C (me'yor: 36.0-37.2°C)\n"
        f"- Nafas chastotasi (ChDD): {rr}/daq (me'yor: 12-20/daq)\n"
        f"- Tungi uyqu: {sleep} soat (klinik norma: 7-8 soat, uyqu tanqisligi yurak faoliyatiga yuklama beradi)\n"
        f"- Kunlik faollik: {steps} qadam\n"
        f"- Tizimli triaj holati: {level.capitalize()} (Subkompensatsiya / Kuzatuv)\n"
        f"- Davolovchi kardiolog: Dr. Bahrom Alimov (+998 90 123 45 67)\n\n"
        "SENING QAT'IY QOIDALARING:\n"
        "1. QAT'IY TIL QOIDASI (CRITICAL LANGUAGE RULE): Foydalanuvchi yozgan tilni darhol aniqlang. "
        "Agar foydalanuvchi Rus tilida yozsa — javobingiz 100% RUS TILIDA bo'lishi SHART! "
        "If user writes in English — your response MUST be 100% in ENGLISH! "
        "Agar foydalanuvchi O'zbek tilida yozsa — javobingiz O'ZBEK TILIDA bo'ladi.\n"
        "2. PROFESSIONAL SHIFOKOR VA KLINIK TERMINOLOGIYA: Tibbiy jihatdan savodli kardiologik terminologiyani to'g'ri qo'lla "
        "(masalan: 'sinusli taxikardiya' / 'синусовая тахикардия' / 'sinus tachycardia', "
        "'arterial gipoksemiya' / 'артериальная гипоксемия' / 'arterial hypoxemia', "
        "'gemodinamik barqarorlik' / 'стабильная гемодинамика' / 'compensated hemodynamics').\n"
        "3. TIPOGRAFIKA VA MATN REGISTRI: Hech qachon ALL-CAPS (katta harflar bilan baqirib) yozma! "
        "Faqat gapning birinchi harfi bosh harf bilan, qolgani kichik harflar bilan yozilsin (Sentence case).\n"
        "4. KLINIK XAVFSIZLIK: O'zboshimchalik bilan retseptli dori yozma. "
        "Har doim davolovchi shifokor Dr. Bahrom Alimov bilan bog'lanishni eslat.\n"
        "5. Telegram formati: Matning chiroyli, HTML teglari (<b>, <i>) bilan formatlangan, qisqa va aniq bo'lsin."
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
            "temperature": 0.3,
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
    """Smart multilingual offline rule engine when Gemini API is unavailable or offline."""
    t = text.lower().strip()
    hr = vitals.get("hr", 86)
    spo2 = vitals.get("spo2", 92)
    sleep = vitals.get("sleep_hours", 5.4)
    temp = vitals.get("skin_temp", 36.6)

    # Russian detection
    is_ru = any(ch in t for ch in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    # English detection
    is_en = any(w in t for w in ["hello", "hi", "how", "what", "pulse", "heart", "oxygen", "doctor", "sleep"])

    if is_en:
        if any(w in t for w in ["hello", "hi", "good morning", "good evening"]):
            return (
                f"Hello! I am the medical AI assistant for <b>{patient_name}</b>. 😊\n\n"
                f"Current vitals: Heart rate <b>{hr} bpm</b>, blood oxygen <b>{spo2}%</b>.\n"
                "How can I assist you regarding clinical parameters or doctor recommendations?"
            )
        if any(w in t for w in ["pulse", "heart", "hr"]):
            return (
                f"❤️ <b>Heart rate (Pulse):</b> <b>{hr} bpm</b>\n\n"
                "Normal physiological range: 60 — 90 bpm. Current reading is compensated."
            )
        if any(w in t for w in ["oxygen", "spo2"]):
            return (
                f"🫁 <b>Blood oxygen saturation (SpO₂):</b> <b>{spo2}%</b>\n\n"
                "Normal range: 95% - 100%. Current 92% indicates mild hypoxemia. Ensure fresh ventilation and restful positioning."
            )
        return format_gibberish_response(patient_name)

    if is_ru:
        if any(w in t for w in ["привет", "здравствуйте", "добрый"]):
            return (
                f"Здравствуйте! Я клинический ассистент пациента <b>{patient_name}</b>. 😊\n\n"
                f"Текущие показатели: Пульс <b>{hr} уд/мин</b>, кислород <b>{spo2}%</b>.\n"
                "Чем я могу помочь вам по состоянию здоровья или рекомендациям врача?"
            )
        if any(w in t for w in ["пульс", "сердце", "чсс"]):
            return (
                f"❤️ <b>Частота сердечных сокращений (Пульс):</b> <b>{hr} уд/мин</b>\n\n"
                "Физиологическая норма: 60 — 90 уд/мин. Показатель находится в пределах нормы."
            )
        if any(w in t for w in ["кислород", "spo2", "сатурация"]):
            return (
                f"🫁 <b>Сатурация кислорода (SpO₂):</b> <b>{spo2}%</b>\n\n"
                "Клиническая норма: 95% - 100%. Текущее значение 92% указывает на умеренную гипоксемию. Рекомендуется проветрить комнату и обеспечить пациенту покой."
            )
        return format_gibberish_response(patient_name)

    # Uzbek default
    if any(w in t for w in ["salom", "assalom", "qalesiz", "salomatmisiz"]):
        return (
            f"Assalomu alaykum! Men <b>{patient_name}</b>ning klinik salomatlik assistentiman. 😊\n\n"
            f"Hozirgi telemetriya: Yurak urishi <b>{hr} bpm</b>, arterial kislorod <b>{spo2}%</b>.\n"
            "Bemoringiz holati yoki kardiolog tavsiyalari bo'yicha qanday yordam bera olaman?"
        )

    if any(w in t for w in ["ahvol", "qanday", "yaxshimi", "holat"]):
        return (
            f"📋 <b>{patient_name} — Hozirgi klinik holat:</b>\n\n"
            f"❤️ Puls (ChSS): <b>{hr} bpm</b> (kompensatsiyalangan)\n"
            f"⚠️ SpO₂ (Kislorod): <b>{spo2}%</b> (subkompensatsiya, yengil gipoksemiya)\n"
            f"🌙 Tungi uyqu: <b>{sleep} soat</b>\n"
            f"🌡 Tana harorati: <b>{temp}°C</b>\n\n"
            "Klinik holat: Subkompensatsiya. Dam olish va tinch muhit tavsiya etiladi."
        )

    if any(w in t for w in ["puls", "yurak", "urish"]):
        return (
            f"❤️ <b>Yurak urishi (Puls / ChSS):</b> <b>{hr} zarba/daq</b>\n\n"
            "Fiziologik me'yor: 60 — 90 bpm. Hozirda ko'rsatkich me'yor chegarasida."
        )

    if any(w in t for w in ["kislorod", "spo2", "nafas"]):
        return (
            f"🫁 <b>Arterial kislorod (SpO₂):</b> <b>{spo2}%</b>\n\n"
            "Klinik me'yor: 95% - 100%. Hozirgi 92% yengil gipoksemiyani ko'rsatadi.\n"
            "Tavsiya: Xonani shamollating, bemorga erkin va toza havodan nafas olishga imkon bering."
        )

    if any(w in t for w in ["uyqu", "dam", "uxladi"]):
        return (
            f"🌙 <b>Tungi uyqu tahlili:</b> Bemor kechasi <b>{sleep} soat</b> uxlagan.\n\n"
            "Fiziologik tiklanish uchun bu me'yordan kamroq. Bemorga qo'shimcha dam olish tavsiya etiladi."
        )

    if any(w in t for w in ["shifokor", "doktor", "vrach", "bog'lanish", "raqam"]):
        return (
            "👨‍⚕️ <b>Davolovchi kardiolog:</b> Dr. Bahrom Alimov\n"
            "📞 <b>Telefon:</b> +998 90 123 45 67\n"
            "📍 <b>Manzil:</b> Xorazm viloyati Kardiologiya Dispanseri\n"
            "Ish vaqti: 08:00 — 17:00 (Du-Ju)"
        )

    return format_gibberish_response(patient_name)


async def handle_user_query(text: str, patient_name: str, vitals: dict[str, Any]) -> str:
    """Main routing pipeline:
    1. Emergency check -> instant SOS in 3 languages
    2. Gibberish check -> polite guidance
    3. Gemini AI assistant -> natural multilingual clinical conversation
    4. Offline multilingual rule engine fallback
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

"""Public Q&A chat for the Pitch Day site, answered by DeepSeek.

The endpoint is anonymous, so it only ever sees the visitor's question and the
project facts below: no patient data, no database access. Requests are rate
limited per client and globally to cap API spend. When DeepSeek is not
configured or fails, it answers 503 and the site falls back to its prepared
answers.
"""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.ai.guardrails import detect_prompt_injection
from app.auth.router import _client_ip
from app.core.exceptions import AIProviderException
from app.core.rate_limit import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/public", tags=["public"])

# Per visitor and for the whole site, so a single script cannot run up the bill.
client_limiter = SlidingWindowRateLimiter(max_attempts=20, window_seconds=600)
global_limiter = SlidingWindowRateLimiter(max_attempts=600, window_seconds=3600)

LANG_NAMES = {"uz": "o'zbek (lotin yozuvi)", "ru": "русский", "en": "English"}

SYSTEM_PROMPT = """Sen WMAX masofaviy kardio-monitoring platformasining rasmiy aqlli AI assistentisan (DeepSeek-V3 neyrotarmog'i asosida ishlayapsan).
Foydalanuvchilarga do'stona, samimiy, batafsil, tushunarli va professional tilda javob ber.

WMAX haqida asosiy ma'lumotlar:
- Muammo: Kasalxonadan (infarkt, stenokardiya yoki kardiojarrohlikdan) chiqqan bemorlar dastlabki 30 kun davomida uyda deyarli qarovsiz va telemetriyasiz qoladi. Kasalxona epikriz xulosalarining atigi 12–34% i oilaviy poliklinika shifokoriga yetib boradi, krizislar esa to'satdan yuz beradi.
- Yechim: WMAX aqlli soat (Samsung Galaxy Watch, Wear OS) orqali bemorning puls, SpO₂ (kislorod), harakat faolligi, uyqu va yiqilish holatlarini 24/7 rejimda qayd etadi. Chegaradan chiqish holatlarida aniq mas'ul shifokorga 24 soatlik klinik vazifa ochiladi, oila a'zolariga esa Telegram orqali real-vaqtda ogohlantirish ketadi. Internet uzilsa ma'lumot soat xotirasida saqlanadi, favqulodda SOS holatida zaxira SMS ketadi.
- AI (Sun'iy Intellekt): Har bir bemorning shaxsiy individual me'yorini (z-score baseline) hisoblaydi va anomaliyalarni erta aniqlaydi. LLM (DeepSeek) Telegram botda va saytda savollarga sodda, tushunarli tilda javob beradi. Muhim qoida: AI mustaqil tashxis qo'ymaydi va dori dozalash bo'yicha mustaqil qaror chiqarmaydi — yakuniy klinik qaror shifokor tomonidan qabul qilinadi.
- Sensorlar: Soat qon bosimi va glyukozani o'lchamaydi (chunki hozircha smart-soatlarda klinik validatsiyalangan optik datchik yo'q). Sifatsiz o'lchov hech qachon "normal" deb soxtalashtirilmaydi.
- Maxfiylik: Bemor ma'lumotlari to'liq shifrlangan (TLS 1.3, AES-256), PostgreSQL RLS (Row Level Security) bilan himoyalangan. Bemor o'z roziligini istalgan payt bekor qilishi mumkin.
- SOS xizmati: SOS va kritik ogohlantirishlar hech qachon pullik qilinmaydi.
- Bosqich: Hozirda Prototype bosqichidamiz (tizim onlayn ishlaydi, arxitektura to'liq faol). Yo'l xaritasi: Idea → Prototype (hozir) → MVP (100 bemorlik pilot sinov) → Launched (poliklinikalar va xususiy klinikalar).
- Jamoa:
  1. Baxrom Bekchanov — Asoschi, Bosh tizimlar arxitektori va Full-stack muhandis (FastAPI, PostgreSQL 16, React, TypeScript, Docker, Flutter, Microservices; backend va xavfsizlik arxitekturasi me'mori).
  2. Nafisa Gʻanijanova — Asoschi, Bosh dizayner va UI/UX mutaxassisi (Figma, mahsulot dizayni, shifokor va bemor portallari interfeys me'mori).
  3. Nodirbek Boltayev — AI / ML & Telemetriya muhandisi (Python, z-score biometrik tahlili, biometriya algoritmlari va LLM integratsiyasi).
- Texnologiyalar steki: FastAPI, PostgreSQL 16, React, TypeScript, Tailwind CSS, Flutter (Android & Wear OS), Redis, Telegram Bot, Docker Compose. AI vositalari: DeepSeek-V3, z-score baseline, Claude Code, GitHub Copilot.
- Havolalar: Demo video va prototip: /demo; Shifokor paneli: /doctor?demo=true; Oila portali: /r; Telegram bot: t.me/WMAX_uz_bot; API hujjatlari: /api/docs (OpenAPI 3, JWT); Kod ombori: github.com/Baxrom0311/wmax.

Muloqot qoidalari:
- Samimiy, madaniyatli, tushunarli tilda gapir.
- Foydalanuvchi salomlashsa yoki hol-ahvol so'rasa, xushmuomalalik bilan javob berib, WMAX bo'yicha har qanday savolga tayyor ekaningni ayt.
- Savollarga lo'nda, ammo to'liq va asosli javob ber.
- Shaxsiy tibbiy tashxis yoki dori buyurma, favqulodda holatda 103 ga qo'ng'iroq qilish kerakligini eslat.
- Javobni foydalanuvchi murojaat qilgan tilda ber."""


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=1000)


class PitchChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    lang: Literal["uz", "ru", "en"] = "uz"
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)


class PitchChatResponse(BaseModel):
    answer: str
    source: Literal["deepseek"] = "deepseek"
    model: str = "DeepSeek-V3"


def _provider():
    from app.ai.deepseek_provider import DeepSeekProvider

    return DeepSeekProvider(timeout=25.0, max_retries=2)


@router.post(
    "/pitch-chat",
    response_model=PitchChatResponse,
    summary="Ask the WMAX site assistant (DeepSeek)",
)
async def pitch_chat(req: PitchChatRequest, request: Request) -> PitchChatResponse:
    for limiter, key in ((client_limiter, f"pitch-chat:{_client_ip(request)}"), (global_limiter, "pitch-chat:all")):
        retry_after = limiter.check(key)
        if retry_after:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring.",
                headers={"Retry-After": str(retry_after)},
            )

    turns = [*req.history[-8:], ChatTurn(role="user", content=req.message)]
    if any(t.role == "user" and detect_prompt_injection(t.content)[0] for t in turns):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Savolni qayta yozing.")

    system = f"{SYSTEM_PROMPT}\n\nJavob berilishi kerak bo'lgan til: {LANG_NAMES[req.lang]}."
    messages = [{"role": "system", "content": system}, *({"role": t.role, "content": t.content} for t in turns)]

    provider = _provider()
    try:
        answer = await provider.chat(messages, temperature=0.6, max_tokens=700)
    except AIProviderException as err:
        logger.warning("Pitch chat unavailable: %s", err)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI yordamchi hozir mavjud emas.") from err

    return PitchChatResponse(answer=answer, source="deepseek", model="DeepSeek-V3")

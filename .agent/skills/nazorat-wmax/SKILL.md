---
name: nazorat-wmax
description: NAZORAT (WMAX) — Aqlli Masofaviy Bemor Monitoringi va Erta Ogohlantirish Tizimi loyihasi bo'yicha ishlashda ishlatiladi. Backend (FastAPI/PostgreSQL/algo), wear (Kotlin/Wear OS), web-doctor va web-relative (React/TypeScript/Vite), notifier (Telegram) modullarida kod yozish, klinik mantiqni saqlagan holda funksiya qo'shish, xatolik tuzatish yoki yangi ekran/endpoint yaratishda chaqiriladi. "NAZORAT", "WMAX", "bemor monitoringi", "triage", "baseline", "dekompensatsiya" so'zlari bilan bog'liq.
---

# NAZORAT (WMAX) — Loyiha Skill'i

Bu skill — Umummilliy AI Xakaton (Xorazm) doirasidagi **NAZORAT (WMAX)** loyihasi ustida ishlaganda agentga kontekst va qoidalarni beradi. Kod yozishdan oldin quyidagi arxitektura va klinik mantiqni har doim hisobga ol.

## 1. Tizim arxitekturasi (qisqacha)

```
Aqlli soat (Wear OS/Kotlin) → Android hamroh ilova (Room DB, WorkManager)
    → HTTPS POST /api/v1/ingest → FastAPI backend (PostgreSQL)
        → 5 daqiqalik darcha / Circadian Feature Engine
        → Shaxsiy Baseline Modeli (yo'nalishli z-score)
        → Signal & Triage (green / amber / red)
        → 24 soatlik Patronaj Aktiv Chaqiruv | AI 72-soatlik prognoz
    → web-doctor (shifokor ish stansiyasi) va web-relative (yaqin kishi portali)
    → notifier (Telegram Bot API orqali shoshilinch xabarnoma)
```

## 2. Modul va texnologiyalar xaritasi

| Modul | Stack | Vazifa |
|---|---|---|
| `backend/app/` | FastAPI, SQLAlchemy 2, Pydantic v2, PostgreSQL | REST API, ingestion, bemorlar boshqaruvi, patronaj |
| `backend/algo/` | NumPy, SciPy, scikit-learn (IsolationForest) | Circadian darchalar, yo'nalishli z-score, kompozit xavf |
| `backend/auth/` | python-jose, Passlib, BCrypt | JWT, shifokor/hamshira login, yaqinlar uchun PIN |
| `web-doctor/` | React 19, TypeScript, Vite, Recharts | Triage saralash, 7 kunlik trend, baseline tasdiqlash |
| `web-relative/` | React 19, TypeScript, Vite | Ko'p bemorli almashtirgich, sodda ko'rsatkichlar |
| `wear/` | Kotlin, Android SDK 34, Health Services, Room DB | Soat ilovasi, oflayn buferlash |
| `notifier/` | Python, HTTPX, Telegram Bot API | Xavf signali va patronaj muddati monitoringi |
| `scripts/watch_sim.py` | Python 3, HTTPX | Haqiqiy soatsiz test ma'lumot generatori |

Yangi kod yozganda, mos moduldagi mavjud stack va konventsiyalardan chetga chiqma (masalan, `backend/app/` ichida Pydantic v2 sintaksisidan foydalan, `web-doctor` va `web-relative`da funksional React 19 komponentlari + TypeScript qat'iy tiplashdan foydalan).

## 3. Klinik mantiq — buzilmasligi kerak bo'lgan qoidalar

Har qanday algoritm yoki UI o'zgarishi quyidagi domen qoidalariga zid bo'lmasligi kerak:

1. **Circadian vaqt darchalari** (`Asia/Tashkent` vaqt zonasi): `0: 00-06` (chuqur uyqu), `1: 06-12` (ertalabki faollik), `2: 12-18` (kunduzgi), `3: 18-24` (kechki). Baseline va anomaliya hisob-kitoblari doim shu 4 darchaga nisbatan qilinishi kerak, kun bo'yi yagona o'rtacha emas.
2. **Yo'nalishli z-score**: har parametr faqat klinik xavfli yo'nalishda baholanadi — `SpO2` va `RMSSD` faqat **pasayganda**, `Puls (HR)`, `Teri harorati`, `Nafas soni (RR)` faqat **ko'tarilganda** xavf hisoblanadi. Ikki tomonlama (bidirectional) z-score ishlatish xato.
3. **Yolg'on signallarga qarshi filtr**: bitta 5 daqiqalik og'ish yetarli emas — signal faqat **kamida 3 ta ketma-ket 5 daqiqalik oynada (15 daqiqa)** davom etsa `amber`/`red` statusiga o'tadi ("sustained alert").
4. **`no_data` holati**: ma'lumot 45 daqiqadan ortiq kelmasa, status `green` emas, alohida `no_data` bo'lishi kerak — bu xavfsizlik uchun muhim, chalkashtirib bo'lmaydi.

Yangi trige/xavf logikasi yozayotganda yoki UI'da status ko'rsatayotganda, shu to'rtta qoidani tekshiruv ro'yxati sifatida ishlat.

## 4. API va ma'lumot oqimi konventsiyalari

- Ingest endpoint (`POST /api/v1/ingest`) **idempotent** bo'lishi kerak — takroriy yuborilgan bir xil o'lchov (masalan, tarmoq uzilib qayta urinishda) UNIQUE cheklov orqali dublikat yaratmasligi kerak.
- Android hamroh ilova internet yo'qligida ma'lumotni **Room DB**da buferlaydi va tarmoq tiklanganda **WorkManager** orqali eksponensial backoff bilan qayta yuboradi — backend shu holatni hisobga olib loyihalanadi.
- Rol asoslangan kirish: **shifokor/hamshira** — telefon+parol (JWT); **yaqin kishi (qarovchi)** — telefon+PIN, faqat o'ziga bog'langan bemor(lar) ma'lumotiga kirish huquqi.

## 5. UI/UX yo'nalishi (ikkala frontend uchun)

- **web-doctor**: klinik ish stansiyasi — zichroq ma'lumot, triage ro'yxati (green/amber/red rang kodlash + matn/ikonka bilan takrorlanishi, faqat rangga tayanmasdan), 7 kunlik trend grafiklari (Recharts), baseline tasdiqlash oqimi aniq va tez bo'lishi kerak.
- **web-relative**: oddiy odamlar (ko'pincha yoshi kattaroq yaqinlar) uchun — sodda til, katta shrift, tibbiy atama emas, "bugun yaxshi", "shifokorga xabar berildi" kabi tushunarli holat matnlari. Ko'p bemorli almashtirgich oddiy va tez bo'lsin.
- Ikkala frontendda ham xavf statusini faqat rang bilan emas, label/ikonka bilan birga ko'rsat (rang-ko'rlik uchun).

## 6. Loyihani ishga tushirish (tezkor eslatma)

```bash
# Docker Compose (tavsiya etiladi)
cp .env.example .env
docker compose up --build -d

# Simulyatsiya bilan test qilish
python scripts/watch_sim.py --patient-id p-001-red --mode decompress --interval 2
```

Demo login: shifokor `+998901234567` / `nazorat123`; hamshira `+998901234568` / `nazorat123`; yaqin kishi `+998901112233` / PIN `112233`. Bu ma'lumotlarni faqat lokal demo/test muhitida ishlat, hech qachon production kodga qattiq yozib qo'yma (hardcode qilma) — `.env` yoki seed skriptida saqla.

## 7. Antigravity'da joylashtirish

`.agent/skills/nazorat-wmax/SKILL.md` (loyiha papkasi ichida) — bu skill faqat shu workspace'da ishlaydi, boshqa loyihalarga aralashmaydi.

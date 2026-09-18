# NAZORAT (WMAX) — Aqlli Masofaviy Bemor Monitoringi va Erta Ogohlantirish Tizimi

> **Umummilliy AI Xakaton, Xorazm (17–20 sentabr 2026)**  
> **Trek:** Sog'liqni saqlash va farmatsevtika · **Muammolar:** 11 (24 soatlik aktiv chaqiruv) + 12 (erta dekompensatsiya prognozi)

---

## 📌 Loyiha Haqida

Kasalxonadan (ayniqsa kardiologiya yoki reanimatsiyadan) chiqarilgan og'ir bemorlarga aqlli soat taqiladi. **NAZORAT** tizimi bemorning 5-7 kunlik fiziologik ko'rsatkichlarini o'rganib, uning **shaxsiy normasini (baseline)** shakllantiradi. 

Har qanday xavfli chetlanish kuzatilganda — bemor qayta kasalxonaga tushishidan bir necha kun oldin:
1. **Oilaviy shifokor va hamshiraga** 24 soatlik "Aktiv chaqiruv" patronaj vazifasi yuklanadi;
2. **Bemorning yaqiniga (qarovchisiga)** sodda, tushunarli tilda holat va amaliy tavsiya beriladi;
3. **Telegram boti orqali** tezkor shoshilinch xabarnoma yetkaziladi.

---

## 🏛 Tizim Arxitekturasi

```
┌─────────────────────────┐
│   Aqlli Soat (Wear OS)  │  Samsung Galaxy Watch 5 (Kotlin, Health Services SDK)
│  PPG · HR · SpO2 · Temp │  1 daqiqalik agregatsiya va Bluetooth uzatish
└────────────┬────────────┘
             │ Bluetooth (Data Layer API)
             ▼
┌─────────────────────────┐
│  Android Hamroh Ilovasi │  Room DB oflayn buferlash (internet uzilganda ma'lumot yo'qolmaydi)
│       (wear/phone)      │  WorkManager orqali tarmoq tiklanganda eksponensial sinxronizatsiya
└────────────┬────────────┘
             │ HTTPS REST (POST /api/v1/ingest)
             ▼
┌───────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + PostgreSQL)         │
│  ┌───────────────────────┐   ┌─────────────────────────┐  │
│  │ Ingest API            │ → │ 5 daqiqalik darcha      │  │
│  │ (Idempotent UNIQUE)   │   │ Circadian Feature Engine│  │
│  └───────────────────────┘   └────────────┬────────────┘  │
│                                           ▼               │
│  ┌───────────────────────┐   ┌─────────────────────────┐  │
│  │ Signal & Triage       │ ← │ Shaxsiy Baseline Modeli │  │
│  │ green / amber / red   │   │ Yo'nalishli z-score     │  │
│  └───────────┬───────────┘   └─────────────────────────┘  │
│              ▼                                            │
│  ┌───────────────────────┐   ┌─────────────────────────┐  │
│  │ 24 soatlik Patronaj   │   │ AI 72-soatlik Prognoz   │  │
│  │ Aktiv Chaqiruv (M.11) │   │ Root-Cause tahlil       │  │
│  └───────────────────────┘   └─────────────────────────┘  │
└──────────────┬────────────────────────────┬───────────────┘
               │                            │
               ▼                            ▼
      ┌─────────────────┐          ┌─────────────────┐
      │  web-relative   │          │   web-doctor    │
      │ Qarovchi Mobile │          │ Shifokor & Narsa│
      │  Vite + React   │          │ Klinik Worklist │
      └─────────────────┘          └─────────────────┘
```

---

## 🧩 Asosiy Modullar

| Modul | Texnologiyalar | Vazifasi |
|---|---|---|
| **`backend/app/`** | FastAPI, SQLAlchemy 2, Pydantic v2, PostgreSQL | REST API, Ingestion, Bemorlar boshqaruvi, Aktiv chaqiruv patronaji |
| **`backend/algo/`** | NumPy, SciPy, Scikit-learn (IsolationForest) | Circadian vaqt darchalari (`Asia/Tashkent`), yo'nalishli z-score, ko'p parametrli kompozit xavf hisobi |
| **`backend/auth/`** | Python-jose, Passlib, BCrypt | JWT avtorizatsiya, shifokor/hamshira login, yaqinlar uchun xavfsiz PIN tizimi |
| **`web-doctor/`** | React 19, TypeScript, Vite, Recharts | Shifokor va patronaj hamshirasi ish stansiyasi: Triage saralash, 7 kunlik trend grafiklari, baseline tasdiqlash |
| **`web-relative/`** | React 19, TypeScript, Vite, CSS Cards | Yaqin kishilar uchun mobil portal: ko'p bemorli almashtirgich, oddiy tushunarli ko'rsatkichlar, shifokor bilan tezkor aloqa |
| **`wear/`** | Kotlin, Android SDK 34, Health Services, Room DB | Galaxy Watch 5 soat ilovasi va Android hamroh ilovasi |
| **`notifier/`** | Python, HTTPX, Telegram Bot API | Shoshilinch xavf signallari va 24 soatlik patronaj muddati tugashini monitoring qiluvchi servis |
| **`scripts/watch_sim.py`**| Python 3, HTTPX | Haqiqiy soatsiz barcha fiziologik ssenariylarni test qilish uchun generator-simulyator |

---

## ⚡️ Tezkor Ishga Tushirish (Quickstart)

### 1. Docker Compose orqali (Tavsiya etiladi)

Barcha xizmatlarni (Postgres, API, Notifier, Doctor Web, Relative Web, Caddy) bir buyruq bilan ko'tarish:

```bash
# Loyiha muhiti sozlamalari
cp .env.example .env

# Konteynerlarni ishga tushirish
docker compose up --build -d
```

Servislar quyidagi manzillarda mavjud bo'ladi:
- **API va Swagger Docs:** `http://localhost:8000/docs`
- **Shifokor portali:** `http://localhost/` (yoki Vite porti: `http://localhost:5173`)
- **Yaqin kishi portali:** `http://localhost/r/` (yoki Vite porti: `http://localhost:5174`)

---

### 2. Lokal Dasturchi Rejimida Ishga Tushirish

#### Backend & Ma'lumotlar Bazasi:
```bash
# 1. PostgreSQL ishga tushirish
docker compose up -d postgres

# 2. Virtual muhit va bog'liqliklar
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r backend/algo/requirements.txt
pip install -r backend/auth/requirements.txt

# 3. API serverni ishga tushirish (root papkadan)
export PYTHONPATH="$PWD:$PWD/backend:$PWD/contracts"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend dasturlari:
```bash
# Web-Doctor (Shifokor portali)
cd web-doctor
npm install
npm run dev # http://localhost:5173

# Web-Relative (Yaqin kishi portali)
cd web-relative
npm install
npm run dev # http://localhost:5174
```

---

## 🔑 Demo Kirish Ma'lumotlari

Tizim oldindan tayyorlangan haqiqiy klinik ssenariylar bilan jihozlangan:

| Rol | Telefon / Login | Parol / PIN | Izoh |
|---|---|---|---|
| **Shifokor** | `+998901234567` | `nazorat123` | Kardiolog, bemorlar bo'yicha to'liq klinik boshqaruv |
| **Patronaj Hamshirasi** | `+998901234568` | `nazorat123` | 24 soatlik chaqiruvlarni tasdiqlovchi xodim |
| **Yaqin Kishi (Qarovchi)** | `+998901112233` | PIN: `112233` | Ota/ona ko'rsatkichlarini kuzatuvchi oila a'zosi |

---

## 🩺 Klinik Mantiq va Domen Qoidalari

1. **Circadian Vaqt Darchalari (`Asia/Tashkent`):**
   - Inson fiziologiyasi 4 ta ritmga bo'lingan holda baholanadi: `0: 00–06` (chuqur uyqu), `1: 06–12` (ertalabki faollik), `2: 12–18` (kunduzgi), `3: 18–24` (kechki).
2. **Yo'nalishli z-score og'ishi:**
   - Har bir parametr faqat klinik xavf yo'nalishida tahlil qilinadi: `SpO2` va `RMSSD` faqat pasaysa xavf; `Puls (HR)`, `Teri harorati`, `Nafas soni (RR)` faqat ko'tarilsa xavf.
3. **Yolg'on signallarga qarshi filtr (Sustained Alert):**
   - Bir martalik sakrash signal keltirib chiqarmaydi. Og'ish **kamida 3 ta ketma-ket 5 daqiqalik oynada (15 daqiqa)** davom etgandagina `amber` yoki `red` statusiga o'tadi.
4. **45 daqiqalik ma'lumot kelmasligi:**
   - Agar aqlli soat yechilsa yoki ma'lumot uzilishi 45 daqiqadan oshsa, holat yashil emas, **`no_data`** holatiga o'tadi.

---

## ⌚️ Aqlli Soat Simulyatsiyasi (`scripts/watch_sim.py`)

Haqiqiy aqlli soatsiz backendga real vaqt rejimida o'lchovlar oqimini yuborish uchun:

```bash
# Sog'lom bemor oqimini simulyatsiya qilish:
python scripts/watch_sim.py --patient-id p-002-green --mode normal --interval 5

# Dekompensatsiya (xavfli holat) signalini chaqirish:
python scripts/watch_sim.py --patient-id p-001-red --mode decompress --interval 2

# Oflayn Room DB bufer mexanizmini tekshirish:
python scripts/watch_sim.py --mode offline-test
```

---

## 📄 Litsenziya

Loyiha Umummilliy AI Xakaton doirasida tibbiyot tizimini raqamlashtirish maqsadida ishlab chiqilgan.

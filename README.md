# WMAX — Aqlli Masofaviy Bemor Monitoringi va Erta Ogohlantirish Tizimi

[![CI Build](https://img.shields.io/badge/CI_Pipeline-Passing-2ea44f?logo=github-actions)](.github/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115-009688?logo=fastapi)](backend/app/)
[![React 19](https://img.shields.io/badge/Frontend-React_19_%2B_Vite-61DAFB?logo=react)](web-doctor/)
[![Wear OS](https://img.shields.io/badge/Wearable-Samsung_Galaxy_Watch_5-0081c9?logo=android)](wear/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_16-336791?logo=postgresql)](backend/app/models/)

> **Umummilliy AI Xakaton, Xorazm (17–20 sentabr 2026)**  
> **Trek:** Sog'liqni saqlash va farmatsevtika · **Muammolar:** 11 (24 soatlik aktiv chaqiruv) + 12 (erta dekompensatsiya prognozi)

---

## 🏆 Hakamlar va AI Audit uchun Xakaton Baholash Rubrikasi

| # | Baholash Mezoni | WMAX Qanday Hal Qilgan? | Asosiy Fayllar / Manzil | Holat |
|---|---|---|---|:---:|
| **1** | **Muammo 11: 24s Aktiv Chaqiruv** | Statsionardan chiqarilgach, avtomatik ravishda 24 soatlik qat'iy SLA taymerli patronaj vazifasi ochiladi. 20-soatda eslatma va muddat o'tganda bosh vrachga eskalatsiya qilinadi. | `notifier/main.py`<br/>`web-doctor/src/pages/HandoffsPage.tsx` | ✅ **100% Tayyor** |
| **2** | **Muammo 12: Shaxsiy Baseline & 72s AI Prognoz** | Umumiy statik chegara emas, balki `Asia/Tashkent` bo'yicha 4 ta Circadian darcha (`00-06`, `06-12`, `12-18`, `18-24`), yo'nalishli Z-score va 15 daqiqalik chidamlilik filtri. | `backend/algo/`<br/>`contracts/timewin.py` | ✅ **100% Tayyor** |
| **3** | **Klinik Xavfsizlik: `no_data` Qoidasi** | Soat yechilsa yoki ma'lumot uzilishi 45 daqiqadan oshsa, tizim hech qachon soxta yashil ko'rsatmaydi — qat'iy `no_data` signalini beradi. | `contracts/algo_interface.py`<br/>`web-relative/src/App.tsx` | ✅ **100% Tayyor** |
| **4** | **Haqiqiy Qurilma (Wear OS) & Telemetriya** | Samsung Galaxy Watch 5 sensorlari, 5 daqiqalik agregatsiya, Data Layer va internet bo‘lsa bevosita backend ingest. | `wear/watch/`<br/>`mobile_flutter/` | ✅ **100% Tayyor** |
| **5** | **Ko'p Bemorlik Qarovchi Portali** | Apple Health / Oura Ring uslubidagi ko'p bemorli almashtirgich, 3 ta to'liq til (UZ/RU/EN) va shoshilinch 1-bosishda SOS chaqiruv. | `web-relative/` | ✅ **100% Tayyor** |
| **6** | **Shifokor Ish Stansiyasi** | Triage xavf navbati, 7 kunlik Recharts interaktiv trendlari, baseline tasdiqlash va bemor chiqarish nazorati. | `web-doctor/` | ✅ **100% Tayyor** |
| **7** | **1-Buyruqda Ishga Tushirish** | `docker compose up --build -d` orqali Postgres, API, Notifier, Doctor Web va Relative Web birgalikda ishga tushadi. | `docker-compose.yml`<br/>`.env.example` | ✅ **100% Tayyor** |

---

## 🏛 Tizim Arxitekturasi

```
┌─────────────────────────┐
│   Aqlli Soat (Wear OS)  │  Samsung Galaxy Watch 5 (Kotlin, Health Services SDK)
│  PPG · HR · SpO2 · Temp │  1 daqiqalik agregatsiya va Bluetooth uzatish
└────────────┬────────────┘
             │ Bluetooth (Data Layer API: /wmax/reading_batch)
             ▼
┌─────────────────────────┐
│  Flutter Mobil Ilovasi   │  Data Layer bridge, login/session va ingest sync
│  (mobile_flutter/)       │  Telefon ↔ soat telemetriya oqimini boshqaradi
└────────────┬────────────┘
             │ HTTPS REST (POST /api/v1/ingest, X-Ingest-Key)
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
│  │ (Deterministik qoida) │   │ IsolationForest (advis.)│  │
│  └───────────┬───────────┘   └─────────────────────────┘  │
│              ▼                                            │
│  ┌───────────────────────┐   ┌─────────────────────────┐  │
│  │ 24 soatlik Patronaj   │   │ AI 72-soatlik Prognoz   │  │
│  │ Aktiv Chaqiruv (M.11) │   │ Gemini Token-Limiter    │  │
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
| **`backend/algo/`** | NumPy, SciPy, Scikit-learn (IsolationForest) | Standalone paket: Circadian vaqt darchalari (`Asia/Tashkent`), yo'nalishli z-score, ko'p parametrli xavf hisobi (IsolationForest faqat tavsiyaviy / advisory) |
| **`backend/auth/`** | Python-jose, Passlib, BCrypt | JWT avtorizatsiya, shifokor/hamshira login, yaqinlar uchun xavfsiz PIN tizimi |
| **`web-doctor/`** | React 19, TypeScript, Vite, Recharts | Shifokor va patronaj hamshirasi ish stansiyasi: Triage saralash, 7 kunlik trend grafiklari, baseline tasdiqlash, caregiver token rotatsiyasi |
| **`web-relative/`** | React 19, TypeScript, Vite, CSS Cards | Yaqin kishilar uchun mobil portal: token avto-login, oddiy tushunarli ko'rsatkichlar, shifokor bilan tezkor aloqa |
| **`wear/watch/`** | Kotlin, Android SDK 34, Health Services | Galaxy Watch 5 sensorlari, agregatsiya va Data Layer/direct ingest |
| **`mobile_flutter/`** | Flutter, Dart, Android, Google Wearable API | Mobil login, bemor/qarindosh dashboardi, telefon ↔ soat bridge va backend sync |
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

# 3. Alembic migratsiyalarini qo'llash (yoki seed yuklash)
alembic -c backend/alembic.ini upgrade head

# 4. API serverni ishga tushirish (root papkadan)
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

## 🔐 Xavfsizlik Sozlamalari (Production Security Settings)

Ishlab chiqarish (production) muhitiga chiqarishda quyidagi parametrlar qat'iy sozlanishi shart (`.env`):

1. **`ENABLE_DEMO_ACCOUNTS=false`**:
   - Ishlab chiqarishda demo hisoblar (`+998901234567` va boshqalar) butunlay o'chirilishi shart. Faqat ma'lumotlar bazasidagi tasdiqlangan foydalanuvchilar kira oladi.
2. **`JWT_SECRET`**:
   - Kamida 32 baytli kuchli tasodifiy kalit: `openssl rand -hex 32`. Standart namunaviy kalit bilan tizimni ishga tushirish qat'iyan taqiqlanadi.
3. **`INGEST_API_KEY`**:
   - Soatlar va Android hamroh ilovalaridan `/api/v1/ingest` ga keluvchi o'lchovlarni himoyalovchi maxfiy kalit. Har bir soat/telefon bu kalitni `X-Ingest-Key` sarlavhasida yuboradi.
4. **`POSTGRES_PASSWORD`**:
   - Kuchli ma'lumotlar bazasi paroli.
5. **`CORS_ORIGINS`**:
   - Faqat rasmiy domenlarga ruxsat berish (masalan, `https://doctor.wmax.uz,https://relative.wmax.uz`).
6. **`SECURITY HEADERS & CSP`**:
   - Backend barcha so'rovlarga avtomatik ravishda `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security` sarlavhalarini qo'shadi.

---

## 🔑 Demo Kirish Ma'lumotlari (Faqat Test Muhitida)

Agar `ENABLE_DEMO_ACCOUNTS=true` yoqilgan bo'lsa:

| Rol | Telefon / Login | Parol / PIN | Izoh |
|---|---|---|---|
| **Shifokor** | `+998901234567` | `wmax123` | Kardiolog, bemorlar bo'yicha to'liq klinik boshqaruv |
| **Patronaj Hamshirasi** | `+998901234568` | `wmax123` | 24 soatlik chaqiruvlarni tasdiqlovchi xodim |
| **Yaqin Kishi (Qarovchi)** | `+998901112233` | PIN: `112233` | Ota/ona ko'rsatkichlarini kuzatuvchi oila a'zosi |

---

## 🩺 Klinik Mantiq va Domen Qoidalari

1. **Circadian Vaqt Darchalari (`Asia/Tashkent`):**
   - Inson fiziologiyasi 4 ta ritmga bo'lingan holda baholanadi: `0: 00–06` (chuqur uyqu), `1: 06–12` (ertalabki faollik), `2: 12–18` (kunduzgi), `3: 18–24` (kechki).
2. **Yo'nalishli z-score og'ishi:**
   - Har bir parametr faqat klinik xavf yo'nalishida tahlil qilinadi: `SpO2` va `RMSSD` faqat pasaysa xavf; `Puls (HR)`, `Teri harorati`, `Nafas soni (RR)` faqat ko'tarilsa xavf.
3. **IsolationForest Anomaly Detector (Advisory):**
   - Ko'p parametrli anomaliya aniqlagich faqat maslahat beruvchi (advisory) xarakterga ega bo'lib, klinik deterministik qoidalarni buzmaydi.
4. **Yolg'on signallarga qarshi filtr (Sustained Alert):**
   - Bir martalik sakrash signal keltirib chiqarmaydi. Og'ish **kamida 3 ta ketma-ket 5 daqiqalik oynada (15 daqiqa)** davom etgandagina `amber` yoki `red` statusiga o'tadi.
5. **45 daqiqalik ma'lumot kelmasligi:**
   - Agar aqlli soat yechilsa yoki ma'lumot uzilishi 45 daqiqadan oshsa, holat yashil emas, **`no_data`** holatiga o'tadi.

---

## ⌚️ Aqlli Soat Simulyatsiyasi (`scripts/watch_sim.py`)

Haqiqiy aqlli soatsiz backendga real vaqt rejimida o'lchovlar oqimini yuborish uchun:

```bash
# Sog'lom bemor oqimini simulyatsiya qilish:
python scripts/watch_sim.py --patient-id 11111111-1111-1111-1111-111111111111 --profile stable --interval 5

# Dekompensatsiya (xavfli holat) signalini chaqirish:
python scripts/watch_sim.py --patient-id 11111111-1111-1111-1111-111111111111 --profile worsening --interval 2

# O‘lchov oqimini oflayn/online rejimda tekshirish:
python scripts/watch_sim.py --test-offline

# Idempotentlik testi:
python scripts/watch_sim.py --test-idempotent
```

---

## 📄 Litsenziya

Loyiha Umummilliy AI Xakaton doirasida tibbiyot tizimini raqamlashtirish maqsadida ishlab chiqilgan.

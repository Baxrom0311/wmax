# A5: wear — Bajarish Rejasi (PLAN.md)

Papkalar: `wear/` va `scripts/watch_sim.py`  
Mas'ul: **A5 agenti**  
Chegaralar: Faqat `wear/` va `scripts/watch_sim.py`. Backend, frontendlarga tegmaydi!

---

## 1. Asosiy Vazifa
Qurilma qatlami — aqlli soat (Galaxy Watch 5 / Wear OS) datchiklaridan o'lchovlarni yig'ish va telefon orqali backendga uzatish.  
**Ish tartibi TESKARI:** avval noutbuk simulyatori (`scripts/watch_sim.py`), keyin Android ilovalari. Bu soatsiz ham quvurning ishlashini 100% kafolatlaydi.

---

## 2. Fayllar Tuzilmasi va Qadamlar

### 2.1 Noutbuk Simulyatori (`scripts/watch_sim.py`) — BIRINCHI QADAM
- [ ] `scripts/watch_sim.py`:
  - Python skripti, `httpx` orqali `POST /api/v1/ingest` ga so'rov yuboradi.
  - Sxema: `contracts/openapi.yaml` dagi `IngestBatch` va `ReadingIn` ga 100% mos.
  - Parametrlar: `--patient-id`, `--base-url`, `--interval`.
  - Offline navbatni taqlid qilish: Server ishlamay qolsa xotirada saqlash va keyingi urinishda batch bilan yuborish.
  - A1 ning idempotentligini tekshirish: Bir xil `(patient_id, ts)` juftligini qayta yuborib ko'rish.

### 2.2 Wear OS Soat Ilovasi (`wear/watch/`)
- [ ] Kotlin / Gradle loyihasi:
  - SDK: `androidx.health:health-services-client`.
  - Datchiklar:
    - `HEART_RATE_BPM` (uzluksiz).
    - `SPO2` (davriy).
    - Akselerometr / `STEPS_DAILY` (faollik).
    - Off-body aniqlash (`worn` flagi).
  - Agregatsiya: 1 daqiqalik darchalarda yig'ish, so'ngra 5 daqiqalik yig'indi qilib Data Layer API orqali telefonga jo'natish.
  - Soat ekrani: joriy puls, ulanish holati ("Ulangan" / "Ulanmagan").

### 2.3 Android Telefon Ilovasi (`wear/phone/`)
- [ ] Kotlin / Gradle loyihasi:
  - Data Layer API orqali soatdan paketlarni qabul qilish.
  - **Room DB buferi:** Internet bo'lmaganda barcha o'lchovlarni xavfsiz saqlash.
  - `WorkManager`: Tarmoq paydo bo'lganda eksponensial qayta urinish bilan backend `POST /api/v1/ingest` ga yuborish.
  - Telefon ekrani: ulanish holati, navbatdagi yozuvlar soni, oxirgi sinxron vaqti.

### 2.4 Hujjatlashtirish
- [ ] `wear/README.md`:
  - Qaysi Android Studio versiyasi kerakligi.
  - SDK sozlamalari, Wear OS emulatorida sinash qadamlari.
  - APK build qilish buyruqlari.

---

## 3. Majburiy Checkpoint
`scripts/watch_sim.py` backendga muvaffaqiyatli ma'lumot uzatgach to'xtab hisobot berish. Shundan keyin Android qismi yoziladi.

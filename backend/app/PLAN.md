# A1: backend-core — Bajarish Rejasi (PLAN.md)

Papka: `backend/app/`  
Mas'ul: **A1 agenti**  
Chegaralar: Faqat `backend/app/`, `backend/Dockerfile`, `backend/requirements.txt`. Boshqa papkalarga tegilmaydi!

---

## 1. Asosiy Vazifa
FastAPI async serverini qurish, PostgreSQL bilan SQLAlchemy 2.0 orqali ishlash, soatdan kelayotgan o'lchovlarni idempotent qabul qilish (`/ingest`), klinik signal quvurini yurgizish (A2 funksiyalarini chaqirib) va frontendlarga API taqdim etish.

---

## 2. Fayllar Tuzilmasi va Qadamlar

### 2.1 Konfiguratsiya va Ma'lumotlar Bazasi
- [ ] `backend/app/core/config.py`:
  - `pydantic-settings` orqali `.env` dan yuklanadi: `DATABASE_URL`, `TZ_LOCAL` (Asia/Tashkent), `NO_DATA_MINUTES` (45), `CONSECUTIVE_WINDOWS` (3), `ALERT_COOLDOWN_HOURS` (6).
- [ ] `backend/app/core/db.py`:
  - `create_async_engine(settings.DATABASE_URL, echo=False)`.
  - `async_sessionmaker(engine, expire_on_commit=False)`.
  - `get_session()` dependency.

### 2.2 ORM Modellar (`backend/app/models/`)
> MUHIM: `contracts/schema.sql` ga 100% mos bo'lsin. Alembic ishlatilmaydi, `Base.metadata.create_all()` chaqirilmaydi.
- [ ] `models/base.py`: SQLAlchemy `DeclarativeBase`.
- [ ] `models/user.py`: `User` (id UUID, full_name, phone UNIQUE, password_hash, role: doctor/nurse/admin, district).
- [ ] `models/patient.py`: `Patient` (id UUID, full_name, age, sex, diagnosis, district, discharge_date, phase: calib/learning/full, baseline_approved_by/at, doctor_id, nurse_id, device_id).
- [ ] `models/relative.py`: `Relative` (id UUID, patient_id FK, full_name, phone UNIQUE, pin_hash, access_token UNIQUE, telegram_chat_id).
- [ ] `models/reading.py`: `Reading` (id BIGSERIAL, patient_id, ts UTC, hr_mean, hr_min, hr_max, rmssd, sdnn, spo2, skin_temp, steps, rr_est, sleep_frag, worn, battery, `UNIQUE(patient_id, ts)`).
- [ ] `models/baseline.py`: `Baseline` (id BIGSERIAL, patient_id, param, time_window 0..3, median, mad, n_samples, `UNIQUE(patient_id, param, time_window)`).
- [ ] `models/alert.py`: `Alert` (id BIGSERIAL, patient_id, ts, level: green/amber/red/no_data, composite_score, triggered_params JSONB, anomaly_score, reason, `UNIQUE(patient_id, ts)`).
- [ ] `models/task.py`: `Task` (id BIGSERIAL, patient_id, doctor_id, type: active_call/red_alert, status: created..overdue, due_at, reminded_at, escalated_at, confirmed_at, note, alert_id).
- [ ] `models/notification.py`: `Notification` (id BIGSERIAL, patient_id, channel, recipient, level, sent_at).
- [ ] `models/refresh_token.py`: `RefreshToken` (token_hash, user_id, relative_id, expires_at, revoked).

### 2.3 Pydantic Sxemalari (`backend/app/schemas/`)
> `contracts/openapi.yaml` komponentlaridan aynan ko'chiriladi.
- [ ] `schemas/reading.py`: `ReadingIn`, `IngestBatch`, `IngestResult`.
- [ ] `schemas/patient.py`: `PatientSummary`, `PatientDetail`, `ParamSeries`, `SeriesPoint`, `Trend`.
- [ ] `schemas/alert.py`: `Alert`, `AlertLevel`.
- [ ] `schemas/task.py`: `Task`, `TaskStatus`.
- [ ] `schemas/relative.py`: `RelativeView`.
- [ ] `schemas/auth.py`: `TokenPair`.

### 2.4 Ingest API va Signal Quvuri
- [ ] `backend/app/api/ingest.py`:
  - `POST /api/v1/ingest`
  - Idempotent insert: `insert(Reading).values(...).on_conflict_do_nothing(index_elements=['patient_id', 'ts'])`.
  - Qaytaradi: `{ accepted, duplicates, latest_level }`.
  - Kiritilgach, `services.pipeline.run_pipeline_for_patient(patient_id)` ni chaqiradi.
- [ ] `backend/app/services/pipeline.py`:
  - Bemorning oxirgi 7 kunlik o'lchovlarini o'qib, `contracts/algo_interface.py` dagi `ReadingVec` ro'yxatiga o'giradi.
  - A2 funksiyalarini chaqiradi:
    - `from algo.baseline import compute_baselines, compute_zscores`
    - `from algo.signal import evaluate_alert`
    - `from algo.trend import compute_trend`
    - `import timewin`
  - Agar `timewin.is_no_data(last_reading_ts, now)` bo'lsa -> level `no_data`.
  - Natijalarni `baselines` va `alerts` jadvallariga saqlaydi.

### 2.5 Bemorlar, Topshiriqlar va Yaqin Kishi API
- [ ] `backend/app/api/patients.py`:
  - `GET /api/v1/patients`: Worklist tartibi: `red` > `no_data` > `amber` > `green`.
  - `GET /api/v1/patients/{id}`: Oxirgi 7 kunlik `ParamSeries`, `baseline_median/low/high`, `deviated_ranges`, `alerts`, `tasks`.
  - `POST /api/v1/patients/{id}/discharge`: `discharge_date` qo'yadi va 24 soatlik `active_call` Task ochadi (`due_at = now + 24h`).
  - `POST /api/v1/patients/{id}/approve-baseline`: phase 'learning' -> 'full', `baseline_approved_by/at` to'ldiriladi.
- [ ] `backend/app/api/tasks.py`:
  - `GET /api/v1/tasks`: Topshiriqlar ro'yxati (status filtri bilan).
  - `POST /api/v1/tasks/{id}/confirm`: `status = 'done'`, `confirmed_at = now()`, shifokor izohi (`note`).
- [ ] `backend/app/api/relatives.py`:
  - `GET /api/v1/relatives/{token}/view`: Yaqin kishi ekrani ma'lumotlari (`RelativeView`), 7 kunlik normallashtirilgan (0..1) `sparkline` massivi.
- [ ] `backend/app/main.py`:
  - FastAPI ilovasi, CORS sozlamalari (`5173`, `5174`), routerlarni ulash, `GET /api/v1/health`.
  - `from auth.deps import auth_router; app.include_router(auth_router)`.

---

## 3. Majburiy Checkpoint
`/health` va `GET /api/v1/patients` endpoints seed ma'lumotlari bilan ishlagach to'xtab hisobot berish.

-- =====================================================================
-- NAZORAT — yagona DB haqiqati (single source of truth).
-- MUZLATILGAN. Hech bir agent bu faylni o'zgartirmaydi.
-- Alembic ishlatilmaydi: sxema o'zgarsa -> docker compose down -v && up
-- SQLAlchemy modellari (backend/app/models) SHU faylga MOS bo'lishi shart.
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------- enum'lar (nomlar ingliz tilida, UI tarjimasi i18n da) ----------
CREATE TYPE user_role     AS ENUM ('doctor', 'nurse', 'admin');
CREATE TYPE patient_phase AS ENUM ('calib', 'learning', 'full');
CREATE TYPE alert_level   AS ENUM ('green', 'amber', 'red', 'no_data');
CREATE TYPE task_type     AS ENUM ('active_call', 'red_alert');
CREATE TYPE task_status   AS ENUM ('created', 'sent', 'seen', 'done', 'overdue');
CREATE TYPE baseline_param AS ENUM
  ('hr_mean', 'rmssd', 'spo2', 'skin_temp', 'sleep_frag', 'steps', 'rr_est');

-- ---------- foydalanuvchilar (A6 auth) ----------
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name     TEXT        NOT NULL,
    phone         TEXT        NOT NULL UNIQUE,      -- login: +998XXXXXXXXX
    password_hash TEXT        NOT NULL,             -- bcrypt
    role          user_role   NOT NULL,
    district      TEXT,                             -- Urganch, Xiva, Xonqa, Shovot
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- bemorlar ----------
CREATE TABLE patients (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name      TEXT          NOT NULL,
    age            SMALLINT      NOT NULL CHECK (age BETWEEN 0 AND 120),
    sex            CHAR(1)       NOT NULL CHECK (sex IN ('m', 'f')),
    diagnosis      TEXT          NOT NULL,
    district       TEXT          NOT NULL,
    discharge_date DATE,
    phase          patient_phase NOT NULL DEFAULT 'calib',
    phase_since    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    baseline_approved_by UUID REFERENCES users(id),   -- odam halqada: shifokor tasdiqlaydi
    baseline_approved_at TIMESTAMPTZ,
    doctor_id      UUID REFERENCES users(id),
    nurse_id       UUID REFERENCES users(id),
    device_id      TEXT,                              -- soat identifikatori
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX idx_patients_doctor ON patients(doctor_id);

-- ---------- yaqin kishilar ----------
CREATE TABLE relatives (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id       UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    full_name        TEXT NOT NULL,
    phone            TEXT NOT NULL UNIQUE,       -- login: telefon + PIN
    pin_hash         TEXT,                       -- bcrypt(6 xonali PIN)
    telegram_chat_id BIGINT,
    access_token     TEXT NOT NULL UNIQUE,       -- /r/{token} manzili uchun (>=32 bayt)
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_relatives_patient ON relatives(patient_id);

-- ---------- o'lchovlar (5 daqiqalik agregat) ----------
-- ts ALWAYS UTC. Mahalliy oyna contracts/timewin.py orqali hisoblanadi.
CREATE TABLE readings (
    id         BIGSERIAL PRIMARY KEY,
    patient_id UUID        NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    ts         TIMESTAMPTZ NOT NULL,
    hr_mean    REAL,
    hr_min     REAL,
    hr_max     REAL,
    rmssd      REAL,
    sdnn       REAL,
    spo2       REAL,
    skin_temp  REAL,
    steps      INTEGER,
    rr_est     REAL,
    sleep_frag REAL,          -- uyqu uzilishi: uyg'onishlar soni / soat
    worn       BOOLEAN     NOT NULL DEFAULT TRUE,
    battery    SMALLINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_reading UNIQUE (patient_id, ts)   -- IDEMPOTENT INGEST
);
CREATE INDEX idx_readings_patient_ts ON readings(patient_id, ts DESC);

-- ---------- shaxsiy baza ----------
CREATE TABLE baselines (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    param       baseline_param NOT NULL,
    time_window SMALLINT NOT NULL CHECK (time_window BETWEEN 0 AND 3),
    median      REAL NOT NULL,
    mad         REAL NOT NULL,
    n_samples   INTEGER NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_baseline UNIQUE (patient_id, param, time_window)
);

-- ---------- signallar ----------
CREATE TABLE alerts (
    id               BIGSERIAL PRIMARY KEY,
    patient_id       UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    ts               TIMESTAMPTZ NOT NULL,
    level            alert_level NOT NULL,
    composite_score  REAL NOT NULL DEFAULT 0,
    triggered_params JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {"spo2": -2.4, "hr_mean": 3.1}
    anomaly_score    REAL,            -- ADVISORY: IsolationForest, qarorga ta'sir qilmaydi
    reason           TEXT,            -- ingliz tilida qisqa sabab kodi
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_alert UNIQUE (patient_id, ts)
);
CREATE INDEX idx_alerts_patient_ts ON alerts(patient_id, ts DESC);

-- ---------- topshiriqlar (aktiv chaqiruv + qizil signal) ----------
CREATE TABLE tasks (
    id           BIGSERIAL PRIMARY KEY,
    patient_id   UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id    UUID REFERENCES users(id),
    type         task_type   NOT NULL,
    status       task_status NOT NULL DEFAULT 'created',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    due_at       TIMESTAMPTZ NOT NULL,
    reminded_at  TIMESTAMPTZ,          -- 20-soat eslatmasi yuborilgani
    escalated_at TIMESTAMPTZ,          -- 24-soat eskalatsiyasi
    confirmed_at TIMESTAMPTZ,
    note         TEXT,
    alert_id     BIGINT REFERENCES alerts(id)
);
CREATE INDEX idx_tasks_open ON tasks(status, due_at) WHERE status IN ('created','sent','seen');

-- ---------- yuborilgan xabarlar (cooldown nazorati uchun) ----------
CREATE TABLE notifications (
    id         BIGSERIAL PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    channel    TEXT NOT NULL,          -- 'telegram'
    recipient  TEXT NOT NULL,          -- chat_id yoki user id
    level      alert_level NOT NULL,
    sent_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notifications_patient ON notifications(patient_id, sent_at DESC);

-- ---------- refresh tokenlar ----------
CREATE TABLE refresh_tokens (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    relative_id UUID REFERENCES relatives(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_owner CHECK (num_nonnulls(user_id, relative_id) = 1)
);

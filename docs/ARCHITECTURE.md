# WMAX — Arxitektura va Qurish Spetsifikatsiyasi

> **Holat:** qurish uchun spetsifikatsiya · 2026-09-22
> **Auditoriya:** kod yozadigan agentlar va dasturchilar
>
> | Hujjat | Javob beradi |
> |---|---|
> | [`IDEOLOGY.md`](./IDEOLOGY.md) | **Nega** shunday |
> | **`ARCHITECTURE.md`** (shu) | **Nima** quriladi va **qanday** |
> | [`SDLC.md`](./SDLC.md) | O'zgarish qanday tekshiriladi, chiqariladi va tiklanadi |

## Bu hujjatdan qanday foydalanish

Bu hujjat maqsad arxitekturasini belgilaydi; mavjud kod, migratsiya yoki
ma'lumotni avtomatik o'chirish rejasi emas. Amaldagi o'zgarishlar uchun
`SDLC.md` jarayoniga amal qiling. Mavjud ma'lumotga ta'sir qiladigan tozalash
oldidan audit, zaxira nusxa va alohida tasdiq shart.

1. Kod yozishdan oldin `IDEOLOGY.md` dagi tegishli bandni o'qing
2. Har bir modul ta'rifida **qaysi bandni bajarishi** yozilgan
3. Ideologiya bandiga zid kod — **qabul qilinmaydi**, sababi qanday bo'lishidan qat'i nazar
4. Spetsifikatsiyada yo'q narsani o'zingizdan qo'shmang — so'rang

---

## Mundarija

| # | Bo'lim |
|---|---|
| 1 | [Asosiy qarorlar — qisqa ro'yxat](#1-asosiy-qarorlar) |
| 2 | [Qatlamlar va yo'nalish](#2-qatlamlar-va-yonalish) |
| 3 | [Katalog skeleti](#3-katalog-skeleti) |
| 4 | [`domain/` — ideologiya qoidalari](#4-domain--ideologiya-qoidalari) |
| 5 | [Ma'lumot modeli](#5-malumot-modeli) |
| 6 | [Kirish nazorati](#6-kirish-nazorati) |
| 7 | [Nima saqlanadi, nima qayta yoziladi](#7-nima-saqlanadi-nima-qayta-yoziladi) |
| 8 | [Qurish tartibi](#8-qurish-tartibi) |
| 9 | [Review mezonlari](#9-review-mezonlari) |
| 10 | [Hali kelishilmagan](#10-hali-kelishilmagan) |
| 11 | [Qurilma ma'lumot yo'li](#11-qurilma-malumot-yoli) |
| 12 | [Qurilma autentifikatsiyasi](#12-qurilma-autentifikatsiyasi) |
| 13 | [API kontrakti](#13-api-kontrakti) |
| 14 | [Postgres RLS](#14-postgres-rls--oxirgi-himoya) |
| 15 | [Signal → vazifa → eskalatsiya](#15-signal--vazifa--eskalatsiya) |
| 16 | [Mavjud ma'lumot](#16-mavjud-malumot-bilan-nima-boladi) |
| 17 | [Partitsiya boshqaruvi](#17-partitsiya-boshqaruvi) |
| 18 | [Ma'lumot oqimlari](#18-malumot-oqimlari) |
| 19 | [Frontend qamrovi](#19-frontend-qamrovi) |
| 20 | [Test strategiyasi](#20-test-strategiyasi) |
| 21 | [Tashqi integratsiyalar](#21-tashqi-integratsiyalar) |
| 22 | [Ishchi agentlar uchun topshiriqlar](#22-ishchi-agentlar-uchun-topshiriqlar) |

---

# 1. Asosiy qarorlar

Butun arxitektura shu oltita qarordan kelib chiqadi. Qolgan hamma narsa — tafsilot.

### 1.1 Bemorning egasi yo'q

`patients` jadvalida `tenant_id` **YO'Q**. Bog'lanish a'zolik orqali.

```
patients (egasiz)
   ▲
   ├── patient_memberships   ← klinika, vaqtli, institutsional
   └── patient_access        ← qarovchi, muddatsiz, shaxsiy
```

### 1.2 Tenant — faqat klinika

B2C da tenant **yo'q**. Oila bemorga to'g'ridan-to'g'ri `patient_access`
orqali ulanadi. Obuna bemorda.

| | B2B | B2C |
|---|---|---|
| Tenant | ✅ klinika | ❌ yo'q |
| Ulanish | `patient_memberships` | `patient_access` |
| To'lov | `tenant_licences` (bemor-kun) | `patient_subscriptions` |

### 1.3 Hisob rolsiz

`accounts` jadvalida **rol yo'q**. Rol — munosabatdan kelib chiqadi:

```
Zilola (bitta hisob, bitta telefon)
  ├── tenant_members → Urganch OvaBMU · hamshira
  └── patient_access → o'z onasi · qarovchi
```

Bugungi kodda bu ifodalanmaydi: `users.role` bitta qiymat, shuning uchun
hamshira o'z onasini kuzata olmaydi.

### 1.4 Bir vaqtda bitta parvarish egasi

`patient_memberships` da `kind='care'` va `revoked_at IS NULL` bo'lgan
**ko'pi bilan bitta** qator. DB darajasida cheklov bilan majburlanadi.

### 1.5 Ikki huquq manbai

| Manba | Nimani yoqadi |
|---|---|
| Parvarish egasining litsenziyasi | **Klinik oqim** — ingest, signal, vazifa, eskalatsiya |
| Bemorning obunasi | **Oilaning ko'rinishi** — tarix, AI, PDF, real vaqt |

Ular hech qachon bir-birini bloklamaydi (`D2`).

### 1.6 Qoidalar `domain/` da, sochilmagan

`D1`–`D5` va `F2`, `F4`, `E5` — har biri **bitta sof funksiya**.
DB'siz, HTTP'siz, to'liq testlanadigan.

---

# 2. Qatlamlar va yo'nalish

```
┌─────────────────────────────────────────────┐
│  api/          HTTP, validatsiya, auth      │
├─────────────────────────────────────────────┤
│  services/     use-case orkestratsiya       │
├─────────────────────────────────────────────┤
│  repositories/ DB, MAJBURIY tenant filtri   │
├─────────────────────────────────────────────┤
│  domain/       sof qoidalar — hech narsani  │
│                bilmaydi                     │
├─────────────────────────────────────────────┤
│  algo/         sof klinik matematika        │
└─────────────────────────────────────────────┘
              yo'nalish FAQAT pastga
```

## Qatlam qoidalari

| Qatlam | Mumkin | **Taqiqlanadi** |
|---|---|---|
| `api/` | `services/` ni chaqirish | DB so'rovi, biznes qarori |
| `services/` | `repositories/`, `domain/`, `algo/` | HTTP obyektlari, qoida yozish |
| `repositories/` | SQLAlchemy | Biznes qarori, `services/` ni chaqirish |
| `domain/` | Sof Python, dataclass | **DB, HTTP, I/O, vaqt o'qish** |
| `algo/` | NumPy, sklearn | `app.*` ni import qilish |

> ⚠️ `domain/` da `datetime.now()` ham **taqiqlanadi** — vaqt argument
> sifatida uzatiladi. Aks holda funksiya testlanmaydigan bo'lib qoladi.

## Nega shunday

Bugungi kodda `D3` kabi qoidani **isbotlab bo'lmaydi**, chunki u
`patient_service`, `relatives`, `api/patients` va `notifier` orasiga
sochilgan. Testlarning yarmi mock bilan to'la — bu qoidalar DB bilan
chirmashib ketganining belgisi.

`backend/algo/` esa yaxshi ishlaydi: sof funksiyalar, 31 test, mocksiz.
`domain/` shu naqshni ideologiya qoidalariga qo'llaydi.

---

# 3. Katalog skeleti

```
backend/
├── algo/                      ✅ SAQLANADI — o'zgartirilmaydi
│   ├── baseline.py
│   ├── signal.py
│   ├── trend.py
│   ├── anomaly.py
│   └── tests/
│
├── alembic/                   ⚠️ ZANJIR NOLDAN
│   └── versions/
│
└── app/
    ├── core/                  ✅ ASOSAN SAQLANADI
    │   ├── config.py
    │   ├── db.py
    │   ├── security.py
    │   ├── metrics.py
    │   ├── rate_limit.py
    │   └── exceptions.py
    │
    ├── domain/                ⭐ YANGI — 4-bo'limga qarang
    │   ├── access.py
    │   ├── responsibility.py
    │   ├── entitlement.py
    │   ├── quality.py
    │   ├── attribution.py
    │   ├── billing_calc.py
    │   └── types.py
    │
    ├── models/                ⚠️ QAYTA YOZILADI — 5-bo'lim
    ├── repositories/          ⚠️ QAYTA YOZILADI — 6-bo'lim
    ├── services/              ⚠️ QAYTA YOZILADI
    ├── api/                   ⚠️ QAYTA YOZILADI
    └── auth/                  ⚠️ QAYTA YOZILADI

contracts/                     ✅ SAQLANADI
├── timewin.py
└── algo_interface.py

notifier/                      ⚠️ QAYTA ISHLANADI — I2 zaxira zanjiri
```

---

# 4. `domain/` — ideologiya qoidalari

Har bir modul — **bitta ideologiya bandini** bajaradi va **sof funksiyalardan**
iborat. Har biriga to'liq test yoziladi, mocksiz.

## 4.1 `responsibility.py` — `C1` `C2` `D3` `D5`

```python
@dataclass(frozen=True)
class CareOwner:
    tenant_id: UUID
    name: str
    licence_active: bool

@dataclass(frozen=True)
class PatientState:
    patient_id: UUID
    care_owner: CareOwner | None
    caregivers: tuple[CaregiverRef, ...]
    subscription_active: bool

def promise_level(state: PatientState) -> Literal["accountable", "awareness"]:
    """C2 — va'da parvarish egasiga qarab ko'tariladi yoki tushadi."""

def should_create_task(state: PatientState, level: AlertLevel) -> bool:
    """D5 — bajaruvchisi yo'q vazifa yaratilmaydi.

    Parvarish egasi bo'lmasa — HECH QACHON True qaytarmaydi.
    """

def notification_targets(
    state: PatientState,
    level: AlertLevel,
) -> tuple[Target, ...]:
    """D3 — kamida bitta javobgar doim xabardor.

    Egasi bor  → hamshiraga HAR DOIM · oilaga obunaga qarab
    Egasi yo'q → oilaga HAR DOIM, obunadan qat'i nazar (bepul)
    """
```

> **Majburiy test:** `notification_targets` hech qachon bo'sh natija
> qaytarmasligi kerak, `level` qizil bo'lganda. Buni property-based
> test bilan tekshiring.

## 4.2 `entitlement.py` — `D2` `D4` `E1`

```python
class Feature(StrEnum):
    # Hech qachon pullik bo'lmaydi — D4
    CRITICAL_ALERT = "critical_alert"
    SOS = "sos"
    # Oilaning ko'rinishi — obunaga bog'liq
    LIVE_STATUS = "live_status"
    ACTIVITY = "activity"
    TREND = "trend"
    HISTORY = "history"
    AI_SUMMARY = "ai_summary"
    PDF_REPORT = "pdf_report"

NEVER_PAYWALLED: frozenset[Feature] = frozenset({
    Feature.CRITICAL_ALERT,
    Feature.SOS,
})

def clinical_pipeline_enabled(state: PatientState) -> bool:
    """D2 — klinik oqim PARVARISH EGASINING huquqi bilan ishlaydi.

    Oilaning obunasiga QARAMAYDI. Litsenziya muddati tugagan bo'lsa ham
    mavjud bemor uchun True qaytaradi — C4.
    """

def family_features(state: PatientState) -> frozenset[Feature]:
    """Oila nimani ko'radi. NEVER_PAYWALLED har doim kiradi."""
```

> ⚠️ `NEVER_PAYWALLED` ga tegish — ideologiya buzilishi. Bu to'plamdan
> element olib tashlaydigan PR avtomatik rad etiladi.

## 4.3 `access.py` — `B3` `B6` `H1` `H2`

```python
def visible_patients(
    viewer: ViewerContext,
) -> AccessScope:
    """Kim qaysi bemorlarni ko'rishini aniqlaydi.

    Klinik xodim → o'z mahallalari (B6)
    Bosh shifokor → butun tenant
    Qarovchi → faqat patient_access bergan bemorlar
    Platforma tadqiqot → hammasi, SHAXSSIZLANTIRILGAN (H1)
    Platforma qo'llab-quvvatlash → to'liq, LEKIN sabab majburiy (H2)
    """

def requires_audit_log(viewer: ViewerContext, patient_id: UUID) -> bool:
    """H2 — tenantlararo o'qish jurnalga yoziladi."""
```

## 4.4 `quality.py` — `F2`

```python
@dataclass(frozen=True)
class DataQuality:
    score: float          # 0.0 – 1.0
    days_with_data: int
    days_total: int
    gaps: tuple[Gap, ...]
    anomalies: tuple[str, ...]

def task_kind(quality: DataQuality, level: AlertLevel) -> Literal["clinical", "technical"]:
    """F2 — sifat vazifa TURINI belgilaydi.

    Ishonchli   → clinical  (bemorga boring · 24s taymer · eskalatsiya)
    Ishonchsiz  → technical (soatni tekshiring · taymersiz)

    Bemor HECH QACHON yashirilmaydi — faqat so'ralgan harakat o'zgaradi.
    """
```

## 4.5 `attribution.py` — `F4`

```python
def attribute_reading(
    reading_ts: datetime,
    device_id: str,
    windows: tuple[AssignmentWindow, ...],
) -> UUID | None:
    """O'lchovni biriktirish OYNASI bo'yicha bemorga yozadi.

    "Hozir kim biriktirilgan" ga QARAMAYDI — oflayn bufer kech
    sinxronlanganda bir bemorning o'lchovi boshqasiga tushib ketadi.

    Hech qaysi oynaga tushmasa → None (orphan_readings ga boradi).
    """

def orphan_candidates(
    device_id: str,
    ts_range: tuple[datetime, datetime],
    windows: tuple[AssignmentWindow, ...],
) -> tuple[UUID, ...]:
    """Hamshiraga ko'rsatiladigan CHEKLANGAN nomzodlar ro'yxati.

    Faqat shu qurilma bilan shu vaqt atrofida bog'liq bemorlar.
    Istalgan bemorni tanlash mumkin emas.
    """
```

## 4.6 `billing_calc.py` — `E2` `E3` `E5`

```python
def patient_days(
    memberships: tuple[Membership, ...],
    assignments: tuple[AssignmentWindow, ...],
    period: DateRange,
) -> PatientDayReport:
    """E5 — a'zolik ochiq VA qurilma biriktirilgan kunlar.

    Kalendar kuni bo'yicha: shart kun davomida bir lahza bajarilsa — sanaladi.
    E3 — ma'lumotsiz kunlar SANALADI, lekin hisobotda alohida ko'rsatiladi.
    """

def invoice_total(report: PatientDayReport, licence: Licence) -> InvoiceLines:
    """E2 — minimal majburiyat qurilmalar soniga bog'langan."""
```

---

# 5. Ma'lumot modeli

> **Nomlash:** jadval nomlari ko'plikda, ustunlar `snake_case`.
> Barcha vaqt ustunlari `TIMESTAMPTZ`, UTC da saqlanadi.
> Barcha ID — `UUID`, `gen_random_uuid()` bilan.

## 5.1 Identifikatsiya

```sql
-- Telefon + SMS bilan tasdiqlangan hisob. ROL YO'Q — rol munosabatdan.
CREATE TABLE accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           TEXT NOT NULL UNIQUE,        -- +998XXXXXXXXX
    phone_verified_at TIMESTAMPTZ,
    full_name       TEXT NOT NULL,
    preferred_lang  TEXT NOT NULL DEFAULT 'uz' CHECK (preferred_lang IN ('uz','ru','en')),
    timezone        TEXT NOT NULL DEFAULT 'Asia/Tashkent',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Keyin qo'shiladi: Google, Telegram (B2 — hisob qatlamiga, bemor modeliga emas)
CREATE TABLE account_identities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    provider    TEXT NOT NULL CHECK (provider IN ('phone','google','telegram')),
    external_id TEXT NOT NULL,
    verified_at TIMESTAMPTZ,
    CONSTRAINT uq_identity UNIQUE (provider, external_id)
);
```

## 5.2 Bemor

```sql
CREATE TABLE patients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- TENANT_ID YO'Q — 1.1 bandiga qarang
    full_name       TEXT NOT NULL,
    birth_date      DATE,                     -- yosh HISOBLANADI, saqlanmaydi
    sex             CHAR(1) CHECK (sex IN ('m','f')),
    phone           TEXT,                     -- bemorning o'zi, bo'lmasligi mumkin
    jshshir         TEXT,                     -- B2 — hozir BO'SH, keyin kuchli kalit
    preferred_lang  TEXT NOT NULL DEFAULT 'uz',
    -- Hayot sikli — J1, J2
    deceased_at     TIMESTAMPTZ,
    deceased_marked_by UUID REFERENCES accounts(id),
    deceased_confirmed_by UUID REFERENCES accounts(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_patients_phone ON patients(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_patients_alive ON patients(id) WHERE deceased_at IS NULL;
```

> **`birth_date`, `age` emas.** Yosh saqlansa eskiradi — 2 yildan keyin
> hamma bemor 2 yoshga yosh bo'ladi. Yosh `@computed_field` bilan hisoblanadi.

## 5.3 Ulanish — ikki mexanizm

```sql
-- B2B — institutsional, vaqtli
CREATE TYPE membership_kind AS ENUM ('care');

CREATE TABLE patient_memberships (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    kind        membership_kind NOT NULL DEFAULT 'care',
    granted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    granted_by  UUID REFERENCES accounts(id),
    revoked_at  TIMESTAMPTZ,
    revoked_reason TEXT,
    -- C3 — klinika baseline bo'yicha qarori
    baseline_decision TEXT CHECK (baseline_decision IN ('accepted','relearn','rejected')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 1.4 — bir vaqtda BITTA parvarish egasi, DB darajasida
CREATE UNIQUE INDEX idx_one_care_owner
    ON patient_memberships (patient_id)
    WHERE kind = 'care' AND revoked_at IS NULL;

-- B2C — shaxsiy, taklif orqali, muddatsiz
CREATE TYPE access_role AS ENUM ('payer', 'caregiver');

CREATE TABLE patient_access (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    account_id  UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    role        access_role NOT NULL DEFAULT 'caregiver',
    relation    TEXT,                     -- "qizi", "o'g'li"
    invited_by  UUID REFERENCES accounts(id),
    granted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at  TIMESTAMPTZ,
    CONSTRAINT uq_access UNIQUE (patient_id, account_id)
);
CREATE INDEX idx_access_active ON patient_access(account_id) WHERE revoked_at IS NULL;
```

## 5.4 Rozilik — `B4` `B5`

```sql
CREATE TYPE consent_scope  AS ENUM ('family_access', 'clinical_monitoring');
CREATE TYPE consent_method AS ENUM ('sms', 'in_app', 'verbal_by_clinician');

CREATE TABLE patient_consents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    scope       consent_scope NOT NULL,
    granted     BOOLEAN NOT NULL,
    method      consent_method NOT NULL,
    -- Og'zaki rozilikda: kim tasdiqladi (B4)
    witnessed_by UUID REFERENCES accounts(id),
    -- Nimaga nisbatan: oila ruxsati bo'lsa qaysi hisobga
    target_account_id UUID REFERENCES accounts(id),
    target_tenant_id  UUID REFERENCES tenants(id),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at  TIMESTAMPTZ,
    revoke_reason TEXT
);
CREATE INDEX idx_consents_patient ON patient_consents(patient_id, scope);
```

## 5.5 Klinika va hudud — `B6`

```sql
CREATE TYPE tenant_kind AS ENUM ('ovabmu','polyclinic','hospital','network');

CREATE TABLE tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind        tenant_kind NOT NULL,
    name        TEXT NOT NULL,
    legal_name  TEXT,
    tax_id      TEXT,
    region      TEXT NOT NULL,
    district    TEXT NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE tenant_role AS ENUM ('nurse','doctor','head_doctor','admin','dispatcher');

CREATE TABLE tenant_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    account_id  UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    role        tenant_role NOT NULL,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    left_at     TIMESTAMPTZ,
    CONSTRAINT uq_member UNIQUE (tenant_id, account_id)
);

-- B6 — mahalla biriktiruvi. Bitta mexanizm ikki ish qiladi:
-- M11 yo'naltirish + kirish huquqi.
CREATE TABLE member_territories (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_member_id  UUID NOT NULL REFERENCES tenant_members(id) ON DELETE CASCADE,
    mahalla           TEXT NOT NULL,
    CONSTRAINT uq_member_mahalla UNIQUE (tenant_member_id, mahalla)
);

CREATE TABLE patient_addresses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    region      TEXT NOT NULL,
    district    TEXT NOT NULL,
    mahalla     TEXT,                    -- B6 yo'naltirish kaliti
    street      TEXT,
    house       TEXT,
    flat        TEXT,
    landmark    TEXT,                    -- qishloqda ko'cha nomi ishonchsiz
    entrance_note TEXT,
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    is_primary  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX idx_one_primary_address
    ON patient_addresses(patient_id) WHERE is_primary;
```

## 5.6 Qurilma — `F1` `F4`

```sql
CREATE TYPE device_status     AS ENUM ('in_stock','assigned','maintenance','lost','retired');
CREATE TYPE device_provenance AS ENUM ('clinic_issued','self_purchased','unknown');

CREATE TABLE devices (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    serial      TEXT NOT NULL UNIQUE,
    model       TEXT NOT NULL,
    status      device_status NOT NULL DEFAULT 'in_stock',
    -- Egasi: klinika yoki bemor. Ikkalasi ham NULL — bizning ombor.
    owner_tenant_id  UUID REFERENCES tenants(id) ON DELETE SET NULL,
    owner_patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    battery_health_pct SMALLINT CHECK (battery_health_pct BETWEEN 0 AND 100),
    last_seen_at TIMESTAMPTZ,
    -- 11.3 — TRANSPORT bog'lanishi. Attributsiyaga TA'SIR QILMAYDI.
    bound_phone_node_id TEXT,
    bound_phone_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_single_owner CHECK (
        num_nonnulls(owner_tenant_id, owner_patient_id) <= 1
    )
);

CREATE TABLE device_assignments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    -- F1 — kelib chiqish
    provenance  device_provenance NOT NULL DEFAULT 'unknown',
    supervised  BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by UUID REFERENCES accounts(id),
    -- F4 — attributsiya oynasi
    assigned_at TIMESTAMPTZ NOT NULL,
    released_at TIMESTAMPTZ,
    assigned_by UUID REFERENCES accounts(id),
    -- Arenda (E2)
    deposit_uzs BIGINT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_assignment_window
    ON device_assignments(device_id, assigned_at, released_at);

-- F4 — oynaga tushmagan o'lchovlar
CREATE TABLE orphan_readings (
    id          BIGSERIAL PRIMARY KEY,
    device_id   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    window_start TIMESTAMPTZ NOT NULL,
    payload     JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Hamshira biriktirishni orqaga surganda to'ldiriladi
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES accounts(id),
    resolved_to_patient_id UUID REFERENCES patients(id)
);
CREATE INDEX idx_orphan_unresolved
    ON orphan_readings(device_id, window_start) WHERE resolved_at IS NULL;
ALTER TABLE orphan_readings
    ADD CONSTRAINT uq_orphan_key UNIQUE (device_id, window_start);
```

> **14 kunlik muddat:** `resolved_at IS NULL AND received_at < now() - interval '14 days'`
> bo'lgan qatorlar fon ishi bilan tashlanadi. Eslash emas, taxmin.

## 5.7 Klinik ma'lumot

```sql
-- K3 — oyma-oy bo'linish HOZIR qo'yiladi, keyin qo'shish qimmat
-- Maydonlar 11.7 kontrakti bo'yicha. Olib tashlanganlari uchun 11.7 ga qarang.
CREATE TABLE readings (
    id          BIGSERIAL,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    device_id   UUID NOT NULL REFERENCES devices(id),
    device_assignment_id UUID REFERENCES device_assignments(id),
    -- 11.4 — 5 daqiqalik chegaraga TEKISLANGAN, yuborish vaqti EMAS
    window_start TIMESTAMPTZ NOT NULL,
    window_end   TIMESTAMPTZ NOT NULL,
    hr_mean     REAL, hr_min REAL, hr_max REAL,
    -- 11.8 sinovi ijobiy bo'lsagina to'ldiriladi
    rmssd       REAL,
    worn        BOOLEAN NOT NULL DEFAULT TRUE,
    worn_pct    SMALLINT CHECK (worn_pct BETWEEN 0 AND 100),
    samples_n   SMALLINT NOT NULL DEFAULT 0,
    battery     SMALLINT,
    -- 11.5 — soat soati
    device_clock_utc TIMESTAMPTZ,
    clock_offset_ms  INTEGER,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- F1 — o'lchov o'z ishonch darajasini olib yuradi
    provenance  device_provenance NOT NULL DEFAULT 'unknown',
    attributed_by TEXT CHECK (attributed_by IN ('window','nurse')),
    PRIMARY KEY (id, window_start),
    -- 11.4 — dublikatni matematik jihatdan imkonsiz qiladi
    CONSTRAINT uq_reading_key UNIQUE (device_id, window_start)
) PARTITION BY RANGE (window_start);

CREATE TABLE baselines (
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    param       TEXT NOT NULL,
    time_window SMALLINT NOT NULL CHECK (time_window BETWEEN 0 AND 3),
    median      REAL NOT NULL,
    mad         REAL NOT NULL,
    n_samples   INTEGER NOT NULL,
    -- Muzlatilganmi (shifokor tasdiqlagan)
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES accounts(id),
    includes_attributed BOOLEAN NOT NULL DEFAULT FALSE,  -- nurse_attributed kirganmi
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (patient_id, param, time_window)
);

CREATE TYPE alert_level AS ENUM ('green','amber','red','no_data');

CREATE TABLE alerts (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    ts          TIMESTAMPTZ NOT NULL,
    level       alert_level NOT NULL,
    composite_score REAL NOT NULL DEFAULT 0,
    triggered_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    anomaly_score REAL,
    reason      TEXT,
    -- F2 — sifat ballи signal bilan birga yoziladi
    data_quality REAL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_alert UNIQUE (patient_id, ts)
);

-- F2 — vazifa TURI sifatdan kelib chiqadi
CREATE TYPE task_kind   AS ENUM ('clinical','technical');
CREATE TYPE task_status AS ENUM ('open','acknowledged','done','overdue','cancelled');

CREATE TABLE tasks (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    assignee_account_id UUID REFERENCES accounts(id),   -- D5: NULL bo'lsa yaratilmaydi
    kind        task_kind NOT NULL,
    status      task_status NOT NULL DEFAULT 'open',
    alert_id    BIGINT REFERENCES alerts(id) ON DELETE SET NULL,
    due_at      TIMESTAMPTZ,                -- technical da NULL — taymer yo'q
    reminded_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    escalated_at TIMESTAMPTZ,
    done_at     TIMESTAMPTZ,
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- D5 — bajaruvchisiz vazifa bo'lmaydi
    CONSTRAINT chk_assignee CHECK (assignee_account_id IS NOT NULL)
);
```

## 5.8 Pul

```sql
-- E1 — obuna BEMORDA
CREATE TYPE sub_plan   AS ENUM ('free','premium','premium_doc');
CREATE TYPE sub_status AS ENUM ('trialing','active','past_due','lapsed');

CREATE TABLE patient_subscriptions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL UNIQUE REFERENCES patients(id) ON DELETE CASCADE,
    plan        sub_plan NOT NULL DEFAULT 'free',
    status      sub_status NOT NULL DEFAULT 'trialing',
    trial_ends_at TIMESTAMPTZ,
    period_end  TIMESTAMPTZ,
    -- Istalgan ulangan hisob to'lay oladi
    last_paid_by UUID REFERENCES accounts(id),
    provider    TEXT CHECK (provider IN ('payme','click','uzum','manual')),
    provider_ref TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- E2 — klinika litsenziyasi
CREATE TABLE tenant_licences (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
    device_count INTEGER NOT NULL DEFAULT 0,
    min_days_per_device INTEGER NOT NULL DEFAULT 10,
    price_per_patient_day_uzs BIGINT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active','past_due','suspended')),
    -- C4 — to'lanmasa: kuzatuv davom etadi, QABUL to'xtaydi
    intake_blocked_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- E5 — materiallashtirilgan bemor-kun
CREATE TABLE billing_days (
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    day         DATE NOT NULL,
    had_data    BOOLEAN NOT NULL,       -- E3 — hisobotda alohida ko'rsatiladi
    PRIMARY KEY (tenant_id, patient_id, day)
);

CREATE TABLE invoices (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end  DATE NOT NULL,
    patient_days_total INTEGER NOT NULL,
    patient_days_with_data INTEGER NOT NULL,
    min_commitment INTEGER NOT NULL,
    billed_days INTEGER NOT NULL,       -- max(total, min_commitment)
    amount_uzs  BIGINT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open','paid','overdue','void')),
    issued_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at     TIMESTAMPTZ
);
```

## 5.9 Bildirishnoma — `I2`

```sql
CREATE TYPE notify_channel AS ENUM ('push','telegram','sms','voice');

CREATE TABLE notifications (
    id          BIGSERIAL PRIMARY KEY,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    recipient_account_id UUID REFERENCES accounts(id),
    alert_id    BIGINT REFERENCES alerts(id) ON DELETE SET NULL,
    level       alert_level,
    urgent      BOOLEAN NOT NULL DEFAULT FALSE,   -- I1 — jiringlaydimi
    acknowledged_at TIMESTAMPTZ,                  -- I2 — zanjir shu yerda to'xtaydi
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Har bir urinish alohida yoziladi
CREATE TABLE notification_attempts (
    id          BIGSERIAL PRIMARY KEY,
    notification_id BIGINT NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel     notify_channel NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered   BOOLEAN NOT NULL DEFAULT FALSE,
    error       TEXT
);
```

## 5.10 Twin va haqiqat halqasi — `G1`–`G5`

```sql
CREATE TABLE patient_conditions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    icd10       TEXT,                    -- G2 — klinika ulanganda to'ladi
    name_uz     TEXT NOT NULL,
    kind        TEXT CHECK (kind IN ('primary','comorbidity','past')),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    recorded_by UUID REFERENCES accounts(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE patient_medications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    dose        TEXT,
    frequency   TEXT,
    started_at  DATE,
    stopped_at  DATE,
    -- L2/L3 uchun MIQDORIY bo'lishi shart, sifatli emas
    -- {"hr_mean": {"direction":"lowers","expected_pct":15.0,
    --              "onset_days":3,"steady_state_days":7,"source":"literature"}}
    affects_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    prescribed_by UUID REFERENCES accounts(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- L2 — aralashuvga HAQIQIY javob
CREATE TABLE medication_responses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    medication_id UUID NOT NULL REFERENCES patient_medications(id) ON DELETE CASCADE,
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    baseline_from TIMESTAMPTZ NOT NULL,
    baseline_to   TIMESTAMPTZ NOT NULL,
    response_from TIMESTAMPTZ NOT NULL,
    response_to   TIMESTAMPTZ NOT NULL,
    observed_effects JSONB NOT NULL DEFAULT '{}'::jsonb,
    verdict     TEXT CHECK (verdict IN ('as_expected','no_response','unexpected','insufficient_data')),
    confidence  REAL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Natija ko'rsatkichlari — model o'rganadigan yagona haqiqat
CREATE TABLE patient_outcomes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL CHECK (kind IN ('admission','er_visit','death','recovered')),
    occurred_at TIMESTAMPTZ NOT NULL,
    icd10       TEXT,
    -- Signal oldindan ogohlantirganmi — model sifatini o'lchash
    predicted_by_alert_id BIGINT REFERENCES alerts(id) ON DELETE SET NULL,
    source      TEXT CHECK (source IN ('clinic','survey','family')),
    recorded_by UUID REFERENCES accounts(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- G3, G4, G5 — so'rovnoma
CREATE TABLE surveys (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        TEXT NOT NULL UNIQUE,
    audience    TEXT NOT NULL CHECK (audience IN ('caregiver','nurse','patient')),
    questions   JSONB NOT NULL,     -- biri TESKARI yozilgan bo'lishi SHART
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE survey_responses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id   UUID NOT NULL REFERENCES surveys(id),
    patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    account_id  UUID NOT NULL REFERENCES accounts(id),
    answers     JSONB NOT NULL,
    -- G4 — sifat signallari
    per_question_ms JSONB NOT NULL,    -- {"q1": 8200, "q2": 3100, "q3": 14700}
    straightline BOOLEAN NOT NULL DEFAULT FALSE,
    reverse_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    fact_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    quality     TEXT NOT NULL CHECK (quality IN ('trusted','weak','rejected')),
    -- Chegirma HAR DOIM beriladi, sifatdan qat'i nazar
    discount_granted BOOLEAN NOT NULL DEFAULT TRUE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 5.11 Audit — `H2`

```sql
CREATE TABLE access_log (
    id          BIGSERIAL PRIMARY KEY,
    account_id  UUID NOT NULL REFERENCES accounts(id),
    patient_id  UUID NOT NULL REFERENCES patients(id),
    viewer_kind TEXT NOT NULL CHECK (viewer_kind IN ('clinician','caregiver','platform_support','platform_research')),
    reason      TEXT,                -- platform_support uchun MAJBURIY
    at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    request_id  TEXT
);
CREATE INDEX idx_access_log_patient ON access_log(patient_id, at DESC);
```

---

# 6. Kirish nazorati

Uch qatlam, har biri mustaqil. Biri buzilsa — qolganlari ushlab qoladi.

```
1. JWT da nima bor        → tenant a'zoliklari, patient_access ro'yxati
2. Repozitoriy filtri     → har so'rov MAJBURAN toraytiriladi
3. Postgres RLS           → oxirgi himoya, DB darajasida
```

## 6.1 Repozitoriy darajasi — majburiy

```python
class ScopedRepository:
    """Har bir so'rov ko'ruvchining doirasiga toraytiriladi.

    Filtrni servis qatlamida yozish — unutiladigan qadam. Unutilganda
    bu test tushishi emas, bir klinikaning boshqasining bemorini o'qishi
    bo'lib chiqadi. Shuning uchun u BITTA joyda majburlanadi.
    """

    def _scope(self, stmt: Select) -> Select:
        scope = visible_patients(self.viewer)     # domain/access.py
        return stmt.where(Patient.id.in_(scope.patient_ids))
```

> **Review qoidasi:** `select(Patient)` ni `_scope()` dan o'tkazmasdan
> ishlatadigan har qanday kod rad etiladi.

## 6.2 JWT tarkibi

```json
{
  "sub": "<account_id>",
  "phone": "+998901234567",
  "memberships": [
    {"tenant_id": "...", "role": "nurse", "mahallas": ["Gulobod", "Qoraqir"]}
  ],
  "exp": 1234567890,
  "type": "access"
}
```

> `patient_access` JWT ga **kiritilmaydi** — u o'zgaruvchan va uzun
> bo'lishi mumkin. Har so'rovda DB dan o'qiladi.

---

# 7. Nima saqlanadi, nima qayta yoziladi

| Yo'l | Holat | Izoh |
|---|---|---|
| `backend/algo/` | ✅ **Tegilmaydi** | 445 qator, 31 test, ideologiyadan mustaqil |
| `contracts/timewin.py` | ✅ Tegilmaydi | Circadian oyna mantiqi |
| `contracts/algo_interface.py` | ✅ Tegilmaydi | Sof tiplar |
| `app/core/config.py` | ✅ Saqlanadi | Yangi sozlamalar qo'shiladi |
| `app/core/db.py` | ✅ Saqlanadi | |
| `app/core/security.py` | ✅ Saqlanadi | bcrypt, JWT |
| `app/core/metrics.py` | ✅ Saqlanadi | |
| `app/core/rate_limit.py` | ⚠️ Tuzatiladi | Sinxron redis → `redis.asyncio` |
| `app/models/` | ❌ **Qayta yoziladi** | 5-bo'lim bo'yicha |
| `app/repositories/` | ❌ Qayta yoziladi | `ScopedRepository` asosida |
| `app/services/` | ❌ Qayta yoziladi | |
| `app/api/` | ❌ Qayta yoziladi | |
| `app/auth/` | ❌ Qayta yoziladi | `accounts` modeli |
| `alembic/versions/` | ❌ **Noldan** | Eski zanjir o'chiriladi |
| `app/tests/` | ❌ Qayta yoziladi | Infratuzilma saqlanadi |
| CI / Docker / deploy | ✅ Saqlanadi | |

---

# 8. Qurish tartibi

Har bosqich **tugallangan va testlangan** bo'lgandan keyin keyingisiga o'tiladi.
Yonida — qaysi bo'lim bo'yicha quriladi.

### Bosqich −1 · Ma'lumot auditi ⚠️ hammasidan oldin
**16.2** · Bazada nima borligi sanaladi, `docs/DATA_AUDIT.md` yoziladi,
`pg_dump` arxivga olinadi. **A yoki B yo'li shu yerda tanlanadi** (16.3).

### Bosqich 0 · Tozalash
Faqat auditda legacy deb tasdiqlangan, ishlatilmaydigan kod olib tashlanadi.
`models/`, `services/`, `api/`, `auth/`, `alembic/versions/`, production
ma'lumotlar yoki backup'lar ko'r-ko'rona o'chirilmaydi. Migratsiya tarixi
saqlanadi; o'chirish alohida review va tiklash rejasi talab qiladi.

### Bosqich 1 · `domain/`
**4-bo'lim** · Olti modul, sof funksiyalar. Har biriga to'liq test,
**mock yo'q, DB yo'q**. Bu bosqich DB'siz tugallanadi — eng erta
boshlanishi mumkin bo'lgan ish.

### Bosqich 2 · `models/` + migratsiya
**5 · 12.3 · 17** · SQLAlchemy modellari, `alembic revision --autogenerate`.
Partitsiyalar joriy oy + 3 oy oldinga yaratiladi.
`alembic check` toza, `upgrade → downgrade → upgrade` ishlaydi.

### Bosqich 2b · Ma'lumot ko'chirish — faqat B yo'lida
**16.4 · 16.5** · Ko'chirish skripti va solishtirish tekshiruvi.

### Bosqich 3 · `repositories/` + RLS
**6.1 · 14** · `ScopedRepository`, RLS siyosatlari, 14.5 testlari.

### Bosqich 4 · `auth/`
**6.2 · 12 · 13.1** · `accounts`, telefon + SMS, JWT a'zolik claim'i,
qurilma ro'yxatga olish va tokeni, rozilik oqimi.

### Bosqich 5 · `services/` + `api/`
**13 · 15 · 18** · Endpointlar faqat 13-bo'lim ro'yxatidan.
Har endpoint `domain/` qoidalarini chaqiradi, o'zi qoida yozmaydi.
`contracts/openapi.yaml` shu bosqichda qayta yoziladi.

### Bosqich 6 · `notifier/` + qurilma yo'li
**11 · 15.6 · 21** · `I2` zaxira zanjiri; soat rejimi va telefon oqimi
`mobile_flutter` ichida quriladi (19.1 · 19.5).

### Bosqich 7 · Frontend
**19** · `mobile_flutter`, `web-doctor`, platforma konsoli.
`web-relative` birlashtiriladi.

---

# 9. Review mezonlari

Har bir PR shu ro'yxat bo'yicha tekshiriladi.

## Avtomatik rad etiladi

- [ ] `NEVER_PAYWALLED` to'plamidan element olib tashlangan (`D4`)
- [ ] `assignee_account_id` NULL bo'lishi mumkin bo'lgan vazifa (`D5`)
- [ ] `patients` ga `tenant_id` qo'shilgan (`1.1`)
- [ ] `domain/` da DB, HTTP yoki `datetime.now()` ishlatilgan
- [ ] `select(Patient)` `_scope()` siz ishlatilgan (`6.1`)
- [ ] Migratsiya qo'lda yozilgan (`autogenerate` emas)
- [ ] `alembic check` toza emas
- [ ] Qurilma tokeni `patient_id` olib yuradi (12.1)
- [ ] 13-bo'limda yo'q endpoint qo'shilgan
- [ ] `SET` ishlatilgan (`SET LOCAL` o'rniga) — hovuz sizishi (14.1)
- [ ] HTTP so'rov ishlov beruvchisida `wmax.bypass = 'on'` (14.4)
- [ ] `patient_memberships` yoki `patient_access` ga RLS qo'shilgan (14.2)
- [ ] `domain/` testida mock ishlatilgan (20.1)
- [ ] 20.2 xavfsizlik testlaridan biri o'tmaydi

## Har PR da tekshiriladi

- [ ] Qaysi ideologiya bandini bajaradi — PR tavsifida yozilganmi
- [ ] `domain/` funksiyasi qo'shilgan bo'lsa — mocksiz testi bormi
- [ ] Yangi jadval — `alembic check` toza, `downgrade` ishlaydimi
- [ ] Bemor ko'rinadigan matn `D1` ni buzmaydimi (tashxis aytilmaydi)
- [ ] Yangi endpoint `ScopedRepository` orqali o'qiydimi

## Shubha bo'lganda

Ideologiya bandiga zid ko'rinsa — **kod emas, savol yuboriladi**.
Band noto'g'ri bo'lsa — `IDEOLOGY.md` o'zgartiriladi, keyin kod.
Teskarisi emas.

---

# 10. Hali kelishilmagan

Spetsifikatsiyaning qolgan qismi yopiq. Quyidagi uchtasi **qurishni
bloklamaydi**, lekin tegishli bosqichga kelguncha hal qilinishi kerak.

| # | Nima | Qachon kerak | Kim hal qiladi |
|---|---|---|---|
| 10.1 | **HRV sinovi natijasi** (11.8) | 2-bosqichgacha | ishchi agent · sinov |
| 10.2 | **SMS / ovoz provayderi** (21.2 · 21.4) | 6-bosqich | tadqiqot + narx |
| 10.3 | **L3/L4 twin modeli** (`G1`) | ~1 yil — ma'lumot to'plangach | keyin |

> 10.1 eng muhimi: natija salbiy bo'lsa `algo/` dagi HRV parametrlari
> o'chiriladi va kontrakt qisqaradi. Buni bilmasdan 2-bosqichni tugatish —
> keyin qayta yozish demak.

---

# 11. Qurilma ma'lumot yo'li

> **Holat:** kelishildi · 2026-09-22
> Bu bo'lim o'chirilgan eski `wear/` kodidagi aniqlangan nosozliklar asosida yozilgan.
> Har bir qoida yonida **qaysi muammoni yopishi** ko'rsatilgan.

## 11.1 Hozirgi holatda topilgan nosozliklar

Qayta qurishdan oldin nimani tuzatayotganimizni aniq bilish kerak.

### Noto'g'ri odamga yozilish

| # | Joy | Muammo |
|---|---|---|
| A1 | `wear/watch/build.gradle.kts:18` | `WMAX_PATIENT_ID` — **APK ichiga kompilyatsiya vaqtida quyilgan**. Soatni boshqa bemorga berish uchun APK qayta yig'iladi. Amalda qilinmaydi → eski bemorga yozishda davom etadi |
| A2 | `data/ReadingDto.kt` | Paketda **`device_id` umuman yo'q**. Server o'lchov qaysi soatdan kelganini bilmaydi → `F4` attributsiyasi texnik jihatdan bajarib bo'lmaydi |
| A3 | `data/ReadingDto.kt` — `SosDto` | `patientId` default qiymati `""` → bo'sh SOS yuborilishi mumkin |

### Ma'lumot yo'qolishi

| # | Joy | Muammo |
|---|---|---|
| B1 | `SensorAggregator.samples` | Oddiy `MutableList` — xotirada. App o'ldi → oyna yo'q |
| B2 | `computeAndDrainWindow()` | Yuborishdan **oldin** tozalaydi. Yuborish muvaffaqiyatsiz → ma'lumot butunlay yo'q |
| B3 | `MainActivity.kt:247` | `catch (_: Exception) {}` — xato jim yutiladi, qayta urinish yo'q |
| B4 | `MainActivity.kt:233` | `sendReading()` natijasi e'tiborsiz qoldiriladi |
| B5 | `MainActivity.kt:221` | `lifecycleScope.launch { while(true) delay(5min) }` — Activity o'lsa sikl o'ladi. Foreground service yo'q |
| B6 | umumiy | **Bufer yo'q.** Internetsiz kun butunlay yo'qoladi |

### Dublikat

| # | Joy | Muammo |
|---|---|---|
| C1 | `SensorAggregator.kt` | `ts = formatIsoUtc(Date())` — **flush vaqti**, oyna boshi emas. Har qayta urinish yangi `ts` → dublikat muqarrar |
| C2 | `MainActivity.kt:231-248` | Ikki kanal parallel yuboriladi, idempotentlik kaliti yo'q |

### O'lchov ishonchliligi

`ReadingDto` da 11 maydon bor. Haqiqatda nechtasi ishlaydi:

| Maydon | Holat | Sabab |
|---|---|---|
| `hr_mean` `hr_min` `hr_max` | ✅ Haqiqiy | PPG dan keladi |
| `worn` | ✅ Haqiqiy | Off-body sensori ishonchli |
| `battery` | ✅ Haqiqiy | |
| `spo2` | ❌ Har doim `null` | `MeasureEvent.SpO2` hech qayerda `trySend` qilinmaydi |
| `skin_temp` | ❌ Har doim `null` | Hech narsa to'ldirmaydi |
| `steps` | ❌ Har doim `0` | `steps = 0` qattiq yozilgan |
| `sleep_frag` | ❌ Har doim `null` | |
| `rmssd` | ⚠️ Matematik noto'g'ri | D1 ga qarang |
| `sdnn` | ⚠️ Noto'g'ri | 5 ta o'rtacha qiymatdan SDNN chiqmaydi |
| `rr_est` | ⚠️ To'qilgan | D2 ga qarang |

**D1 · RMSSD nega noto'g'ri** (`SensorAggregator.kt:73-82`):
kod 1 daqiqalik **o'rtacha HR** dan RR intervalini chiqaradi (`rr = 60000/hr`).
RMSSD esa yurakning **ketma-ket ikki urishi** orasidagi farqni talab qiladi —
daqiqada ~70 ta juftlik. Bu yerda 5 ta o'rtacha bor.
`RawSensorSample.rrIntervalMs` maydoni **mavjud**, lekin hech qachon
to'ldirilmaydi va agregator uni o'qimaydi.

**D2 · `rr_est` nega xavfli**: `rr_est = hr_mean / 4.5`.
Bu nafas tezligi emas, HR ning konstantaga bo'lingani. Mustaqil ma'lumot **nol**.
Lekin baseline va anomaliya algoritmiga **alohida parametr** sifatida kiradi →
HR o'zgarganda ikki marta signal beradi, signal kuchini sun'iy ikkilantiradi.

**D3 · Ekrandagi soxta raqamlar** (`MainActivity.kt:269-270`):
```kotlin
var spo2 by remember { mutableDoubleStateOf(98.0) }
var skinTemp by remember { mutableDoubleStateOf(36.6) }
```
Ekranda `SpO2 98%` va `36.6°C` ko'rinadi. Hech qanday sensordan kelmaydi.
Hamshira buni haqiqiy o'lchov deb o'qiydi. **Darhol olib tashlanadi.**

---

## 11.2 Uch bog'lanishni ajratish — asosiy qoida

Hozirgi kodda uch xil narsa bitta tushunchaga chalkashgan. Ajratish —
noto'g'ri odamga yozilishning oldini oladigan asosiy nazorat.

| Bog'lanish | Nima hal qiladi | Qayerda saqlanadi |
|---|---|---|
| **Transport** | Soat ma'lumotni qaysi telefon orqali yuboradi | Soatda |
| **Vakolat** | Kim bu soatni biriktirishga haqli | Mobil ilova sessiyasi |
| **Attributsiya** | O'lchov qaysi **bemorga** yoziladi | **FAQAT serverda** — `device_assignments` |

> ⚠️ **Telefon hech qachon bemorni belgilamaydi.** Klinikada hamshirada
> bitta telefon, palatada 20 ta soat bo'ladi. "Telefon → bemor" qoidasi
> 20 ta soatning hammasini hamshiraga yozadi.

## 11.3 Biriktirish oqimi

```
1. Mobil ilovada login            → vakolat aniqlanadi
2. Soat QR / BLE orqali ulanadi   → soat telefon tugunini eslab qoladi (transport)
3. Ilova so'raydi: "Kimga?"       → bemor tanlanadi
4. Serverda device_assignment     → attributsiya SHU YERDAN
```

- **B2C:** 3-qadam bir marta bo'ladi va unutiladi
- **B2B:** hamshira har yangi bemorga qayta tanlaydi

### Telefon almashganda

Soat **"bog'lanmagan"** holatga o'tadi:

- O'lchash va buferlash **davom etadi**
- Yuborilgan ma'lumot `orphan_readings` ga tushadi
- Yangi telefon ulanib bemor tasdiqlanganidan keyin `F4` oynasi bo'yicha
  orqaga biriktiriladi, `attributed_by = 'nurse'` bilan

> **Jimgina qayta biriktirish hech qachon bo'lmaydi.** Oila a'zosi soatni
> olib o'z telefonini ulasa, bemor o'z-o'zidan almashmaydi.

## 11.4 Idempotentlik — dublikat imkonsizligi

Soatda ham, telefonda ham bufer bo'ladi. Dublikat bo'lmasligi **holat
boshqaruvi bilan emas, kalit bilan** ta'minlanadi.

```
Kalit = (device_id, window_start)
```

`window_start` — **5 daqiqalik UTC chegarasiga tekislangan** vaqt:
`10:00:00`, `10:05:00`, `10:10:00` …

```sql
INSERT INTO readings (...) VALUES (...)
ON CONFLICT (device_id, window_start) DO NOTHING;
```

Bu nimani kafolatlaydi:

| Holat | Natija |
|---|---|
| Soat 5 marta qayta yuboradi | Bitta qator |
| Soat kanali va telefon kanali bir vaqtda yetadi | Bitta qator |
| Telefon buferi eski paketni qayta yuboradi | Bitta qator |

> **O'chirish qoidasi:** soat va telefon o'z buferidan faqat **server ACK
> bergandan keyin** o'chiradi. Ikkalasi mustaqil ishlaydi, bir-biriga qaramaydi.

### Oyna tekislash

Agregator **vaqt bo'yicha** yopiladi, **nusxa soni bo'yicha emas**.
Hozirgi `samples.size >= 5` shart sampling to'xtab qolsa "5 daqiqalik oyna"
bir soatga cho'zilishiga olib keladi.

## 11.5 Soat soati (clock skew)

`window_start` soatning soatidan hisoblanadi. Soat bir hafta oflayn tursa
vaqti surilishi mumkin → kalit noto'g'ri, ma'lumot noto'g'ri vaqtga tushadi.

Mexanizm:

1. Har paketda soatning xom vaqti (`device_clock_utc`) yuboriladi
2. Server `received_at` bilan solishtiradi
3. Har ACK javobida server o'z vaqtini qaytaradi
4. Soat farqni (`clock_offset_ms`) saqlaydi va `window_start` ni shu bilan tuzatadi
5. Farq chegaradan katta bo'lsa — paket belgilanadi, `F2` bo'yicha
   **texnik vazifa** ochiladi

## 11.6 Kanallar

| Kanal | Rol |
|---|---|
| Soat → telefon → server | **Asosiy** |
| Soat → server (Wi-Fi/LTE) | **Zaxira** — telefon uzoq vaqt yo'q bo'lganda |

Zaxira kanal faqat quyidagi shartlarda yoqiladi:
- Telefon tuguni belgilangan muddatdan uzoq ulanmagan
- Soatda Wi-Fi mavjud
- Bufer to'lish chegarasiga yaqinlashgan

Kalit bir xil bo'lgani uchun ikkala kanal bir vaqtda ishlasa ham dublikat
bo'lmaydi. Zaxira kanal batareyani ko'proq sarflaydi — shuning uchun
doimiy emas.

## 11.7 Yangi o'lchov kontrakti

Ishlamayotgan va to'qilgan maydonlar olib tashlanadi.

```
device_id          ← YANGI, majburiy
window_start       ← tekislangan, idempotentlik kaliti
window_end
hr_mean · hr_min · hr_max
rmssd              ← FAQAT haqiqiy RR intervallaridan (11.8), aks holda yuborilmaydi
worn               ← bool
worn_pct           ← YANGI: oynaning necha foizi taqilgan (F1 ishonch)
samples_n          ← YANGI: nechta xom o'lchovdan hisoblangan (F1 ishonch)
battery
device_clock_utc   ← YANGI
clock_offset_ms    ← YANGI
```

**Olib tashlanadi:**

| Maydon | Sabab |
|---|---|
| `rr_est` | To'qilgan — `hr_mean / 4.5`. Mustaqil ma'lumot nol |
| `sdnn` | 5 ta o'rtacha qiymatdan SDNN chiqmaydi |
| `spo2` | Hech qachon to'ldirilmagan |
| `skin_temp` | Hech qachon to'ldirilmagan |
| `steps` | Har doim `0` |
| `sleep_frag` | Hech qachon to'ldirilmagan |

> Sensor **haqiqatan ishlaganda** qaytariladi. Ishlamaydigan maydon
> `null` bo'lib turgani — yo'q bo'lgandan yomonroq: u ishlayotgandek ko'rinadi.

## 11.8 HRV — avval tekshiriladi

**Qurishdan oldin bajariladigan sinov.** Natija chiqmaguncha `rmssd`
kontraktga kiritilmaydi.

Tekshiriladigan savol:
> Galaxy Watch 5 da Health Services haqiqiy **beat-to-beat RR interval (IBI)**
> berdimi, yo'qmi?

Bajarilishi:
1. Soatda kichik sinov ilovasi
2. Mavjud IBI / RR data type'lari so'raladi, natija loglanadi
3. Kelgan bo'lsa — namuna tezligi va uzilishlar o'lchanadi
4. Hisobot yoziladi

Natijaga qarab:

| Natija | Qaror |
|---|---|
| Haqiqiy IBI keladi | To'g'ri RMSSD quriladi, `rmssd` kontraktga kiradi |
| Kelmaydi yoki ishonchsiz | HRV kontraktdan **butunlay chiqariladi**, `algo/` dagi HRV parametrlari o'chiriladi |

> **Taxmin qilinmaydi.** Soxta HRV baseline'ni buzadi va soxta signal beradi.

## 11.9 Buferlash talablari

| Qatlam | Saqlash | O'chirish sharti |
|---|---|---|
| Soat | Room DB, doimiy | Server ACK |
| Telefon | Room DB, doimiy | Server ACK |

- O'lchov agregator xotirasida emas, **darhol** doimiy xotiraga yoziladi
- Sikl `lifecycleScope` da emas, **foreground service** yoki `WorkManager` da
- Bufer to'lganda **eng eski** yozuv tashlanadi, eng yangisi emas
- Har tashlangan yozuv loglanadi va `F2` bo'yicha texnik vazifa ochadi

> Joriy kod hali Room ishlatmaydi: soat va telefon navbatlari commit bilan
> `SharedPreferences`ga yoziladi, uzatish `WorkManager` va server ACK bilan
> davom etadi. Room'ga o'tish alohida migratsiya; yuqoridagi talab yakuniy
> saqlash maqsadini bildiradi, bugungi implementatsiya deb talqin qilinmaydi.

## 11.10 Ko'p platformali sensor manbalari

| Manba | Qamrov | Ishlash usuli | Chegara |
|---|---|---|---|
| Wear Health Services | Wear OS soati: yurak urishi, qadamlar, kunlik qadam, zinapoya, balandlik o'sishi, faollik holati | Soatdagi Flutter ilovasi, imkoniyatga qarab passiv kuzatuv, lokal navbat va Data Layer | Interval va mavjud sensorlar modelga bog'liq; doimiy sekundlik oqim kafolatlanmaydi |
| Android Health Connect | Android'dagi bir nechta provider, jumladan Samsung Health'da sinxronlangan ma'lumotlar: HR/HRV RMSSD, qon bosimi, glyukoza, vazn/tana yog'i, VO2 max, tana/teri harorati, qadam, uyqu, mashq va energiya | Telefonda foydalanuvchi tanlagan ruxsatlar bilan tarixiy batch o'qish | Faqat Health Connect'ga yozilgan va alohida ruxsat berilgan turlar; vendor'ning raw sensor oqimi emas |
| Apple HealthKit | iPhone/Apple Watch Health store: HR, HRV SDNN, qon bosimi, glyukoza, vazn/tana yog'i, VO2 max, tana harorati, qadam, uyqu, mashq va SpO2 | iOS native bridge, alohida HealthKit roziligi, umumiy batch ingest | Read ruxsati har bir tur uchun foydalanuvchi tomonidan boshqariladi; iOS app qaysi read turiga ruxsat berilganini tekshira olmaydi; HealthKit SDNN RMSSD o'rnini bosmaydi |
| Samsung Health Data SDK | Samsung Health bazasidagi tanlangan tarixiy wellness turlari | Android telefonda SDK va foydalanuvchi ruxsati | Ommaviy tarqatish uchun Samsung app verification/partner ro'yxati kerak; developer mode faqat sinov uchun |
| Samsung Health Sensor SDK | Galaxy Watch4+ BioActive sensorlari: HR/IBI, SpO2, skin temperature; ayrim turlarda raw ECG/PPG/EDA | Galaxy Watch'da alohida vendor SDK; imkoniyat va tracker holati tekshiriladi | Watch modeli va Samsung Health Sensor Service'ga bog'liq; ayrim o'lchovlar faqat foreground/on-demand; wellness SDK, tibbiy tashxis emas |

**Joriy holat:** Health Services, Health Connect va HealthKit `HealthDataBatch`
orqali ulangan. Samsung Health'dan Health Connect'ga kelgan yozuvlar umumiy
provider yo'lida ko'rinadi. Samsung'ning to'g'ridan-to'g'ri SDK'lari alohida
adapter bo'ladi; AAR/licenziya, Galaxy qurilma va rozilik tekshirilmasdan
majburiy build dependency qilinmaydi. HealthKit background delivery alohida
observer/lifecycle ishidir; foreground batch o'qish uni o'rnini bosmaydi.

**Qabul mezoni:** provider nomi, provider record ID, asl vaqt oralig'i, birlik,
rozilik holati va qurilma imkoniyati saqlansin. Turli manbalardagi takroriy
yozuvlar o'chirilmasin yoki qo'shib yuborilmasin; provenance bilan idempotent
saqlansin. Raw ECG/PPG klinik signal pipeline'iga talqin qilinmagan holda
kiritilmaydi.

Rasmiy manbalar:
- Android Health Connect: https://developer.android.com/health-and-fitness/health-connect
- Apple HealthKit observer/background delivery: https://developer.apple.com/documentation/healthkit/executing-observer-queries
- Samsung Health Data SDK: https://developer.samsung.com/health/data/overview.html
- Samsung Health Sensor SDK: https://developer.samsung.com/health/sensor/overview.html

## 11.11 Review mezonlari — qurilma yo'li

Avtomatik rad etiladi:

- [ ] Paketda `device_id` yo'q
- [ ] `patient_id` soat kodida yoki build konfiguratsiyasida
- [ ] `ts` / `window_start` yuborish vaqtidan olingan (chegaraga tekislanmagan)
- [ ] Bufer server ACK dan oldin tozalanadi
- [ ] `catch { }` — bo'sh, loglamaydigan, qayta urinmaydigan
- [ ] UI da sensordan kelmaydigan qattiq yozilgan qiymat
- [ ] Kontraktda 11.7 da olib tashlangan maydon
- [ ] 11.8 sinovi natijasisiz `rmssd` qo'shilgan

---

# 12. Qurilma autentifikatsiyasi

> 11-bo'lim `device_id` ni majburiy qildi. Bu bo'lim uni **kim isbotlashini**
> aniqlaydi. Ularsiz 11-bo'lim himoyasi ochiq: istalgan kishi `device_id`
> yozib real bemorga soxta o'lchov yuborardi.

## 12.1 Asosiy qoida

> **Qurilma tokeni `patient_id` ni olib yurmaydi.**
> U faqat "men shu qurilmaman" deydi. Kimga tegishli ekanini
> `device_assignments` hal qiladi (11.2).

Bu ajratish buzilsa, 11-bo'limning butun himoyasi qulaydi.

## 12.2 Ro'yxatga olish oqimi

```
1. Vakolatli klinika foydalanuvchisi qurilma uchun code yaratadi
   POST /devices/enroll {device_id}       → 6 raqam, 10 daqiqa amal qiladi
2. Qurilma egasi device ID va kodni Flutter qurilma rejimiga kiritadi
   POST /devices/claim {device_id, code}  → muvaffaqiyatda bir martalik token
3. Kod DB'da hash holida saqlanadi, 5 noto'g'ri urinishda bloklanadi
4. Yangi credential yaratiladi, oldingi faol credential bekor qilinadi
5. Token iOS Keychain / Android secure storage'da saqlanadi
```

> Kod serverda **ochiq saqlanmaydi** — faqat hash. Qurilma tokeni faqat
> bir martalik claim javobida beriladi; yo'qolsa credential bekorlanib,
> yangi kod orqali qayta enrollment qilinadi.

## 12.3 Jadval

```sql
CREATE TABLE device_credentials (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    secret_hash TEXT NOT NULL,              -- argon2 yoki bcrypt
    issued_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    issued_by   UUID REFERENCES accounts(id),
    last_used_at TIMESTAMPTZ,
    revoked_at  TIMESTAMPTZ,
    revoke_reason TEXT
);

-- Bir vaqtda bitta amaldagi sir
CREATE UNIQUE INDEX idx_one_active_credential
    ON device_credentials (device_id) WHERE revoked_at IS NULL;

CREATE TABLE device_enrollments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    code_hash   TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    attempts    SMALLINT NOT NULL DEFAULT 0
);
```

## 12.4 So'rov autentifikatsiyasi

```
Authorization: Device <device_id>.<device_secret>
```

TLS ustidan, oddiy bearer. Har so'rovda:

| Qadam | Tekshiruv |
|---|---|
| 1 | `device_credentials` da sir hash mos keladimi |
| 2 | `revoked_at IS NULL` |
| 3 | `devices.status` `retired` / `lost` emasmi |
| 4 | `last_used_at` yangilanadi |

Muvaffaqiyatsiz → `401`, urinish `access_log` ga yoziladi.

> **Nega HMAC imzo emas:** `A3` sodda — bitta mexanizm. Takroriy hujum
> (replay) baribir zarar keltirmaydi, chunki `(device_id, window_start)`
> kaliti dublikatni qabul qilmaydi (11.4).

## 12.5 Bekor qilish

Sir **darhol** bekor qilinadi:

| Sabab | Kim |
|---|---|
| Qurilma yo'qolgan / o'g'irlangan | Klinika admini yoki qarovchi |
| Bemor bilan aloqa tugadi va qurilma qaytmadi | Klinika |
| Shubhali faollik (boshqa mintaqadan IP, g'ayritabiiy tezlik) | Avtomatik + bildirishnoma |

Bekor qilingandan keyin soatdan kelgan ma'lumot **qabul qilinmaydi**,
lekin **o'chirilmaydi** — `orphan_readings` ga `rejected` belgisi bilan
yoziladi (`K1`).

## 12.6 Vakolat matritsasi — kim nima qila oladi

| Harakat | Klinika admini | Hamshira | Qarovchi | Bemor |
|---|---|---|---|---|
| Qurilmani bazaga kiritish | ✅ | ❌ | ❌ | ❌ |
| Ro'yxatga olish (enroll) | ✅ | ✅ | ✅ o'z qurilmasi | ❌ |
| Bemorga biriktirish | ✅ | ✅ o'z mahallasi | ✅ o'z bemori | ❌ |
| Biriktirishni bekor qilish | ✅ | ✅ | ✅ | ❌ |
| Sirni bekor qilish | ✅ | ❌ | ✅ o'z qurilmasi | ❌ |
| Yetim o'lchovni biriktirish | ✅ | ✅ | ❌ | ❌ |

> Yetim o'lchovni faqat klinik xodim biriktiradi — oila a'zosi bemorning
> ma'lumotiga boshqa o'lchov qo'sha olmasligi kerak (`F4`, `G4` ishonch).

---

# 13. API kontrakti

> **Majburiy:** har bir ishchi agent faqat shu ro'yxatdagi endpointlarni
> yozadi. Yangi endpoint kerak bo'lsa — kod emas, **savol** yuboriladi.
>
> `contracts/openapi.yaml` hozirgi holatda **eski modelga** tegishli
> (`patient_id` bilan ingest) va u 5-bosqichda shu bo'lim bo'yicha
> qayta yoziladi.

Umumiy qoidalar:

- Prefiks: `/api/v1`
- Har javob `request_id` sarlavhasini qaytaradi
- Sahifalash: `?limit=&cursor=`, `limit` maksimum 100
- Xato formati bitta: `{"error": {"code": "...", "message": "...", "field": "..."}}`
- Vaqt — ISO-8601 UTC, `Z` bilan

## 13.1 Autentifikatsiya

| Metod | Yo'l | Izoh |
|---|---|---|
| `POST` | `/auth/request-code` | Telefon → SMS kod |
| `POST` | `/auth/verify-code` | Kod → access + refresh token |
| `POST` | `/auth/refresh` | Token yangilash |
| `POST` | `/auth/logout` | Refresh tokenni bekor qilish |
| `GET` | `/auth/me` | Hisob + a'zoliklar + mahallalar |

> Rol yo'q — `/auth/me` **a'zoliklar ro'yxatini** qaytaradi (1.3).
> Mijoz shu ro'yxatdan qaysi oynani ko'rsatishni hal qiladi.

## 13.2 Bemor

| Metod | Yo'l | Izoh |
|---|---|---|
| `GET` | `/patients` | Ko'rinadigan bemorlar (`visible_patients`) |
| `POST` | `/patients` | Yangi bemor yaratish |
| `GET` | `/patients/{id}` | Tafsilot |
| `PATCH` | `/patients/{id}` | Profil tahriri |
| `GET` | `/patients/{id}/timeline` | Hodisalar lentasi |
| `GET` | `/patients/{id}/readings` | O'lchovlar, oraliq bilan |
| `GET` | `/patients/{id}/baseline` | Joriy baseline |
| `POST` | `/patients/{id}/baseline/approve` | Shifokor muzlatadi |
| `POST` | `/patients/{id}/deceased` | `J1` — qo'lda, tasdiq bilan |

## 13.3 Ulanish va rozilik

| Metod | Yo'l | Izoh |
|---|---|---|
| `POST` | `/patients/{id}/memberships` | Klinika qabul qiladi (`C1`) |
| `DELETE` | `/patients/{id}/memberships/{mid}` | Parvarishni tugatish |
| `POST` | `/patients/{id}/memberships/{mid}/baseline-decision` | `C3` |
| `POST` | `/patients/{id}/access/invite` | Qarindoshni taklif qilish |
| `POST` | `/access/accept` | Taklifni qabul qilish |
| `DELETE` | `/patients/{id}/access/{aid}` | Ruxsatni olib tashlash |
| `GET` | `/patients/{id}/consents` | Roziliklar holati |
| `POST` | `/patients/{id}/consents` | Rozilik yozish (`B4`) |
| `POST` | `/patients/{id}/consents/{cid}/revoke` | Bekor qilish (`B5`) |

## 13.4 Qurilma

| Metod | Yo'l | Auth | Izoh |
|---|---|---|---|
| `POST` | `/devices` | hisob | Bazaga kiritish |
| `GET` | `/devices` | hisob | Ro'yxat |
| `POST` | `/devices/enroll` | hisob | 12.2 · 3-qadam |
| `POST` | `/devices/{id}/assign` | hisob | Bemorga biriktirish |
| `POST` | `/devices/{id}/release` | hisob | Biriktirishni yopish |
| `POST` | `/devices/{id}/revoke-credential` | hisob | 12.5 |
| `GET` | `/devices/{id}/health` | hisob | Batareya, oxirgi aloqa |

## 13.5 Ingest — qurilma kanali

| Metod | Yo'l | Auth |
|---|---|---|
| `POST` | `/ingest/readings` | **qurilma tokeni** |
| `POST` | `/ingest/sos` | qurilma tokeni |

So'rov tanasi **`patient_id` ni O'Z ICHIGA OLMAYDI** (11.2):

```json
{
  "device_clock_utc": "2026-09-22T10:05:03Z",
  "readings": [
    {
      "window_start": "2026-09-22T10:00:00Z",
      "window_end":   "2026-09-22T10:05:00Z",
      "hr_mean": 78.4, "hr_min": 71.0, "hr_max": 94.0,
      "worn": true, "worn_pct": 100, "samples_n": 5,
      "battery": 62
    }
  ]
}
```

Javob:

```json
{
  "server_time": "2026-09-22T10:05:04Z",
  "accepted":  ["2026-09-22T10:00:00Z"],
  "duplicate": [],
  "orphaned":  [],
  "rejected":  []
}
```

| Maydon | Ma'nosi | Soat nima qiladi |
|---|---|---|
| `accepted` | Bemorga yozildi | Buferdan o'chiradi |
| `duplicate` | Allaqachon bor | Buferdan o'chiradi |
| `orphaned` | Biriktirish oynasi topilmadi, saqlandi | Buferdan o'chiradi |
| `rejected` | Qabul qilinmadi (yaroqsiz) | Buferdan o'chiradi, loglaydi |

> `server_time` — 11.5 dagi `clock_offset_ms` shu yerdan hisoblanadi.
> **ACK = to'rt ro'yxatning birida bo'lish.** Javob kelmasa — o'chirilmaydi.

## 13.6 Yetim o'lchovlar

| Metod | Yo'l | Izoh |
|---|---|---|
| `GET` | `/orphans` | Hal qilinmaganlar, qurilma bo'yicha |
| `GET` | `/orphans/{id}/candidates` | `orphan_candidates()` — cheklangan ro'yxat |
| `POST` | `/orphans/{id}/resolve` | Bemorga biriktirish, `attributed_by='nurse'` |
| `POST` | `/orphans/{id}/discard` | Tashlash — o'chirilmaydi, belgilanadi |

## 13.7 Signal va vazifa

| Metod | Yo'l | Izoh |
|---|---|---|
| `GET` | `/alerts` | Filtrlar bilan |
| `GET` | `/tasks` | Mening vazifalarim |
| `POST` | `/tasks/{id}/acknowledge` | Ko'rdim (15.3) |
| `POST` | `/tasks/{id}/complete` | Bajarildi + izoh |
| `POST` | `/tasks/{id}/reassign` | Boshqaga o'tkazish (`D5`) |
| `POST` | `/sos` | Ilovadan SOS |

## 13.8 Pul

| Metod | Yo'l | Izoh |
|---|---|---|
| `GET` | `/patients/{id}/subscription` | Obuna holati (`E1`) |
| `POST` | `/patients/{id}/subscription/checkout` | To'lov boshlash |
| `POST` | `/webhooks/payments/{provider}` | Provayder qaytarishi |
| `GET` | `/tenants/{id}/licence` | Litsenziya |
| `GET` | `/tenants/{id}/usage` | Bemor-kun hisoboti (`E3`) |
| `GET` | `/tenants/{id}/invoices` | Hisob-fakturalar |

## 13.9 So'rovnoma

| Metod | Yo'l | Izoh |
|---|---|---|
| `GET` | `/surveys/pending` | Menga tegishli so'rovnomalar |
| `GET` | `/surveys/{id}` | Savollar (10s darvoza mijozda) |
| `POST` | `/surveys/{id}/submit` | Javoblar + `per_question_ms` |

## 13.10 Platforma oynasi

| Metod | Yo'l | Izoh |
|---|---|---|
| `GET` | `/platform/research/cohort` | Shaxssizlantirilgan (`H1`) |
| `GET` | `/platform/support/patients/{id}` | To'liq — **`reason` majburiy** (`H2`) |
| `GET` | `/platform/access-log` | Kim nimani ko'rgan |

## 13.11 Xizmat

| Metod | Yo'l |
|---|---|
| `GET` | `/health` |
| `GET` | `/health/ready` |
| `GET` | `/metrics` |

---

# 14. Postgres RLS — oxirgi himoya

> 6-bo'lim uchta himoya qatlamini sanadi. Bu — uchinchisi.
> Maqsadi: `ScopedRepository` da xato qilinsa ham bir klinika
> boshqasining bemorini **DB darajasida** o'qiy olmasligi.

## 14.1 Sessiya o'zgaruvchilari

Har so'rov boshida ulanishga yoziladi, oxirida tozalanadi:

```sql
SET LOCAL wmax.account_id = '<uuid>';
SET LOCAL wmax.tenant_ids = '<uuid>,<uuid>';
SET LOCAL wmax.bypass     = 'off';   -- faqat migratsiya va fon ishi uchun 'on'
```

> `SET LOCAL` — tranzaksiya doirasida. Ulanish hovuzida (`pool`)
> keyingi so'rovga **sizib o'tmaydi**. `SET` (LOCAL'siz) ishlatish —
> avtomatik rad etiladi.

## 14.2 Qamrab olinadigan jadvallar

| Jadval | Siyosat asosi |
|---|---|
| `patients` | a'zolik yoki `patient_access` |
| `readings` | `patients` orqali |
| `alerts` | `patients` orqali |
| `tasks` | `tenant_id` + `assignee_account_id` |
| `device_assignments` | `patients` orqali |
| `patient_consents` | `patients` orqali |
| `patient_conditions` · `patient_medications` | `patients` orqali |
| `billing_days` · `invoices` | `tenant_id` |

### RLS QO'YILMAYDIGAN jadvallar ⚠️

`patient_memberships` va `patient_access` ga RLS **ataylab qo'yilmaydi**.

Sabab: `patients` siyosati shu ikki jadvalni o'qiydi. Ularga ham RLS
qo'yilsa, ularning siyosati yana `patients` ga qarashi kerak bo'ladi →
**cheksiz rekursiya**, Postgres so'rovni to'xtatadi.

Ular `ScopedRepository` darajasida himoyalanadi (6.1). Bu qatlamlar
ataylab turlicha — ikkalasi bir xil mexanizm bo'lsa, bitta xato
ikkalasini ham ochib yuboradi.

> Bu ikki jadvalga RLS qo'shadigan PR **rad etiladi**, "xavfsizroq
> bo'lsin" degan sabab bilan ham.

`accounts`, `tenants`, `devices`, `device_credentials` ham RLS'siz —
ular vakolat manbai, himoya `ScopedRepository` da.

## 14.3 Asosiy siyosat

```sql
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients FORCE ROW LEVEL SECURITY;

CREATE POLICY patients_visible ON patients
FOR SELECT USING (
    current_setting('wmax.bypass', true) = 'on'
    OR EXISTS (
        SELECT 1 FROM patient_memberships m
        WHERE m.patient_id = patients.id
          AND m.revoked_at IS NULL
          AND m.tenant_id::text = ANY(
              string_to_array(current_setting('wmax.tenant_ids', true), ',')
          )
    )
    OR EXISTS (
        SELECT 1 FROM patient_access a
        WHERE a.patient_id = patients.id
          AND a.revoked_at IS NULL
          AND a.account_id::text = current_setting('wmax.account_id', true)
    )
);
```

> **Mahalla filtri RLS da EMAS.** `B6` biznes qoidasi — u
> `domain/access.py` da qoladi. RLS faqat **tenant chegarasini**
> ushlaydi. RLS ga biznes mantig'i solinsa u testlanmaydigan bo'lib qoladi.

## 14.4 Bypass — qat'iy cheklangan

`wmax.bypass = 'on'` faqat uch joyda:

| Joy | Sabab |
|---|---|
| Alembic migratsiyalari | Sxema o'zgarishi |
| Fon ishlari (baseline, billing, partitsiya) | Butun to'plam bo'yicha |
| Platforma tadqiqot oynasi (`H1`) | Shaxssizlantirilgan, `access_log` bilan |

HTTP so'rov ishlov beruvchisida `bypass` yoqish — **avtomatik rad etiladi**.

## 14.5 Majburiy testlar

- [ ] Klinika A hisobi klinika B bemorini `SELECT` qila olmaydi
- [ ] Qarovchi ruxsati bekor qilingach bemor ko'rinmaydi
- [ ] `SET LOCAL` tranzaksiya tugagach qolmaydi (hovuz sizishi)
- [ ] `bypass='off'` da fon ishi so'rovi bo'sh qaytaradi
- [ ] `patients` so'rovi rekursiyasiz ishlaydi (14.2)

---

# 15. Signal → vazifa → eskalatsiya

> `tasks` jadvalida `due_at`, `reminded_at`, `escalated_at` ustunlari bor.
> Bu bo'lim ular **qachon** to'lishini aniqlaydi.
>
> Vaqtlar **sozlanadigan**, lekin standart qiymatlar shu yerda.

## 15.1 Signal darajalari

| Daraja | Ma'nosi | `D4` |
|---|---|---|
| `green` | Baseline doirasida | — |
| `amber` | Chetlanish, shoshilinch emas | — |
| `red` | Jiddiy chetlanish | **hech qachon pullik emas** |
| `no_data` | O'lchov yo'q | — |

## 15.2 Signaldan vazifagacha

```
signal yaratildi
   ↓
should_create_task(state, level)        ← domain/responsibility.py · D5
   ↓ false → vazifa YO'Q (bajaruvchi yo'q)
   ↓ true
task_kind(quality, level)               ← domain/quality.py · F2
   ↓
   ├── clinical  → due_at qo'yiladi, eskalatsiya bor
   └── technical → due_at YO'Q, taymer yo'q
   ↓
notification_targets(state, level)      ← domain/responsibility.py · D3
```

> `should_create_task` `false` qaytarsa ham **bildirishnoma yuboriladi**.
> `D3` vazifadan qat'i nazar kamida bitta javobgarni xabardor qiladi.

## 15.3 Standart vaqtlar

### `clinical` vazifa

| Daraja | `due_at` | 1-eslatma | Eskalatsiya |
|---|---|---|---|
| `red` | +2 soat | +15 daq | +30 daq → bosh shifokor |
| `amber` | +24 soat | +4 soat | +12 soat → bosh shifokor |
| `no_data` | +48 soat | +12 soat | yo'q |

### `technical` vazifa

| | Qiymat |
|---|---|
| `due_at` | **`NULL`** — taymer yo'q |
| Eslatma | kuniga bir marta, 3 kun |
| Eskalatsiya | yo'q — 3 kundan keyin klinika hisobotiga tushadi |

> `F2` sababi: sifatsiz ma'lumotdan kelib chiqqan signal uchun hamshirani
> tunda uyg'otish — ishonchni yo'qotadi. Bemor yashirilmaydi, lekin
> so'raladigan harakat "soatni tekshiring" bo'ladi, "bemorga boring" emas.

## 15.4 Holatlar

```
open ──acknowledge──▶ acknowledged ──complete──▶ done
 │                         │
 │                         └──due_at o'tdi──▶ overdue
 ├──due_at o'tdi──────────────────────────▶ overdue
 └──bemor chiqdi / vafot etdi────────────▶ cancelled
```

| O'tish | Kim |
|---|---|
| `acknowledge` | Faqat `assignee_account_id` |
| `complete` | Faqat `assignee_account_id` — izoh **majburiy** |
| `reassign` | Klinika admini yoki bosh shifokor · yangi bajaruvchi majburiy (`D5`) |
| `cancel` | Tizim — `J2` yoki parvarish tugaganda |

## 15.5 Signal bostirish (alert fatigue)

> Bu `F2` ni to'ldiradi. Takroriy signal hamshirani ko'mib tashlamasligi kerak.

| Qoida | Qiymat |
|---|---|
| Bir xil bemor + bir xil parametr + `amber` | 6 soatda bir marta vazifa |
| Bir xil bemor + `red` | **bostirilmaydi** — har safar |
| `no_data` | kuniga bir marta |
| Ochiq vazifa bor | Yangi vazifa emas — mavjudi yangilanadi |

> `red` hech qachon bostirilmaydi. `D4` bilan bir mantiq: eng muhim
> signalni tejash mumkin emas.

## 15.6 Bildirishnoma zanjiri — `I2`

```
app push ──15 daq javob yo'q──▶ Telegram ──15 daq──▶ SMS ──15 daq──▶ ovozli qo'ng'iroq
```

- Zanjir **tasdiqlanmaguncha** davom etadi
- `red` da qadamlar orasida 5 daqiqa (15 emas)
- Har urinish `notification_attempts` ga yoziladi
- `urgent = true` bo'lsa — qabul qiluvchining tungi rejimini **buzadi**
  (`I1`: kelishuv — uxlab yotgan bo'lsa ham yuboriladi)
- Ovozli qo'ng'iroqdan keyin ham javob bo'lmasa → keyingi javobgarga o'tadi

---

# 16. Mavjud ma'lumot bilan nima bo'ladi

> 8-bo'lim "alembic zanjiri noldan" deydi. Bu bo'lim bazada **hozir turgan**
> ma'lumot taqdirini aniqlaydi. `K1` — hech narsa o'chirilmaydi.

## 16.1 Hozirgi holat

| | Qiymat |
|---|---|
| Migratsiyalar | 2 ta (`20260919_0129`, `20260919_0751`) |
| Modellar | 26 |
| API modullari | 10 |

Baza yosh — bu migratsiyani sezilarli osonlashtiradi.

## 16.2 Birinchi qadam — audit (0-bosqichdan OLDIN)

Hech narsa o'chirilmasdan oldin bajariladi:

```
1. Har jadvaldagi qatorlar soni sanaladi
2. Haqiqiy (production) ma'lumot bormi — demo urug'idan farqlanadi
3. Natija docs/DATA_AUDIT.md ga yoziladi
```

`scripts/seed_demo.py` yaratgan ma'lumot — demo. Undan tashqarisi bo'lsa
haqiqiy deb hisoblanadi.

## 16.3 Ikki yo'l

### A · Haqiqiy ma'lumot yo'q

```
1. To'liq zaxira nusxa (pg_dump) → arxivga
2. Baza tashlanadi va yangi sxema bilan qayta quriladi
3. Demo urug'i yangi model bo'yicha qayta yoziladi
```

Eng tez yo'l. Zaxira nusxa **baribir olinadi**.

### B · Haqiqiy ma'lumot bor

```
1. To'liq zaxira nusxa → arxivga
2. Eski sxema legacy_ prefiksi bilan saqlanadi (ALTER SCHEMA)
3. Yangi sxema yonida quriladi
4. Ko'chirish skripti yoziladi → 16.4
5. Solishtirish tekshiruvi o'tgach eski sxema o'qish-uchun qoladi
6. Eski sxema HECH QACHON o'chirilmaydi (K1)
```

## 16.4 Ko'chirish xaritasi

| Eski | Yangi | Izoh |
|---|---|---|
| `users` | `accounts` + `tenant_members` | Rol ustuni a'zolikka aylanadi (1.3) |
| `patients.tenant_id` | `patient_memberships` | Egalik a'zolikka aylanadi (1.1) |
| `relatives` | `patient_access` | `role='caregiver'` |
| `tenants` (`kind='household'`) | **ko'chirilmaydi** | B2C da tenant yo'q (1.2) |
| `subscriptions` | `patient_subscriptions` | Hisobdan bemorga ko'chadi (`E1`) |
| `readings.ts` | `readings.window_start` | **Chegaraga tekislanadi** (11.4) |
| `readings.rr_est` · `sdnn` | **tashlanadi** | 11.7 — soxta |
| `readings.spo2` · `skin_temp` · `steps` | **tashlanadi** | 11.7 — har doim bo'sh |
| `device_assignments` | o'zi | `provenance='unknown'` bilan |
| `measurements` · `admissions` | `patient_outcomes` | |

### Hal qilinishi kerak bo'lgan holatlar

| Holat | Qaror |
|---|---|
| Bir bemorda bir nechta ochiq a'zolik | Eng yangisi qoladi, qolgani `revoked` (`C1`) |
| `tenant_id` yo'q bemor | A'zoliksiz qoladi — `promise_level = awareness` |
| Rol `relative` bo'lgan `users` | `accounts` + `patient_access` |
| Bir xil `window_start` ga tushgan ikki o'lchov | Birinchisi qoladi, ikkinchisi `orphan_readings` ga |
| Roziligi yo'q bemor | `consent_method='verbal_by_clinician'`, `witnessed_by=NULL`, **qayta so'raladi** |

> Oxirgi qator muhim: eski ma'lumotda rozilik yozuvi yo'q. Uni "bor" deb
> belgilash — `B4` ni buzish. Belgilanadi va qayta so'raladi.

## 16.5 Tekshiruv

Ko'chirishdan keyin, eski sxemani yopishdan oldin:

- [ ] Bemorlar soni mos
- [ ] Har bemorda ko'pi bilan bitta ochiq parvarish egasi
- [ ] O'lchovlar soni: yangi + yetim = eski
- [ ] Hech bir o'lchov bemorsiz qolmagan (yoki ataylab yetim)
- [ ] Obunalar summasi mos
- [ ] Tasodifiy 20 bemor qo'lda solishtirilgan

---

# 17. Partitsiya boshqaruvi

> `readings` `PARTITION BY RANGE (window_start)` deb e'lon qilingan.
> Partitsiyani **kimdir yaratishi** kerak — aks holda birinchi yozuv
> `no partition found` xatosi bilan tushadi.

## 17.1 Qoida

| | Qiymat |
|---|---|
| Oraliq | Oylik |
| Nom | `readings_YYYY_MM` |
| Oldindan yaratish | **3 oy** oldinga |
| Kim yaratadi | Kunlik fon ishi |
| Zaxira partitsiya | `readings_default` — hech qachon bo'sh bo'lmasligi kerak |

## 17.2 Monitoring

- `readings_default` da qator paydo bo'lsa → **darhol ogohlantirish**
  (partitsiya yaratilmagan degani)
- Har partitsiya hajmi `metrics` ga chiqadi
- Migratsiya joriy oy + 3 oyni oldindan yaratadi

## 17.3 Siqish — keyin

`K3`: hozir bo'linadi, keyin siqiladi. 12 oydan eski partitsiyalar
siqiladi yoki sekin xotiraga ko'chiriladi. **O'chirilmaydi** (`K1`).

Bu hozir qurilmaydi — faqat sxema buni keyin qo'shish mumkin bo'ladigan
qilib tuzilgan.

---

# 18. Ma'lumot oqimlari

> `IDEOLOGY.md` oxirida va'da qilingan olti oqim. Har biri qaysi
> bandlarni ishlatishini ko'rsatadi.

## 18.1 Oqim — Qarovchi bemorni ulaydi (B2C)

```
Qizi ilovaga kiradi (telefon + SMS)
   └─▶ accounts yozuvi
Onasini qo'shadi
   └─▶ patients (tenant_id YO'Q · B1)
   └─▶ patient_access(role='payer', relation='qizi' · B3)
Onasiga SMS: "Qizingiz sizni kuzatmoqchi. Roziq/Rad"
   └─▶ patient_consents(scope='family_access' · B4)
Soat ro'yxatga olinadi
   └─▶ device_enrollments → device_credentials (12.2)
   └─▶ device_assignments(provenance='self_purchased' · F1)
Obuna
   └─▶ patient_subscriptions (BEMORGA · E1)
```

**Va'da darajasi:** `awareness` — parvarish egasi yo'q (`C2`).
Vazifa yaratilmaydi (`D5`), lekin `red` signal va SOS ishlaydi (`D4`).

## 18.2 Oqim — Klinika parvarishni qabul qiladi (B2C → B2B)

```
Hamshira bemorni qabul qilmoqchi
   └─▶ licence.intake_blocked_at tekshiriladi (C4)
   └─▶ bemorga SMS: klinik kuzatuv roziligi (B5)
Rozilik kelgach
   └─▶ patient_memberships(kind='care') · BITTA ochiq (C1)
Klinika mavjud baseline'ni ko'radi
   └─▶ baseline_decision: accepted | relearn | rejected (C3)
```

**Va'da darajasi:** `awareness` → `accountable` (`C2`).
Endi vazifalar yaratiladi. Oilaning obunasi bunga **ta'sir qilmaydi** (`D2`).

## 18.3 Oqim — O'lchov keladi

```
Soat: 5 daqiqalik oyna yopiladi
   └─▶ Room DB ga yoziladi (11.9)
   └─▶ telefonga uzatiladi → telefon Room DB
Telefon: POST /ingest/readings
   └─▶ Device tokeni tekshiriladi (12.4)   → 401 bo'lsa to'xtaydi
   └─▶ attribute_reading(ts, device, windows)  ← domain/attribution.py · F4
         ├── bemor topildi → readings
         │      ON CONFLICT (device_id, window_start) DO NOTHING  (11.4)
         └── topilmadi     → orphan_readings
   └─▶ javob: accepted / duplicate / orphaned / rejected (13.5)
Soat va telefon: ACK kelgan yozuvlarni o'chiradi
```

> Hech bir bosqichda `patient_id` qurilmadan kelmaydi.

## 18.4 Oqim — Signaldan harakatga

```
readings → algo/baseline · algo/signal · algo/anomaly
   └─▶ alerts (data_quality bilan)
   └─▶ should_create_task(state, level)        · D5
         └── false → vazifa yo'q
   └─▶ task_kind(quality, level)               · F2
         ├── clinical  → due_at (15.3) · eskalatsiya
         └── technical → taymer yo'q
   └─▶ 15.5 bostirish tekshiruvi
   └─▶ notification_targets(state, level)      · D3
   └─▶ I2 zanjiri: push → TG → SMS → qo'ng'iroq (15.6)
```

## 18.5 Oqim — Obuna tugaydi

```
patient_subscriptions.status → 'lapsed'
   └─▶ family_features(state)                  · domain/entitlement.py
         ├── LIVE_STATUS · ACTIVITY · TREND · HISTORY  → BLOKLANADI
         └── CRITICAL_ALERT · SOS                      → QOLADI (D4)
   └─▶ clinical_pipeline_enabled(state)        → O'ZGARMAYDI (D2)
         hamshira hammasini ko'rishda davom etadi
   └─▶ oilaga xabar: "Obuna tugadi"
```

> Klinik kuzatuv **hech qachon** oilaning to'lovi bilan to'xtamaydi.

## 18.6 Oqim — So'rovnoma va haqiqat halqasi

```
Obuna to'lovidan oldin: "3 savol → chegirma"
   └─▶ GET /surveys/{id}
   └─▶ mijoz: 10 soniya darvoza (savol ko'rinadi, javob yopiq)
   └─▶ POST /surveys/{id}/submit + per_question_ms
Server sifat baholaydi:
   ├── straightline        (bir xil javob)
   ├── reverse_conflict    (teskari savol bilan zid)
   ├── fact_conflict       (kuzatilgan faktga zid · G5)
   └── javob vaqti dispersiyasi
   └─▶ quality: trusted | weak | rejected
   └─▶ CHEGIRMA HAR DOIM BERILADI (G4)
   └─▶ faqat 'trusted' modelga kiradi
```

---

# 19. Frontend qamrovi

> 8-bo'limning 7-bosqichi. Har ilova uchun nima o'zgaradi.

## 19.1 `mobile_flutter` — qarovchi va bemor ilovasi

| Ish | Sabab |
|---|---|
| Kirish: telefon + SMS | Rol tanlash ekrani **olib tashlanadi** (1.3) |
| Bemor qo'shish oqimi | 18.1 |
| Rozilik ekranlari | `B4` · `B5` |
| Qurilma ro'yxatga olish (QR) | 12.2 |
| **Biriktirish ekrani: "Kimga?"** | 11.3 · 3-qadam |
| Obuna oynasi | `E1` — istalgan a'zo to'laydi |
| Bloklangan bo'limlar ko'rinadi, ochilmaydi | 18.5 |
| SOS — obunadan qat'i nazar | `D4` |
| So'rovnoma + 10s darvoza | 18.6 |

## 19.2 `web-doctor` — klinika oynasi

| Ish | Sabab |
|---|---|
| Ish ro'yxati **mahalla bo'yicha** filtrlanadi | `B6` |
| Vazifa turi ajratiladi: klinik / texnik | `F2` |
| Baseline qabul qilish ekrani | `C3` |
| **Yetim o'lchovlar ekrani** | 13.6 |
| Qurilma boshqaruvi: biriktirish, bo'shatish, bekor qilish | 12.6 |
| Bemor-kun hisoboti | `E3` — ma'lumotsiz kunlar alohida |
| Litsenziya to'lanmagan bannner: "qabul to'xtadi" | `C4` |

## 19.3 `web-relative` — birlashtiriladi

Hozir alohida ilova. `mobile_flutter` bilan bir xil vazifani bajaradi.

> **Qaror:** alohida ilova sifatida **qoldirilmaydi**. Qarindoshning
> web-ko'rinishi `mobile_flutter` ning web build'i bo'ladi. Ikki
> kod bazasida bir xil ruxsat mantig'ini saqlash — `D2`/`D4` buzilishining
> eng ehtimoliy manbai.

## 19.4 Platforma konsoli — yangi

| Oyna | Izoh |
|---|---|
| Tadqiqot | Shaxssizlantirilgan kohorta (`H1`) |
| Qo'llab-quvvatlash | To'liq ko'rinish · **sabab majburiy** (`H2`) |
| Kirish jurnali | Kim nimani ko'rgan |

Bu ikki oyna **bir ekranda birlashtirilmaydi** — chalkashish xavfi.

## 19.5 `mobile_flutter` — soat rejimi

| Ish | Sabab |
|---|---|
| Alohida `wear/` Kotlin app bo'lmaydi | bitta Flutter kod bazasi |
| `--dart-define=WMAX_APP_MODE=watch` | soat build'i shu targetdan chiqadi |
| `--dart-define=WMAX_APP_MODE=health` | iPhone HealthKit yoki Android Health Connect manba qurilmasi |
| Health/watch qurilmasi `/devices/claim` orqali bir martalik kodni token bilan almashtiradi | 12.2 |
| Device token iOS Keychain’da, Android’da Keystore AES-GCM bilan shifrlangan lokal storage’da saqlanadi | 12.2 |
| `WMAX_PATIENT_ID` vaqtinchalik debug uchun; device-token asosidagi SOS bilan almashtiriladi | 12.2 |
| Lokal navbat | 11.9 |
| Serverga bevosita yuborish + ACK bo'yicha tozalash | 11.9 |
| Soxta UI qiymatlari olib tashlanadi | 11.1 · D3 |
| `rmssd` faqat haqiqiy IBI tasdiqlansa; hozir `null` | 11.8 |
| `rr_est` · `sdnn` · `spo2` · `skin_temp` taxmin qilinmaydi | 11.7 |
| Oyna vaqt bo'yicha yopiladi | 11.4 |

> Eski `wear/watch` va `wear/phone` yo'nalishi yopildi. Keyingi ishlar
> `mobile_flutter` ichida telefon va soat rejimlari sifatida qilinadi.

---

# 20. Test strategiyasi

> "Tugadi" nimani anglatishini aniqlaydi.

## 20.1 Qatlam bo'yicha

| Qatlam | Tur | Mock | Talab |
|---|---|---|---|
| `algo/` | birlik | yo'q | mavjud 31 test saqlanadi |
| `domain/` | birlik | **taqiqlanadi** | har funksiya · chegaraviy holatlar |
| `repositories/` | integratsiya | yo'q — haqiqiy DB | izolyatsiya testlari majburiy |
| `services/` | integratsiya | faqat tashqi xizmat | |
| `api/` | kontrakt | — | har endpoint uchun auth testi |
| RLS | integratsiya | yo'q | 14.5 |

> `domain/` da mock ishlatilishi — funksiya sof emasligining belgisi.
> Mock kerak bo'lsa, funksiya noto'g'ri yozilgan.

## 20.2 Majburiy xavfsizlik testlari

Bular o'tmasa — hech narsa deploy qilinmaydi.

- [ ] Klinika A klinika B bemorini ko'rmaydi (repozitoriy **va** RLS)
- [ ] Qurilma tokeni bilan boshqa qurilmaning ma'lumoti yozilmaydi
- [ ] Bekor qilingan qurilma tokeni rad etiladi
- [ ] Bir xil paket 5 marta yuborilsa bitta qator
- [ ] Ikki kanaldan bir vaqtda kelsa bitta qator
- [ ] Biriktirish oynasidan tashqari o'lchov `orphan_readings` ga tushadi
- [ ] Obuna tugaganda `red` signal va SOS ishlaydi
- [ ] Obuna tugaganda klinik oqim to'xtamaydi
- [ ] Bajaruvchisiz vazifa yaratilmaydi
- [ ] Rozilik bekor qilingach ko'rinish yopiladi
- [ ] `platform_support` o'qishi `reason`siz rad etiladi

## 20.3 Qurilma yo'li testlari

Simulyator bilan:

- [ ] 7 kun oflayn → ulanadi → hammasi yetib boradi, dublikatsiz
- [ ] Soat soati 3 soatga surilgan → `clock_offset_ms` tuzatadi
- [ ] Telefon almashdi → yangi ma'lumot `orphan`, jimgina biriktirilmaydi
- [ ] Bufer to'ldi → eng eski tashlanadi, texnik vazifa ochiladi
- [ ] ACK kelmadi → bufer tozalanmaydi

## 20.4 Chegaralar

| Ko'rsatkich | Minimum |
|---|---|
| `domain/` qamrovi | **100%** — kichik va sof |
| `algo/` qamrovi | mavjud daraja pasaymaydi |
| Umumiy qamrov | 80% |
| 20.2 ro'yxati | **100% o'tishi shart** |

---

# 21. Tashqi integratsiyalar

## 21.1 To'lov

| | Qaror |
|---|---|
| Provayderlar | Payme · Click · Uzum |
| Yondashuv | Har biriga alohida adapter, bitta umumiy interfeys |
| Takroriy to'lov | **Avtomatik yechish QILINMAYDI** — ishonch masalasi |
| O'rniga | Tugashdan 3 kun oldin eslatma → qo'lda to'lov |
| Webhook | `POST /webhooks/payments/{provider}` · idempotent |
| Idempotentlik | `provider_ref` bo'yicha |

> Avtomatik yechish oddiy foydalanuvchi uchun tushunarsiz va shikoyat
> manbai. `A3` — sodda bo'lsin.

## 21.2 SMS

| | Qaror |
|---|---|
| Foydalanish | Kirish kodi · rozilik so'rovi · `I2` zanjiri |
| Talab | O'zbekistonda ishonchli yetkazish, `+998` |
| Zaxira | Ikkinchi provayder, birinchisi 3 marta tushsa |

Provayder tanlovi — alohida tadqiqot. Kod **interfeys ortida** yoziladi,
provayder almashtirilishi bitta fayl o'zgarishi bo'lsin.

## 21.3 Telegram

`I2` zanjirining ikkinchi bo'g'ini. Bot orqali. Hisobga ulanish
ixtiyoriy — ulanmagan bo'lsa zanjir SMS ga o'tadi.

## 21.4 Ovozli qo'ng'iroq

Zanjirning oxirgi bo'g'ini. Yozib qo'yilgan matn + tasdiqlash uchun
tugma bosish. Provayder keyin tanlanadi.

## 21.5 Umumiy qoida

Har tashqi xizmat:

- Interfeys ortida — `services/integrations/`
- Testlarda soxta (fake) implementatsiya
- Tushib qolsa tizim ishlashda davom etadi
- Har urinish jurnalga yoziladi

---

# 22. Ishchi agentlar uchun topshiriqlar

> Har topshiriq **mustaqil berilishi mumkin** bo'lgan paket. Yonida:
> qaysi bo'limlar bo'yicha quriladi, nimaga bog'liq, nima topshiriladi.
>
> Agent faqat o'z paketini bajaradi. Paketdan tashqari fayl o'zgartirilsa —
> review'da rad etiladi.

## 22.1 Bog'liqlik xaritasi

```
W0 audit ─┬─▶ W3 models ─┬─▶ W4 repos+RLS ─┐
          │              ├─▶ W5 auth ──────┼─▶ W6 api ─┬─▶ W7 notifier
          │              └─▶ W13 migration │           ├─▶ W10 mobile
          │                  (faqat B yo'li)│           ├─▶ W11 web-doctor
          │                                 │           └─▶ W12 platforma
W1 HRV ───┴──────────────────────────────▶ W8 mobile_flutter watch mode
W2 domain ───────────────────────────────▶ W4 · W6
```

**Darhol boshlanishi mumkin:** `W0` · `W1` · `W2` — uchalasi parallel.

## 22.2 Paketlar

### W0 · Ma'lumot auditi
| | |
|---|---|
| Bo'limlar | 16.2 · 16.3 |
| Bog'liq | — |
| Topshiriladi | `docs/DATA_AUDIT.md` · `pg_dump` arxivi · **A yoki B tavsiyasi** |
| Hajm | kichik |

> Kod yozilmaydi. Faqat hisobot. Natijasiz 0-bosqich boshlanmaydi.

### W1 · HRV sinovi
| | |
|---|---|
| Bo'limlar | 11.8 |
| Bog'liq | — |
| Topshiriladi | Sinov ilovasi + `docs/HRV_SPIKE.md` hisoboti |
| Hajm | kichik · ~1 kun |

> Natija salbiy bo'lsa `algo/` dagi HRV parametrlari o'chiriladi.
> Bu **tashlanadigan kod** — saqlanmaydi.

### W2 · `domain/` paketi
| | |
|---|---|
| Bo'limlar | 4 (to'liq) · 20.1 |
| Bog'liq | — |
| Topshiriladi | 6 modul + `types.py` · **100% qamrov** · mocksiz |
| Hajm | o'rta |

> DB, HTTP, `datetime.now()` — taqiq. Mock kerak bo'lsa funksiya
> noto'g'ri yozilgan.

### W3 · Modellar va migratsiya
| | |
|---|---|
| Bo'limlar | 5 (to'liq) · 12.3 · 17 |
| Bog'liq | W0 |
| Topshiriladi | `app/models/` · yangi alembic zanjiri · partitsiya ishi |
| Hajm | katta |

> Migratsiya `--autogenerate` bilan. Qo'lda yozilgan migratsiya rad etiladi.

### W4 · Repozitoriylar va RLS
| | |
|---|---|
| Bo'limlar | 6.1 · 14 |
| Bog'liq | W2 · W3 |
| Topshiriladi | `ScopedRepository` + repozitoriylar · RLS siyosatlari · 14.5 testlari |
| Hajm | o'rta |

### W5 · Auth va qurilma tokeni
| | |
|---|---|
| Bo'limlar | 6.2 · 12 (to'liq) · 13.1 |
| Bog'liq | W3 |
| Topshiriladi | `app/auth/` · ro'yxatga olish oqimi · bekor qilish · rozilik |
| Hajm | o'rta |

### W6 · Servislar va API
| | |
|---|---|
| Bo'limlar | 13 (to'liq) · 15 · 18 |
| Bog'liq | W2 · W4 · W5 |
| Topshiriladi | `app/services/` · `app/api/` · yangi `contracts/openapi.yaml` |
| Hajm | katta |

> **Faqat 13-bo'limdagi endpointlar.** Yangi kerak bo'lsa — savol yuboriladi.

### W7 · Bildirishnoma
| | |
|---|---|
| Bo'limlar | 15.6 · 21.2–21.5 |
| Bog'liq | W6 |
| Topshiriladi | `notifier/` · `I2` zanjiri · integratsiya interfeyslari + fake'lar |
| Hajm | o'rta |

### W8 · `mobile_flutter` soat rejimi
| | |
|---|---|
| Bo'limlar | 11 (to'liq) · 12.2 · 19.5 |
| Bog'liq | W1 · W5 |
| Topshiriladi | Flutter watch mode · lokal navbat · yangi kontrakt · enroll ekrani |
| Hajm | katta |

> 11.1 dagi 15 nosozlikning har biri yopilgani ko'rsatilishi shart.

### W10 · `mobile_flutter`
| | |
|---|---|
| Bo'limlar | 19.1 · 18.1 · 18.5 · 18.6 |
| Bog'liq | W6 |
| Topshiriladi | Yangi kirish · rozilik · biriktirish · obuna · so'rovnoma |
| Hajm | katta |

### W11 · `web-doctor`
| | |
|---|---|
| Bo'limlar | 19.2 · 13.6 · 15 |
| Bog'liq | W6 |
| Topshiriladi | Mahalla filtri · vazifa turlari · yetim o'lchovlar · hisobot |
| Hajm | katta |

### W12 · Platforma konsoli
| | |
|---|---|
| Bo'limlar | 19.4 · 13.10 · `H1` · `H2` |
| Bog'liq | W6 |
| Topshiriladi | Ikki alohida oyna · kirish jurnali |
| Hajm | o'rta |

### W13 · Ma'lumot ko'chirish — faqat B yo'lida
| | |
|---|---|
| Bo'limlar | 16.4 · 16.5 |
| Bog'liq | W0 (B tavsiyasi) · W3 |
| Topshiriladi | Ko'chirish skripti · solishtirish hisoboti |
| Hajm | o'rta |

## 22.3 Har paket uchun umumiy talablar

Bular har topshiriqda takrorlanmaydi — **doim amal qiladi**:

- [ ] PR tavsifida qaysi bo'lim va qaysi ideologiya bandi bajarilgani yozilgan
- [ ] Spetsifikatsiyada yo'q narsa qo'shilmagan
- [ ] 9-bo'limdagi avtomatik rad ro'yxatidan hech biri buzilmagan
- [ ] 20-bo'lim bo'yicha testlar yozilgan
- [ ] Paket chegarasidan tashqari fayl o'zgartirilmagan

## 22.4 Nizo bo'lganda

| Holat | Harakat |
|---|---|
| Spetsifikatsiya noaniq | **Savol yuboriladi.** Taxmin qilinmaydi |
| Spetsifikatsiya ichida ziddiyat | Savol yuboriladi, ikkala joy ko'rsatiladi |
| Ideologiya bandi noto'g'ri ko'rinadi | `IDEOLOGY.md` o'zgartiriladi, **keyin** kod |
| Texnik jihatdan bajarib bo'lmaydi | Sabab bilan hisobot · muqobil taklif |

> Hech qaysi holatda "o'zimcha qilib qo'ya qolay" javobi qabul qilinmaydi.

## 23. Tez va yo'qolmaydigan ma'lumot almashish

### 23.1 Transport tanlovi

| Oqim | Transport | Sabab |
|---|---|---|
| Soat → backend fiziologik o'lchovlar | Qisqa HTTP batch + ACK | Wear OS background rejimida doimiy socket ishonchsiz; batch lokal navbat/retry bilan yo'qolmaydi |
| Backend → klinik dashboard | WebSocket | Shifokor oynasiga alert, yetim o'lchov va task o'zgarishini darhol yuboradi |
| Backend → tashqi provayderlar | Webhook + idempotency | To'lov/SMS/103 kabi tizimlar qayta yuborishi mumkin; provider_ref bo'yicha duplicate yopiladi |
| Ko'p replica / yuqori yuklama | NATS JetStream yoki Redis Streams | In-memory hub faqat bitta API instance uchun; production scale'da durable consumer group kerak |

### 23.2 Qat'iy qoidalar

- Device yuborgan har bir 5 daqiqalik oynada idempotency kaliti bo'ladi: `device_id + window_start`.
- Device har batchga `batch_id` va ixtiyoriy monotonic `sequence` qo'yadi; server ACK aynan shu qiymatlarni qaytaradi.
- Device tanasida `patient_id` bo'lmaydi; bemor device assignment orqali aniqlanadi.
- Backend ACK to'rt holatni qaytaradi: `accepted`, `duplicate`, `orphaned`, `rejected`.
- Backend ACK `idempotency_key` ham qaytaradi: `device_id + batch_id + sequence`.
- Dashboard real-time xabariga ishonadi, lekin sahifa ochilganda REST snapshot oladi.
- WebSocket xabar yo'qolsa klinik holat yo'qolmaydi; haqiqat manbai Postgres bo'lib qoladi.
- Webhooklar provider transaction id bo'yicha idempotent bo'lishi shart.

### 23.3 Hozirgi implementatsiya

- `GET /api/v1/realtime/status` — realtime transport holati.
- `GET /api/v1/realtime/events?after_id=...` — WebSocket reconnectdan keyin Postgres outbox'dan catch-up.
- `WS /api/v1/realtime/ws?token=...&topic=readings` — klinik xodimlar uchun live event kanali.
- `PipelineService.ingest_batch()` qabul qilingan batchdan keyin `readings`, `reading.accepted`, `reading.orphaned`, `reading.rejected` eventlarini chiqaradi.
- `PipelineService.evaluate_patient()` alert yozilganda `alert.created` eventini chiqaradi.
- `TaskService` vazifa yaratilganda yoki holati o'zgarganda `task.created`, `task.acknowledged`, `task.done`, `task.reassigned` eventlarini chiqaradi.
- `SosService` favqulodda holat lifecycle uchun `sos.raised`, `sos.cancelled`, `sos.acknowledged`, `sos.dispatched`, `sos.resolved` eventlarini chiqaradi.
- Har realtime event `realtime_events` Postgres outbox jadvaliga ham yoziladi.
- WebSocket xabarida outbox `id` bo'ladi; dashboard oxirgi ko'rgan `id`ni saqlaydi va reconnectda `after_id` sifatida yuboradi.
- `REALTIME_TRANSPORT=memory` lokal/dev uchun.
- `REALTIME_TRANSPORT=redis_streams` production uchun; `REDIS_URL` va `REALTIME_STREAM_KEY` talab qilinadi.
- Fanout hub WebSocket subscriberlarni lokal process ichida ushlab turadi.
- Redis stream bridge har API instance'da ishga tushadi: boshqa replica yozgan eventlarni stream'dan o'qib, lokal WebSocket subscriberlarga yetkazadi.
- Stream entry `origin = instance_id` olib yuradi; bridge o'z instance'i yozgan eventni skip qiladi.
- Bridge lokal fanout qilganda eventni stream'ga qayta yozmaydi; aks holda loop yoki duplicate paydo bo'ladi.
- Postgres outbox qayta tiklash va audit uchun qoladi.

## 24. Billing ajratilishi

- `patient_subscriptions` faqat bemor darajasidagi `free`, `premium`, `premium_doc` tariflari uchun ishlatiladi.
- `clinic` tarifi `patient_subscriptions`ga yozilmaydi; klinika/B2B hisob-kitobi `tenant_licences`, `billing_days`, `invoices` orqali yuradi.
- Patient checkout darhol `active` qilmaydi: pullik tarif tanlanganda subscription `past_due`, payment `pending` bo'ladi.
- Payment webhook `provider_ref` bo'yicha idempotent; `patient_subscription_id` bilan kelgan muvaffaqiyatli to'lov subscriptionni `active` qiladi va 30 kunlik `period_end` beradi.
- Safety feature'lar (`critical_alert`, `sos_button`, `status_color`, `vitals`) hech qachon paywall bilan yopilmaydi.

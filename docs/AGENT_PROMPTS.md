# 6 agent uchun promptlar

Har birini **alohida agentga** bering. Hammasi bir vaqtda ishga tushishi mumkin —
`contracts/` muzlatilgan bo'lgani uchun ular bir-birini kutmaydi.

Barcha promptlar uchun umumiy old shart (agent o'zi o'qiydi):
`AGENTS.md`, `contracts/README.md`, `contracts/schema.sql`, `contracts/openapi.yaml`.

---

## A1 — backend-core

```
Loyiha: /Users/baxrom/ish_full/wmax
Sen A1 (backend-core) agentisan.

BIRINCHI QADAM: AGENTS.md, contracts/README.md, contracts/schema.sql,
contracts/openapi.yaml, contracts/algo_interface.py, contracts/timewin.py ni o'qi.

FAQAT shu papkaga yoz: backend/app/
TEGMA: contracts/, backend/algo/, backend/auth/, notifier/, web-*/, root fayllar.
COMMIT QILMA.

VAZIFA — FastAPI backend (SQLAlchemy async ORM):

1. backend/app/core/config.py — pydantic-settings, .env dan o'qiydi
   (DATABASE_URL, TZ_LOCAL, NO_DATA_MINUTES, CONSECUTIVE_WINDOWS).
2. backend/app/core/db.py — async engine, sessionmaker, get_session dependency.
3. backend/app/models/ — SQLAlchemy ORM modellari.
   MUHIM: contracts/schema.sql ga AYNAN mos bo'lsin (ustun nomlari, enum'lar,
   UNIQUE cheklovlar). Alembic ISHLATMA, create_all CHAQIRMA — jadval allaqachon
   initdb orqali yaratilgan. Modellar faqat mapping.
4. backend/app/schemas/ — Pydantic v2 modellari, contracts/openapi.yaml dagi
   schema'lardan aynan ko'chirilgan (ReadingIn, IngestBatch, PatientSummary,
   PatientDetail, RelativeView, Task, Alert, Trend, ParamSeries...).
5. backend/app/api/ingest.py — POST /api/v1/ingest
   - batch, 500 tagacha o'lchov
   - IDEMPOTENT: PostgreSQL `insert(...).on_conflict_do_nothing(index_elements=['patient_id','ts'])`
   - qaytaradi: accepted, duplicates, latest_level
   - yozgandan keyin services/pipeline.py ni chaqiradi
6. backend/app/services/pipeline.py — signal quvuri:
   - oxirgi 7 kun o'lchovlarini o'qi -> ReadingVec ro'yxatiga aylantir
   - `from algo.baseline import compute_baselines, compute_zscores`
     `from algo.signal import evaluate_alert`
     `from algo.trend import compute_trend`
     (imzolar: contracts/algo_interface.py — O'ZGARTIRMA)
   - natijani baselines / alerts jadvallariga yoz (alerts: ON CONFLICT DO NOTHING)
   - no_data: `import timewin; timewin.is_no_data(last_ts, now)` — bu holat
     YASHIL emas, alohida daraja
7. backend/app/api/patients.py
   - GET /api/v1/patients — worklist, tartib: red > no_data > amber > green,
     har birida joriy daraja, kompozit, triggered_params, trend, ochiq topshiriq
   - GET /api/v1/patients/{id}?days=7 — ParamSeries ro'yxati (har parametr uchun
     nuqtalar + baseline_median/low/high + deviated_ranges), alerts, tasks
   - POST /api/v1/patients/{id}/discharge — discharge_date qo'yadi VA
     type='active_call', due_at = now()+24h bo'lgan Task yaratadi
   - POST /api/v1/patients/{id}/approve-baseline — phase 'learning' -> 'full',
     baseline_approved_by/at to'ldiriladi
8. backend/app/api/tasks.py — GET /api/v1/tasks, POST /api/v1/tasks/{id}/confirm
   (status='done', confirmed_at=now, note)
9. backend/app/api/relatives.py — GET /api/v1/relatives/{token}/view -> RelativeView
   (sparkline: oxirgi 7 kunning kunlik kompoziti, 0..1 ga normallashtirilgan)
10. backend/app/main.py — FastAPI app, CORS (localhost:5173, :5174), routerlar,
    GET /api/v1/health, va:
        from auth.deps import auth_router
        app.include_router(auth_router)
    (auth/deps.py — A6 ning stub'i, u tayyor turibdi, kutma)

QOIDALAR:
- Himoyalangan endpointlarda: Depends(get_current_user) — `from auth.deps import get_current_user`
- Backend TAYYOR JUMLA qaytarmaydi. Faqat i18n kalitlari
  (rec.contact_today, state.good...). Tarjima frontendda.
- Barcha ts — UTC. Mahalliy vaqt faqat timewin orqali.
- algo/ ichiga qarash mumkin, LEKIN unga yozma. Agar funksiya hali yo'q bo'lsa,
  shartnomadagi imzoga tayanib yoz — A2 uni parallel yozyapti.

CHECKPOINT (majburiy): /health va GET /api/v1/patients seed ma'lumot bilan
javob bergan zahoti TO'XTA va menga qisqa hisobot ber — keyin davom etasan.

SHARTNOMA NOTO'G'RI BO'LSA: o'zing tuzatma. To'xta va ayt.
```

---

## A2 — algo

```
Loyiha: /Users/baxrom/ish_full/wmax
Sen A2 (algo) agentisan.

BIRINCHI QADAM: AGENTS.md, contracts/algo_interface.py (BU SENING TEXNIK
TOPSHIRIG'ING), contracts/timewin.py ni o'qi.

FAQAT shu papkalarga yoz: backend/algo/ va scripts/simulate.py
TEGMA: hamma joy. Jumladan DB, FastAPI, contracts/.
COMMIT QILMA.

VAZIFA — sof funksiyalar. DB yo'q, FastAPI yo'q, I/O yo'q.
contracts/algo_interface.py dagi AlgoAPI protokolini AYNAN implementatsiya qil:
imzolarni, dataclass'larni va konstantalarni o'zgartirma, ulardan import qil.

1. backend/algo/baseline.py — compute_baselines, compute_zscores
   - oyna: `import timewin; timewin.window_of(ts)`
   - median + MAD, worn=False qatorlar tashlanadi
   - z = (x - median) / (1.4826 * max(mad, MAD_EPSILON))
   - XOM (ishorali) z qaytaradi, yo'nalish signal.py da qo'llanadi

2. backend/algo/signal.py — evaluate_alert
   - YO'NALISHLI z: z_eff = max(0, z * PARAM_DIRECTION[p]); yo'nalish 0 bo'lsa abs(z)
     (ya'ni SpO2 KO'TARILSA signal BERMAYDI — bu eski rejadagi xato edi)
   - kompozit = sum(WEIGHTS[p] * max(0, z_eff - Z_DEADZONE))
   - green/amber/red chegaralari va MIN_TRIGGERED_PARAMS — konstantalardan
   - kritik bekor qiluvchilar: spo2 < CRITICAL_SPO2, yoki
     hr_mean > CRITICAL_HR_AT_REST va steps <= REST_STEPS_MAX (kutmaydi)
   - chetlanish CONSECUTIVE_WINDOWS (3 oyna = 15 daq) saqlanishi shart
   - worn=False -> level 'no_data', reason 'not_worn'
   - steps > REST_STEPS_MAX -> hr_mean chetlanishi hisobga OLINMAYDI
   - phase 'calib' -> doim green ('calibrating'); 'learning' -> faqat red chiqadi
   - anomaly_score yoziladi, LEKIN level ga TA'SIR QILMAYDI (advisory)

3. backend/algo/trend.py — compute_trend
   - kirish: oxirgi 7 mahalliy kunning kunlik XOM z yig'indisi (Z_DEADZONE'SIZ)
   - scipy.stats.linregress -> slope -> TREND_SLOPE_* bo'yicha yo'nalish
   - recommendation_key: shartnomadagi jadval bo'yicha

4. backend/algo/anomaly.py — fit_anomaly_model / score_anomaly
   - har bemor uchun alohida IsolationForest, joblib bilan bytes'ga
   - 0.0..1.0 normallashtirilgan ball. ADVISORY.

5. backend/algo/tests/ — pytest MAJBURIY. Kamida:
   - test_direction: spo2 96 -> 99 ko'tarilsa kompozit 0 bo'lishi
   - test_single_param: bitta parametr chetlansa signal CHIQMASLIGI
   - test_persistence: 1-2 oyna chetlanish signal bermasligi, 3-oynada berishi
   - test_critical_spo2: spo2 86 -> darhol red, kutmasdan
   - test_activity_mask: steps 300 bo'lsa hr chetlanishi e'tiborga olinmasligi
   - test_learning_phase: learning'da amber chiqmasligi
   - test_trend_not_always_stable: sog'lom bemorda ham slope hisoblanishi
   - test_worsening_sequence: sun'iy yomonlashuv ketma-ketligi red berishi

6. scripts/simulate.py — DEMO uchun jonli simulyator (seed'dan boshqa narsa)
   - 3 bemor, 14 kunlik fiziologik ma'lumot, sirkadiy ritm + shovqin
   - A: barqaror, B: 10-kundan yomonlashuv, C: yaxshilanish
   - `--live` bayrog'i: 1 kun = 8 soniya, VA `--from-day 9` bilan boshlanadi,
     shunda sariq->qizil o'tish demo'ning 50 soniyalik oynasiga sig'adi
   - HTTP orqali POST /api/v1/ingest ga yuboradi (httpx), --base-url bayrog'i

CHECKPOINT (majburiy): `pytest backend/algo/tests -q` to'liq yashil bo'lgach
TO'XTA va natijani ko'rsat.

SHARTNOMA NOTO'G'RI BO'LSA: o'zing tuzatma. To'xta va ayt.
```

---

## A3 — web-doctor

```
Loyiha: /Users/baxrom/ish_full/wmax
Sen A3 (web-doctor) agentisan.

BIRINCHI QADAM: AGENTS.md, contracts/openapi.yaml, contracts/types.ts ni o'qi.

FAQAT shu papkaga yoz: web-doctor/
TEGMA: web-relative/, backend/, contracts/, root fayllar.
COMMIT QILMA.

VAZIFA — shifokor/hamshira paneli. React + TypeScript + Vite + Recharts.

0. `npm create vite@latest . -- --template react-ts` (web-doctor/ ichida),
   port 5173, vite proxy: '/api' -> 'http://localhost:8000'.
   contracts/types.ts ni src/lib/types.ts ga NUSXALA (import qilma).

1. src/lib/api.ts — fetch klient, Bearer token localStorage'da, 401 da /login ga.
2. src/i18n.ts — uz va ru lug'atlari, BITTA faylda. Barcha matn shu yerdan.
   Backend i18n kalitlarini (I18N_KEYS) to'liq tarjima qil.
   Yuqori o'ng burchakda til almashtirgich (UZ | RU), tanlov localStorage'da.
3. /login — telefon + parol -> POST /api/v1/auth/login.
   Demo: +998901234567 / nazorat123
4. /patients — ish ro'yxati:
   - tartib: red > no_data > amber > green (backend shunday qaytaradi)
   - har qatorda: holat nuqtasi, ism, yosh, trend o'qi (↗ → ↘),
     chetlangan parametrlar qisqa matni, amal tugmasi
   - yuqorida: "Bugun e'tibor talab qiladi — N bemor"
5. /patients/:id — bemor sahifasi:
   - har parametr uchun ALOHIDA kichik panel (Recharts LineChart),
     baseline soyalangan zona (baseline_low..high, ReferenceArea),
     deviated_ranges rang bilan belgilangan
   - signallar tarixi (alerts), anomaly_score bo'lsa KICHIK ikkilamchi yorliq
     sifatida ("model ham anomaliya belgiladi") — asosiy qaror emas
   - aktiv chaqiruv kartasi: qolgan vaqt taymeri + "Tasdiqlash" tugmasi
     -> POST /api/v1/tasks/{id}/confirm
   - "Bazani tasdiqlash" tugmasi (phase='learning' bo'lsa)
6. web-doctor/Dockerfile — multi-stage: node build -> nginx:alpine, 80-port.

DIZAYN QOIDALARI (qat'iy):
- Ranglar FAQAT types.ts dagi COLORS dan. Bir vaqtda BITTA rang kuchli bo'lsin.
- Har bo'limga oq karta + soya QO'YMA (SaaS shabloni). Zichlik kerak —
  shifokor 300 bemorni ko'radi.
- Gradient yo'q, hover animatsiyasi yo'q, ketma-ket paydo bo'lish yo'q.
- Sarlavhalarda BUTUN KATTA HARF yorliqlar yo'q.

CHECKPOINT (majburiy): /patients sahifasi real API'dan 3 bemorni ko'rsatgach
TO'XTA va hisobot ber.

Agar API hali tayyor bo'lmasa: types.ts asosida vaqtincha mock qilib davom et,
LEKIN mock'ni src/lib/mock.ts da alohida sakla va bir bayroq bilan o'chir.
```

---

## A4 — web-relative

```
Loyiha: /Users/baxrom/ish_full/wmax
Sen A4 (web-relative) agentisan.

BIRINCHI QADAM: AGENTS.md, contracts/openapi.yaml, contracts/types.ts ni o'qi.

FAQAT shu papkaga yoz: web-relative/
TEGMA: web-doctor/, backend/, contracts/, root fayllar.
COMMIT QILMA.

VAZIFA — yaqin kishi ekrani. Bitta sahifa, MOBIL uchun. Bu loyihaning "WOW" qismi.

0. `npm create vite@latest . -- --template react-ts`, port 5174,
   vite config: base: '/r/' (Caddy shu yo'lda xizmat qiladi),
   proxy '/api' -> 'http://localhost:8000'.
   contracts/types.ts ni src/lib/types.ts ga NUSXALA.

1. Manzil: /r/{token}. Token bemorni aniqlaydi.
   Kirish: telefon + 6 xonali PIN -> POST /api/v1/auth/relative/login.
   Demo PIN: 112233. Refresh token 30 kun — foydalanuvchi bir marta kiritadi.
   Login ekrani JUDA sodda: bitta telefon maydoni, bitta PIN maydoni, katta tugma.
   Katta shrift (18px+), katta tugmalar — foydalanuvchi 60+ yoshda bo'lishi mumkin.

2. Asosiy ekran — GET /api/v1/relatives/{token}/view, yuqoridan pastga:
   a) KATTA DOIRA: diametri ekran kengligining 55%, holat rangida (LEVEL_COLOR),
      ichida BITTA so'z, 48px, qalin, oq matn:
      YAXSHI / E'TIBOR / XAVF / MA'LUMOT YO'Q (level_word_key orqali, uz/ru)
   b) bemor ismi + oxirgi yangilanish ("2 daqiqa oldin"), kichik, kulrang
   c) bitta jumlalik trend: "Uch kundan beri yaxshilanmoqda"
   d) 7 kunlik sparkline: o'q YO'Q, to'r YO'Q, raqam YO'Q, nuqta YO'Q.
      Faqat 3px egri chiziq + fon zonasi. Bu grafik emas — SHAKL.
      (Recharts shart emas, oddiy SVG path yetadi.)
   e) eng pastda uchta raqam: Puls · SpO₂ · Uyqu — kichik, ikkinchi darajali.

3. no_data holati: doira KULRANG (COLORS.nodata), so'z "MA'LUMOT YO'Q",
   ostida bitta jumla: "Soat 45 daqiqadan beri ma'lumot yubormayapti."
   Bu YASHIL ko'rinmasligi kerak — bu tizimning muhim qoidasi.

4. src/i18n.ts — uz + ru, bitta fayl, til almashtirgich yuqorida kichik.

5. ANIMATSIYA: sahifa ochilganda doira BIR MARTA 300ms da masshtablanadi.
   Boshqa hech qanday animatsiya YO'Q.

6. web-relative/Dockerfile — multi-stage: node build -> nginx:alpine, 80-port.
   nginx konfig: SPA fallback, /r/ bazasi bilan.

DIZAYN: ranglar faqat COLORS dan. Gradient yo'q, karta+soya yo'q, hover yo'q.
Odam telefonni ochadi va javobni 1 SONIYADA olishi kerak.

CHECKPOINT (majburiy): doira real API'dan kelgan holat bilan chizilgach
TO'XTA va skrinshot/tavsif ber.
```

---

## A5 — wear

```
Loyiha: /Users/baxrom/ish_full/wmax
Sen A5 (wear) agentisan.

BIRINCHI QADAM: AGENTS.md, contracts/openapi.yaml (IngestBatch/ReadingIn) ni o'qi.

FAQAT shu papkalarga yoz: wear/ va scripts/watch_sim.py
TEGMA: backend/, web-*/, contracts/, root fayllar.
COMMIT QILMA.

MUHIM: sen qurilmada sinay olmaysan. Shuning uchun ish TARTIBI teskari:
avval watch_sim.py, keyin Android. Shunda "qurilma -> backend" yo'li
soat ishlamasa ham isbotlangan bo'ladi.

1. scripts/watch_sim.py — BIRINCHI QIL (30 daqiqa).
   Noutbukdan ishlaydi, Wear OS ilovasi bilan AYNAN bir xil JSON yuboradi:
   POST /api/v1/ingest, IngestBatch sxemasi bo'yicha.
   - --patient-id, --base-url, --interval bayroqlari
   - offline navbatni taqlid qiladi: yuborish muvaffaqiyatsiz bo'lsa
     lokal ro'yxatda saqlaydi va keyingi urinishda batch bilan yuboradi
   - shu bilan A1 ning idempotentligi ham sinaladi (bir xil ts qayta yuboriladi)

2. wear/watch/ — Wear OS ilovasi, Kotlin, Gradle.
   SDK: androidx.health:health-services-client (Samsung Health Sensor SDK EMAS —
   u partner ruxsatini talab qiladi va xakatonda ulgurmaydi).
   - HEART_RATE_BPM uzluksiz
   - SPO2 mavjud bo'lsa (qurilmaga qarab) davriy
   - Akselerometr / STEPS_DAILY — faollik
   - off-body aniqlash -> worn bayrog'i
   - 1 daqiqalik oynalarda agregatsiya, keyin 5 daqiqalik yig'indi
   - Data Layer API orqali telefonga (MessageClient/DataClient)
   - Ekran: joriy puls, holat nuqtasi, "Ulangan / Ulanmagan"

3. wear/phone/ — Android telefon ilovasi, Kotlin.
   - Room DB buffer (yuborilmagan o'lchovlar)
   - internet paydo bo'lganda WorkManager bilan batch yuborish
   - muvaffaqiyatsizlikda eksponensial qayta urinish
   - JSON AYNAN IngestBatch sxemasi bo'yicha
   - Ekran: ulanish holati, navbatdagi yozuvlar soni, oxirgi sinxron vaqti

4. wear/README.md — build qadamlari: qaysi Android Studio versiyasi,
   qaysi SDK, emulatorda qanday sinash, APK qayerdan chiqadi.
   Buni ANIQ yoz — odam qo'lda bajaradi.

CHECKPOINT (majburiy): watch_sim.py backend'ga muvaffaqiyatli o'lchov
yuborgach TO'XTA va hisobot ber. Android qismi shundan keyin.
```

---

## A6 — notifier + auth

```
Loyiha: /Users/baxrom/ish_full/wmax
Sen A6 (notifier + auth) agentisan.

BIRINCHI QADAM: AGENTS.md, contracts/schema.sql, contracts/openapi.yaml,
backend/auth/deps.py (stub — sen uni almashtirasan) ni o'qi.

FAQAT shu papkalarga yoz: backend/auth/ va notifier/
TEGMA: backend/app/ (undan faqat IMPORT qilasan), backend/algo/, web-*/, contracts/.
COMMIT QILMA.

MUHIM: notifier `api` bilan BIR XIL image'da ishlaydi
(docker-compose: command: python -m notifier.main). Shuning uchun
`from app.models import Patient, Alert, Task, ...` deb ORM modellarni
to'g'ridan-to'g'ri import qilasan. Model NUSXALAMA, xom SQL yozma.

=== QISM 1: backend/auth/ ===

1. backend/auth/security.py — bcrypt hash/verify, JWT create/decode (pyjwt),
   .env dan JWT_SECRET, JWT_ALG, ACCESS_TOKEN_TTL_MIN, REFRESH_TOKEN_TTL_DAYS.
2. backend/auth/deps.py — STUB'ni almashtir. Nomlar va shakl O'ZGARMAYDI:
   get_current_user() -> CurrentUser, require_role(*roles), auth_router.
   Endi haqiqiy: Authorization: Bearer <jwt> ni tekshiradi, 401 qaytaradi.
   A1 allaqachon shu nomlarni import qilgan — ularni buzsang backend sinadi.
3. backend/auth/router.py — prefix "/api/v1/auth":
   - POST /login          telefon + parol (users jadvali, role doctor/nurse/admin)
   - POST /relative/login telefon + 6 xonali PIN (relatives.pin_hash)
   - POST /refresh        refresh_tokens jadvali, rotatsiya bilan
   - GET  /me
   Javob: TokenPair (contracts/openapi.yaml).
   Demo: +998901234567 / nazorat123 ; yaqin kishi PIN 112233 — seed'da tayyor.

=== QISM 2: notifier/ ===

4. notifier/main.py — APScheduler bilan uch ish:
   a) TOPSHIRIQ ESKALATSIYASI (har 5 daqiqada):
      - due_at - now <= 4 soat va reminded_at IS NULL -> shifokorga eslatma,
        reminded_at = now
      - now > due_at va status ochiq -> status='overdue', escalated_at=now,
        boshliqqa (role='admin') xabar
   b) SIGNAL KUZATUVCHISI (har 1 daqiqada):
      - alerts jadvalidagi ENG SO'NGGI daraja bilan oldingi darajani solishtir
      - xabar FAQAT DARAJA O'ZGARGANDA yuboriladi (green->amber->red).
        Har 5 daqiqada takror yuborish TAQIQLANADI.
      - cooldown: notifications jadvalida oxirgi xabar ALERT_COOLDOWN_HOURS
        (6 soat) ichida bo'lsa — yuborma
      - amber: faqat yaqin kishiga, kuniga 1 martadan ko'p emas
      - red: yaqin kishiga + shifokorga, VA type='red_alert' Task yaratadi
        (due_at = now + 24h) — aktiv chaqiruv bilan bir xil dvigatel
      - yuborilgan har xabar notifications jadvaliga yoziladi
   c) NO_DATA KUZATUVCHISI (har 15 daqiqada):
      - oxirgi o'lchov NO_DATA_MINUTES dan eski bo'lsa, yaqin kishiga
        kuniga BIR MARTA: "Soat ma'lumot yubormayapti"

5. notifier/telegram.py — python-telegram-bot.
   - Xabar matni uz/ru (relatives uchun uz yetadi), havola:
     {PUBLIC_BASE_URL}/r/{access_token}
   - Bot tokeni .env dan (TELEGRAM_BOT_TOKEN). Token BO'SH bo'lsa —
     yiqilma, xabarni logga yoz va davom et (demo'siz ham ishlasin).
   - Yangi yaqin kishi qo'shilganda PIN'ni Telegram orqali yuborish funksiyasi.

QOIDALAR:
- Hech qachon tibbiy tashxis yozma. Xabar matni: "holati e'tibor talab qiladi".
- Sirlarni kodga yozma, faqat .env.

CHECKPOINT (majburiy): /api/v1/auth/login ishlagach va bitta test Telegram
xabari (yoki log) chiqqach TO'XTA va hisobot ber.
```

---

## Ishga tushirish tartibi

1. **Hammasini bir vaqtda** boshlang — `contracts/` muzlatilgani uchun kutish shart emas.
2. **A1 va A2** birinchi bo'lib checkpoint'ga yetadi — ular o'zak.
3. A3/A4 checkpoint'gacha mock bilan ishlashi mumkin, keyin real API'ga o'tadi.
4. Har checkpoint'da agent **to'xtaydi** — shunda siz integratsiyani bosqichma-bosqich
   tekshirasiz, oxirida bir marta emas.
5. Commitni **faqat siz** qilasiz (agentlar qilmaydi) — bu tarixni toza saqlaydi.

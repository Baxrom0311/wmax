# NAZORAT — Arxitektura va Claude Code uchun qurilish rejasi
### Umummilliy AI Xakaton, Xorazm · 17–20 sentabr 2026 · Ma'mun universiteti
**Trek:** Sog'liqni saqlash va farmatsevtika · **Muammolar:** 11 + 12 (+ 10)

---

## 0. Bir gapda

> Kasalxonadan chiqarilgan og'ir bemorga aqlli soat beriladi. Tizim uning shaxsiy normasini o'rganadi, undan chetlanishni kuzatadi, va holat yomonlashganda — kasalxonaga tushishdan kunlar oldin — oilaviy shifokorga "aktiv chaqiruv" topshirig'i, yaqiniga esa xabar yuboradi.

**Uch foydalanuvchi, uch ekran:** yaqin kishi (eng sodda), hamshira (ro'yxat va tashrif), shifokor (qaror va tasdiqlash).

---

## 1. Tizim arxitekturasi

### 1.1 Umumiy sxema

```
┌─────────────────┐
│  Galaxy Watch 5 │  Wear OS ilova
│  (Wear OS app)  │  HR · IBI · PPG · SpO2 · teri harorati
└────────┬────────┘  akselerometr · uyqu
         │ Bluetooth (Data Layer API)
         ▼
┌─────────────────┐
│  Telefon ilova  │  Buffer (Room DB) · offline navbat
│   (Android)     │  ulanish paydo bo'lganda sinxron
└────────┬────────┘
         │ HTTPS (REST)
         ▼
┌──────────────────────────────────────────┐
│              BACKEND (FastAPI)           │
│  ┌────────────┐  ┌──────────────────┐    │
│  │  Ingest    │→ │  Feature qurish  │    │
│  │  API       │  │  (5 daq oyna)    │    │
│  └────────────┘  └────────┬─────────┘    │
│                           ▼              │
│              ┌────────────────────────┐  │
│              │  Shaxsiy bazaviy model │  │
│              │  (z-score og'ish)      │  │
│              └───────────┬────────────┘  │
│                          ▼               │
│              ┌────────────────────────┐  │
│              │  Signal dvigateli      │  │
│              │  yashil/sariq/qizil    │  │
│              └───────────┬────────────┘  │
│                          ▼               │
│              ┌────────────────────────┐  │
│              │  Aktiv chaqiruv (11)   │  │
│              │  24 soat taymer        │  │
│              └────────────────────────┘  │
└──────────┬───────────────┬───────────────┘
           │               │
           ▼               ▼
   ┌──────────────┐  ┌──────────────┐
   │ Yaqin kishi  │  │ Shifokor /   │
   │ (mobil web)  │  │ hamshira     │
   │              │  │ (web panel)  │
   └──────────────┘  └──────────────┘
```

### 1.2 Texnologiya tanlovi (xakaton uchun optimal)

| Qatlam | Texnologiya | Sabab |
|---|---|---|
| Soat | Wear OS (Kotlin) + Samsung Health Sensor SDK | Yagona yo'l; developer rejimida ruxsatsiz ishlaydi |
| Telefon | Android (Kotlin) + Room | Offline buffer |
| Backend | **FastAPI + Postgres + Redis** | Tez, jamoa biladi |
| ML | **scikit-learn / XGBoost + numpy** | CPU'da soniyalarda; CNN shart emas |
| Panel | **React + Recharts** yoki oddiy HTML+Chart.js | Grafiklar tez chiqadi |
| Signal | Telegram bot API | SMS'dan tez va bepul; demoda ishlaydi |

> **Xakaton qoidasi:** Telegram bot — eng tez g'alaba. SMS gateway sozlashga vaqt ketadi, Telegram 20 daqiqada ishlaydi va zalda jonli ko'rsatiladi.

### 1.3 Ma'lumot oqimi

```
Soat (1 Hz HR, IBI) 
  → 1 daqiqalik agregat (telefon)
  → 5 daqiqalik feature vektor (backend)
  → 1 soatlik va 24 soatlik trend
  → z-score (shaxsiy bazaga nisbatan)
  → signal darajasi
```

**Nima yuboriladi (5 daqiqada bir marta, ~200 bayt):**
```json
{
  "patient_id": "uuid",
  "ts": "2026-09-19T14:30:00Z",
  "hr_mean": 78, "hr_min": 71, "hr_max": 94,
  "rmssd": 24.5, "sdnn": 41.2,
  "spo2": 96,
  "skin_temp": 34.8,
  "steps": 112,
  "rr_est": 17.4,
  "worn": true,
  "battery": 63
}
```

---

## 2. Shaxsiy bazaviy model — tizimning yuragi

### 2.1 Nega qat'iy chegara emas

60 yoshli yurak bemori uchun pulse 95 normal bo'lishi mumkin; boshqasi uchun bu qizil signal. Qat'iy chegara ikkalasida ham xato qiladi. LINK-HF tadqiqoti aynan shu sababli shaxsiy bazaviy modeldan foydalangan va 76–88% sezuvchanlik, 85% xoslik, o'rtacha 6.5 kun oldindan ogohlantirish bergan.

### 2.2 Uch bosqichli hayot sikli

| Bosqich | Qachon | Nima qiladi |
|---|---|---|
| **1. Texnik sozlash** | Kasalxonada, 1–2 kun | Soat to'g'ri turibdimi, signal toza keladimi, bemor taqishni o'rgandimi. Baza QURILMAYDI (yotoq rejimi uy rejimi emas). |
| **2. O'rganish rejimi** | Uyda, 5–7 kun | Shaxsiy norma quriladi. Faqat keskin og'ishlarda signal. Mayda chetlanishlar yutiladi. |
| **3. To'liq rejim** | 7-kundan | To'liq signal mantiqi ishlaydi. |

O'rganish tugagach → shifokorga bemorning shaxsiy profili ko'rsatiladi → shifokor **tasdiqlaydi**. Odam halqada qoladi.

### 2.3 Algoritm (soddalashtirilgan, lekin ishlaydigan)

Har bir parametr uchun (HR tinch holatda, RMSSD, SpO2, teri harorati, faollik, uyqu uzilishi, RR):

```python
# O'rganish rejimida
baseline[p] = median(qiymatlar[oxirgi 7 kun, o'sha soat oynasi])
spread[p]   = MAD(qiymatlar)  # median absolute deviation, outlier'ga chidamli

# To'liq rejimda
z[p] = (joriy[p] - baseline[p]) / (1.4826 * spread[p])
```

**Vaqt konteksti muhim:** tungi soat 3 dagi HR bilan kunduzgi HR'ni solishtirmang. Bazani **soat oynasi bo'yicha** qurish (masalan 4 ta oyna: tun 00–06, ertalab 06–12, kunduz 12–18, kech 18–24).

### 2.4 Signal mantiqi — soxta signalga qarshi

Bu eng muhim qism. Bitta parametr chetlansa signal bermang.

```
kompozit_ball = Σ w[p] * max(0, |z[p]| - 1.5)

Darajalar:
  YASHIL  : kompozit < 2.0
  SARIQ   : 2.0 ≤ kompozit < 4.0  VA kamida 2 parametr chetlangan
  QIZIL   : kompozit ≥ 4.0        VA kamida 2 parametr chetlangan
            YOKI bitta parametr kritik zonada (SpO2 < 88, HR > 130 tinch holatda)

Qo'shimcha shartlar:
  - Chetlanish kamida 2 ta ketma-ket oynada saqlanishi kerak (30 daqiqa)
  - Soat taqilmagan bo'lsa → signal yo'q, o'rniga "soatni taqing" eslatmasi
  - Faollik yuqori bo'lsa → HR chetlanishi hisobga olinmaydi
```

Og'irliklar (`w`) boshlang'ich qiymatlari: HR 1.0 · SpO2 1.5 · teri harorati 1.2 · RMSSD 0.8 · uyqu 0.7 · faollik 0.6 · RR 1.3.

### 2.5 Trend va prognoz (foydalanuvchi so'ragan qism)

Har bemor uchun **7 kunlik yo'nalish** hisoblanadi:

```python
# Oxirgi 7 kunning kunlik kompozit balllari bo'yicha chiziqli regressiya
slope = linregress(kunlar, kunlik_kompozit).slope

if slope < -0.15:  yo'nalish = "Yaxshilanmoqda"   ↗ yashil
elif slope > 0.15: yo'nalish = "Yomonlashmoqda"   ↘ qizil
else:              yo'nalish = "Barqaror"         → kulrang
```

Va shifokor uchun bitta aniq tavsiya chiqadi:

| Holat | Tavsiya |
|---|---|
| Yomonlashmoqda + sariq | "3 kun ichida ko'rik tavsiya etiladi" |
| Yomonlashmoqda + qizil | "Bugun bog'laning" |
| Barqaror + yashil | "Reja bo'yicha kuzatuv" |
| Yaxshilanmoqda | "Monitoring davom etsin" |

> **Pitchda ayting:** bu prognoz emas, bu **trend tahlili**. 5 yillik bashorat va'da qilmang.

---

## 3. Aktiv chaqiruv (11-muammo)

Bu qismni to'liq qiling — hujjat aynan shuni so'ragan.

```
Bemor chiqariladi
  → tizim avtomatik "Aktiv chaqiruv" topshirig'ini yaratadi
  → hududiy oilaviy shifokorga yuboriladi
  → 24 soatlik taymer ishga tushadi
  → shifokor bemorni ko'radi va tizimda TASDIQLAYDI
  → tasdiqlanmasa: 20-soatda eslatma, 24-soatda boshliqqa eskalatsiya
```

Holatlar: `yaratildi → yuborildi → ko'rildi → bajarildi` yoki `muddati o'tdi`.

Xuddi shu mexanizm qizil signal paydo bo'lganda ham ishga tushadi — ya'ni bitta topshiriq dvigateli ikki holatga xizmat qiladi.

---

## 4. Dizayn yo'nalishi

### 4.1 Kim qaraydi

| Ekran | Kim | Qanday qaraydi |
|---|---|---|
| Yaqin kishi | 25–45 yosh, telefonda, kuniga 2–3 marta | 5 soniya qaraydi, javob izlaydi: "yaxshimi?" |
| Hamshira | planshet/telefon, uy tashrifida | Ro'yxat, kim birinchi |
| Shifokor | kompyuter, kuniga bir marta | Kim bugun e'tibor talab qiladi |

**Eng muhim qoida:** yaqin kishi o'qimaydi. U **rangga qaraydi**. Raqamlar ikkinchi darajada.

### 4.2 Rang tizimi

Rang bu yerda dekoratsiya emas — u ma'lumot. Shuning uchun palitra qasddan tor:

```
--holat-yaxshi:   #2E7D5B   (to'q yashil, oq matn o'qiladi)
--holat-etibor:   #C77A0A   (amber, sariq emas — sariq ekranda yo'qoladi)
--holat-xavf:     #B3261E   (to'q qizil)
--fon:            #FAFAF8   (juda ochiq, deyarli oq)
--matn:           #1C1B1F
--chiziq:         #D8D6D0
```

Faqat **bitta** rang bir vaqtda kuchli bo'lsin. Ekranda uchta rang birga yonmasin.

### 4.3 Yaqin kishi ekrani — "WOW" shu yerda

Sahifa ochilganda birinchi ko'rinadigan narsa — **katta doira**, ichida bitta so'z:

```
┌───────────────────────────┐
│                           │
│        ╭─────────╮        │
│        │         │        │
│        │  YAXSHI │        │   ← katta doira, holat rangida
│        │         │        │      ichida 1 so'z, 48px
│        ╰─────────╯        │
│                           │
│   Otabek aka · 2 daq oldin│   ← kichik, kulrang
│                           │
│   ↗ Uch kundan beri       │   ← trend, bitta jumla
│     yaxshilanmoqda        │
│                           │
├───────────────────────────┤
│   ╱╲    ╱╲                │
│  ╱  ╲__╱  ╲___            │   ← 7 kunlik chiziq, o'q va raqamsiz
│                           │      faqat shakl ko'rinadi
│   So'nggi 7 kun           │
├───────────────────────────┤
│  Puls 76  ·  SpO₂ 97      │   ← raqamlar eng pastda
│  Uyqu 6s 40d              │
└───────────────────────────┘
```

Nega ishlaydi: odam telefonni ochadi, doiraning rangini ko'radi, javobni **1 soniyada** oladi. Qolgani — xohlasa qaraydi.

**Grafik uchun qoidalar:** o'q belgilarisiz, to'r chiziqlarsiz, faqat egri chiziq va holat zonasi fon rangida. Qalinligi 3px. Nuqtalar yo'q. Bu grafik emas — bu **shakl**.

### 4.4 Shifokor paneli

Bu yerda aksincha — zichlik kerak. Shifokor 300 bemorni ko'radi.

```
┌────────────────────────────────────────────────┐
│ Bugun e'tibor talab qiladi            3 bemor  │
├────────────────────────────────────────────────┤
│ ●  Otabek R.    68y   ↘ yomonlashmoqda         │
│    SpO₂ ↓ 3 kun · HR ↑ tunda    [Bog'lanish]  │
├────────────────────────────────────────────────┤
│ ●  Gulnora M.   72y   ↘ yomonlashmoqda         │
│    Aktiv chaqiruv · 18 soat qoldi  [Tasdiq]   │
├────────────────────────────────────────────────┤
│ ○  Rustam K.    59y   → barqaror               │
└────────────────────────────────────────────────┘
```

Bemor ustiga bosilsa — 7 kunlik ko'p qatorli grafik, har parametr alohida, chetlangan joylar rang bilan belgilangan.

### 4.5 Nimadan qochish

- Har bir bo'limga bir xil oq karta + soyа (SaaS shabloni)
- Barcha sarlavhalarda katta harfli yorliqlar
- Hover animatsiyalari, sahifa yuklanishida ketma-ket paydo bo'lish
- Gradient bezaklar
- Uchta rangni birga yoqish

Bitta joyda jasur bo'ling: **katta doira**. Qolgani jim tursin.

---

## 5. Claude Code uchun qurilish rejasi

> Har bir vazifani alohida prompt sifatida bering. Ketma-ketlikni buzmang — keyingisi oldingisiga tayanadi.

### Vazifa 1 — Backend skeleti (60 daq)

```
FastAPI loyihasi yarat. Postgres (SQLAlchemy async) va Alembic.
Modellar:
- Patient(id, fio, yosh, tashxis, discharge_date, phase[calib/learning/full], doctor_id, nurse_id)
- Relative(id, patient_id, fio, telegram_chat_id)
- Reading(id, patient_id, ts, hr_mean, hr_min, hr_max, rmssd, sdnn, spo2, skin_temp, steps, rr_est, worn, battery)
- Baseline(id, patient_id, param, time_window[0-3], median, mad, updated_at)
- Alert(id, patient_id, ts, level[green/amber/red], composite_score, triggered_params JSON, status)
- Task(id, patient_id, doctor_id, type[active_call], created_at, due_at, status, confirmed_at, note)

Endpointlar:
POST /api/v1/ingest            - o'lchovlar (batch, ro'yxat qabul qilsin)
GET  /api/v1/patients          - ro'yxat + joriy holat + trend
GET  /api/v1/patients/{id}     - 7 kunlik ma'lumot, baseline, signallar
POST /api/v1/patients/{id}/discharge - aktiv chaqiruv yaratadi
POST /api/v1/tasks/{id}/confirm - shifokor tasdiqlaydi
GET  /api/v1/relatives/{token} - yaqin kishi uchun public ko'rinish

Docker Compose: api + postgres. Seed skript: 3 ta bemor, Xorazm tumanlari
(Urganch, Xiva, Xonqa, Shovot), o'zbekcha ismlar.
```

### Vazifa 2 — Bazaviy model va signal dvigateli (90 daq)

```
app/services/baseline.py yoz:

1. compute_baseline(patient_id): oxirgi 7 kun o'lchovlaridan har parametr va
   har vaqt oynasi (0=tun 00-06, 1=ertalab 06-12, 2=kunduz 12-18, 3=kech 18-24)
   uchun median va MAD hisoblasin, Baseline jadvaliga yozsin.

2. compute_zscores(patient_id, reading): joriy o'lchovni mos vaqt oynasidagi
   baseline bilan solishtirib z = (x - median) / (1.4826 * MAD) qaytarsin.
   MAD == 0 bo'lsa kichik epsilon ishlatsin.

3. evaluate_alert(patient_id, reading):
   - kompozit = sum(w[p] * max(0, abs(z[p]) - 1.5))
   - og'irliklar: hr 1.0, spo2 1.5, skin_temp 1.2, rmssd 0.8, sleep 0.7,
     activity 0.6, rr 1.3
   - YASHIL: kompozit < 2.0
   - SARIQ: 2.0 <= kompozit < 4.0 VA >= 2 parametr chetlangan
   - QIZIL: kompozit >= 4.0 VA >= 2 parametr chetlangan, YOKI spo2 < 88,
     YOKI tinch holatda hr > 130
   - shart: chetlanish 2 ketma-ket oynada saqlansin
   - worn == false bo'lsa signal chiqarma
   - steps yuqori bo'lsa hr chetlanishini hisobga olma
   - phase == 'learning' bo'lsa faqat QIZIL chiqsin

4. compute_trend(patient_id): oxirgi 7 kunning kunlik o'rtacha kompozit
   balli bo'yicha scipy.stats.linregress. slope < -0.15 "Yaxshilanmoqda",
   > 0.15 "Yomonlashmoqda", aks holda "Barqaror".
   Shifokor uchun tavsiya matnini ham qaytarsin.

Pytest testlari yoz: sun'iy yomonlashuv ketma-ketligi kiritilganda tizim
qizil signal berishini tekshirsin.
```

### Vazifa 3 — Simulyator (45 daq) — **demo shu bilan tirik bo'ladi**

```
scripts/simulate.py yoz.

Uchta bemor uchun 14 kunlik realistik fiziologik ma'lumot generatsiya qilsin:
- sirkadiy ritm (tunda HR past, kunduzi yuqori)
- tasodifiy shovqin
- bemor A: barqaror
- bemor B: 10-kundan boshlab sekin yomonlashish (HR bazadan +12%,
  SpO2 -3%, teri harorati +0.6, RMSSD -30%, uyqu uzilishi ortadi)
- bemor C: yaxshilanish

--live bayrog'i bilan: ma'lumotni real vaqtda /api/v1/ingest ga
tezlashtirilgan tarzda yuborsin (1 kun = 20 soniya), shunda sahnada
grafik ko'z oldida o'zgaradi va qizil signal jonli chiqadi.
```

### Vazifa 4 — Shifokor/hamshira paneli (90 daq)

```
React + Vite + Recharts. Sahifalar:
- /patients : bemorlar ro'yxati, avval e'tibor talab qiladiganlar.
  Har qatorda: status nuqtasi, ism, yosh, trend o'qi, chetlangan
  parametrlar qisqa matni, amal tugmasi.
- /patients/:id : 7 kunlik ko'p qatorli grafik (har parametr alohida panel,
  baseline soyalangan zona sifatida, chetlangan joylar rang bilan),
  signallar tarixi, aktiv chaqiruv kartasi va "Tasdiqlash" tugmasi.
- Rang tokenlari: --holat-yaxshi #2E7D5B, --holat-etibor #C77A0A,
  --holat-xavf #B3261E, --fon #FAFAF8, --matn #1C1B1F, --chiziq #D8D6D0
- Interfeys tili: o'zbek.
Karta/soya shablonidan qoch. Bitta rang bir vaqtda kuchli bo'lsin.
```

### Vazifa 5 — Yaqin kishi ekrani (60 daq) — **WOW shu yerda**

```
Bitta sahifa, mobil uchun. /r/{token} manzilida, login talab qilmaydi.

Tepada: katta doira (diametri ekran kengligining 55%), ichida bitta so'z —
YAXSHI / E'TIBOR / XAVF — holat rangida, 48px, qalin.
Ostida: bemor ismi va oxirgi yangilanish vaqti, kichik kulrang matnda.
Ostida: bitta jumlalik trend — "Uch kundan beri yaxshilanmoqda".

O'rtada: 7 kunlik sparkline. O'q yo'q, to'r yo'q, raqam yo'q, nuqta yo'q.
Faqat 3px egri chiziq va fon zonasi. Grafik emas — shakl.

Pastda: uchta raqam — Puls, SpO₂, Uyqu. Kichik, ikkinchi darajali.

Animatsiya: sahifa ochilganda doira bir marta 300ms da masshtablanadi.
Boshqa animatsiya yo'q.
```

### Vazifa 6 — Wear OS ilova (90 daq, parallel)

```
Wear OS ilova (Kotlin). Samsung Health Sensor SDK bilan:
- HeartRateTracker (uzluksiz, IBI bilan)
- SpO2Tracker (har 10 daqiqada on-demand)
- SkinTemperatureTracker (uzluksiz)
- Akselerometr (qadam va faollik uchun)
Ma'lumotni 1 daqiqalik oynalarda agregatsiya qilsin.
Off-body sensor bilan taqilganini aniqlasin (worn bayrog'i).
Data Layer API orqali telefonga yuborsin.
Ekranda: joriy pulse, holat nuqtasi, "Ulangan / Ulanmagan".

Telefon ilovasi: Room DB'da buffer, internet paydo bo'lganda
/api/v1/ingest ga batch yuborish, muvaffaqiyatsizlikda qayta urinish.
```

### Vazifa 7 — Telegram signal (30 daq)

```
Signal QIZIL bo'lganda:
- yaqin kishiga: "Otabek akaning holati e'tibor talab qiladi.
  Batafsil: <havola>"
- shifokorga: aktiv chaqiruv topshirig'i + havola
SARIQ bo'lganda faqat yaqin kishiga, kuniga bir martadan ko'p emas.
python-telegram-bot ishlatilsin. Bot tokeni .env dan.
```

### Vazifa 8 — Oxirgi (agar vaqt qolsa)

```
- Nafas olish tezligini PPG'dan baholash (tinch holatda)
- Yiqilishni akselerometrdan aniqlash
- Offline rejim ko'rsatkichi va sinxronlash holati
```

---

## 6. Vaqt jadvali (qolgan ~2 kun)

| Vaqt | Ish | Checkpoint |
|---|---|---|
| **18-sent ertalab** | Vazifa 1 + 6 parallel | Backend ishlaydi, soatdan birinchi pulse keladi |
| **18-sent 14:00** | **CHEKPOINT 1** — ingest + soat ko'rsatiladi | |
| 18-sent kunduz | Vazifa 2 + 3 | Simulyator qizil signal chiqaradi |
| 18-sent kech | Vazifa 4 | Shifokor paneli ishlaydi |
| **19-sent ertalab** | Vazifa 5 + 7 | Yaqin ekrani va Telegram |
| **19-sent 14:00** | **CHEKPOINT 2** | |
| 19-sent 14:00–17:00 | Demo silliqlash, offline sinov | |
| **19-sent 17:00** | **BUILD MUZLATILADI** | |
| **19-sent 18:00** | ⛔ **LOYIHA TOPSHIRILADI** | |
| 19-sent 19:30–21:00 | Video | |
| **19-sent 21:00** | ⛔ **VIDEO TOPSHIRILADI** | |
| 20-sent 09:30 | Pitch mashqi (3 marta) | |

---

## 7. Demo ssenariysi (3 daqiqa)

| Vaqt | Nima ko'rsatiladi |
|---|---|
| 0:00–0:20 | Soat qo'lda. Ilovada jonli pulse. "Bu haqiqiy, hozir." |
| 0:20–0:40 | Shifokor paneli. "Otabek aka kecha chiqarildi." → Aktiv chaqiruv paydo bo'ladi, 24 soat taymer. |
| 0:40–1:30 | Simulyator `--live`. Grafik ko'z oldida o'zgaradi. Yashil → sariq → **qizil**. |
| 1:30–1:50 | Telefonda Telegram xabari keladi. Yaqin kishi ekrani ochiladi — katta qizil doira. |
| 1:50–2:10 | Shifokor "Tasdiqlash" bosadi. Topshiriq yopiladi. |
| 2:10–3:00 | Metrikalar va halollik slaydi. |

**Zaxira:** hamma narsani oldindan video qilib qo'ying. Wi-Fi yiqilsa — darhol videoga o'ting, uzr so'ramang.

---

## 8. Halollik slaydi (majburiy)

Bu slayd sizni shifokor-hakamdan himoya qiladi va kuchli ko'rsatadi.

**Biz o'lchamaymiz:**

| Parametr | Nega | Biz nima qilamiz |
|---|---|---|
| Qonda qand | FDA 2024-yilda soatlardan qand o'lchashga qarshi ogohlantirgan | Diabetli bemorda HRV va uyqu og'ishini kuzatamiz |
| Qon bosimi | Kalibrsiz model populyatsiya o'rtachasiga regressiya qiladi; Samsung o'zi 28 kunlik kaff kalibratsiyasini talab qiladi | Bosimni da'vo qilmaymiz |
| Nafas soni harakatda | Bilak PPG harakatda ishonchsiz | Faqat tinch/uyqu holatida |
| Ong darajasi | Soatdan o'lchab bo'lmaydi | Harakatsizlik va taqilmaganlikni proksi sifatida |

**Bir jumla:** *"Biz tashxis qo'ymaymiz. Biz shaxsiy normadan og'ishni aniqlab, shifokorni tekshirishga undaymiz."*

---

## 9. Metrikalar slaydi

- **Ilmiy asos:** LINK-HF — shaxsiy bazaviy model bilan HF gospitalizatsiyasi 76–88% sezuvchanlik, 85% xoslik, mediana 6.5 kun oldin (Circulation: Heart Failure 2020).
- **Bizning tizim:** simulyatsiya qilingan yomonlashuv ssenariysida qizil signal necha soat oldin chiqdi.
- **Soxta signal nazorati:** barqaror bemorda 14 kun davomida nechta noto'g'ri signal (maqsad: 0–1).
- **Signal qamrovi:** soat taqilgan vaqt ulushi.
- **Kechikish:** o'lchovdan signalgacha vaqt.

---

## 10. Xavflar

| Xavf | Zaxira reja |
|---|---|
| Samsung SDK developer rejimi ishlamaydi | Wear OS Health Services API (oddiyroq HR) |
| Soat batareyasi demo paytida tugaydi | Zaryadlagich yoningizda, demo oldidan 100% |
| Wi-Fi yiqiladi | Hammasi localhost'da ishlasin + zaxira video |
| Simulyator va real oqim to'qnashadi | Ikki alohida bemor: biri real soat, biri simulyator |
| Ulgurmaslik | Vazifa 6 (soat) tushib qolsa ham tizim simulyator bilan to'liq ishlaydi |

---

*Reja xakaton davomida o'zgarishi mumkin. Vazifa 1, 2, 3 — majburiy o'zak. Qolganlari vaqtga qarab.*

# A2: algo — Bajarish Rejasi (PLAN.md)

Papka: `backend/algo/` va `scripts/simulate.py`  
Mas'ul: **A2 agenti**  
Chegaralar: Faqat `backend/algo/` va `scripts/simulate.py`. DB, FastAPI, contracts/ ga mutlaqo tegmaydi!

---

## 1. Asosiy Vazifa
Klinik tahlil yadrosi — sof matematik va statistik funksiyalarni implementatsiya qilish. Hech qanday I/O, ma'lumotlar bazasi yoki tarmoq so'rovlari bo'lmaydi. Barcha funksiyalar `contracts/algo_interface.py` dagi `AlgoAPI` protokoliga qat'iy mos keladi.

---

## 2. Fayllar Tuzilmasi va Qadamlar

### 2.1 Bazaviy Model va Z-score (`backend/algo/baseline.py`)
- [ ] `compute_baselines(readings: list[ReadingVec]) -> list[BaselineEntry]`:
  - `worn == False` bo'lgan yozuvlarni chiqarib tashlash.
  - Har bir yozuv uchun `timewin.window_of(ts)` orqali mahalliy vaqt oynasini (0..3) aniqlash.
  - Har bir `(param, time_window)` kesimida:
    - `median` hisoblash.
    - `mad = median(|x - median|)` (Median Absolute Deviation).
    - `n_samples` sonini qayd etish.
- [ ] `compute_zscores(reading: ReadingVec, baselines: list[BaselineEntry]) -> dict[str, float]`:
  - O'lchovning vaqt oynasidagi bazani topish.
  - Xom ishorali z-score:
    $$z = \frac{x - \text{median}}{1.4826 \cdot \max(\text{mad}, \text{MAD\_EPSILON})}$$
  - Faqat mavjud parametrlar uchun dict qaytarish.

### 2.2 Signal Baholash Dvigateli (`backend/algo/signal.py`)
- [ ] `evaluate_alert(reading, baselines, recent_zscores, phase, anomaly_score) -> AlertResult`:
  - Agar `worn == False` bo'lsa: `level = 'no_data'`, `reason = 'not_worn'`.
  - **Yo'nalishli Z-score:**
    $$z_{\text{eff}} = \begin{cases} \max(0, z \cdot \text{PARAM\_DIRECTION}[p]), & \text{agar } \text{PARAM\_DIRECTION}[p] \neq 0 \\ |z|, & \text{agar } 0 \end{cases}$$
    *(SpO2 faqat tushganda, HR faqat ko'tarilganda og'ish deb olinadi)*.
  - **Faollik filtri:** Agar `reading.steps > REST_STEPS_MAX (20)` bo'lsa, `hr_mean` z-score inobatga olinmaydi.
  - **Kompozit ball:**
    $$\text{composite} = \sum_{p} \text{WEIGHTS}[p] \cdot \max(0, z_{\text{eff}}[p] - \text{Z\_DEADZONE})$$
  - **Kritik istisnolar (darhol qizil, kutmaydi):**
    - $SpO_2 < \text{CRITICAL\_SPO2} (88.0)$
    - $HR_{\text{mean}} > \text{CRITICAL\_HR\_AT\_REST} (130.0)$ va $\text{steps} \le \text{REST\_STEPS\_MAX} (20)$.
  - **Persitentlik qoidasi:** Chetlanish ketma-ket `CONSECUTIVE_WINDOWS` (3 oyna = 15 daqiqa) davomida saqlanishi shart. Buning uchun `recent_zscores` tekshiriladi.
  - **Fazalar filtri:**
    - `phase == 'calib'` bo'lsa: doim `'green'`, `reason = 'calibrating'`.
    - `phase == 'learning'` bo'lsa: faqat `'red'` chiqishi mumkin (amber chiqmaydi, `'green'` ga tushadi).
    - `phase == 'full'`: odatiy kompozit qoidalari.
  - `anomaly_score`: natijaga yoziladi, lekin `level` ga mutlaqo TA'SIR QILMAYDI (advisory).

### 2.3 Trend Tahlili (`backend/algo/trend.py`)
- [ ] `compute_trend(daily_raw_scores: list[tuple[int, float]]) -> TrendResult`:
  - Oxirgi 7 mahalliy kunning kunlik xom z-score yig'indisi asosida `scipy.stats.linregress` orqali slope hisoblash.
  - Qiyalik bo'yicha:
    - `slope < TREND_SLOPE_IMPROVING (-0.15)` -> `'improving'`.
    - `slope > TREND_SLOPE_WORSENING (+0.15)` -> `'worsening'`.
    - oraliqda bo'lsa -> `'stable'`.
  - Tavsiya kalitlari (`contracts/types.ts` I18N_KEYS bo'yicha).

### 2.4 Anomaliya Modeli (`backend/algo/anomaly.py`)
- [ ] `fit_anomaly_model(readings: list[ReadingVec]) -> bytes`: `IsolationForest` ni fit qilib `joblib.dumps` orqali baytga o'girish.
- [ ] `score_anomaly(model_blob: bytes, reading: ReadingVec) -> float`: 0.0..1.0 oraliqdagi normallashtirilgan anomaliya bali.

### 2.5 Pytest To'plami (`backend/algo/tests/`)
- [ ] `test_direction`: SpO2 96 dan 99 ga ko'tarilsa kompozit 0 bo'lishi.
- [ ] `test_single_param`: Faqat bitta parametr oshganda kamida 2 ta parametr sharti tufayli signal chiqmasligi.
- [ ] `test_persistence`: 1-2 oynada signal chiqmasligi, faqat 3-oynada amber/red chiqishi.
- [ ] `test_critical_spo2`: SpO2 86 bo'lganda kutmasdan darhol red berishi.
- [ ] `test_activity_mask`: steps=300 bo'lganda puls 135 ga chiqsa ham qizil bo'lmasligi.
- [ ] `test_learning_phase`: learning fazasida faqat red chiqishi, amber esa green bo'lib qolishi.
- [ ] `test_trend_not_always_stable`: sog'lom bemorda ham qiyalik hisoblanishi.
- [ ] `test_worsening_sequence`: sun'iy yomonlashuv ketma-ketligi red berishi.

### 2.6 Jonli Demo Simulyatori (`scripts/simulate.py`)
- [ ] 3 bemor profili: A (sog'lom), B (10-kundan yurak yetishmovchiligi boshlanadi), C (tuzalayotgan).
- [ ] `--live` va `--from-day 9` bayroqlari: demo rejimida har 8 soniyada 1 kunlik o'lchov yuborilib, 50 soniya ichida yashil -> sariq -> qizil o'tishini ko'rsatish.

---

## 3. Majburiy Checkpoint
`pytest backend/algo/tests -q` to'liq yashil (100% pass) bo'lgach to'xtab hisobot berish.

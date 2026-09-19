# A4: web-relative — Bajarish Rejasi (PLAN.md) — 100% PRO WOW QAROVCHI PORTALI

Papka: `web-relative/`  
Mas'ul: **A4 agenti**  
Chegaralar: Faqat `web-relative/`. Boshqa papkalarga tegilmaydi.

---

## 1. Konsepsiya va Maqsad

Bemorning yaqini / qarovchisi uchun **Apple Health / Oura Ring** darajasidagi zamonaviy, tushunarli, chuqur tahliliy va 100% "PRO WOW" sog'liqni saqlash portali.
Qarovchi bir yoki bir nechta bemorning (masalan, otasi va onasi) holatini bitta kabinetdan kuzatadi, AI erta ogohlantirish prognozlarini ko'radi, muammolarning tub sabablarini inson tilida tushunadi va shaxsiy normativ koridorli interaktiv grafiklar bilan dinamikani tahlil qila oladi.

---

## 2. Texnologik Stek va UI Arxitekturasi

- **Framework:** React 18, TypeScript, Vite (Port: 5174, `base: '/r/'`, proxy `/api` -> `http://localhost:8000`).
- **Grafik va Vizualizatsiya:** Recharts (`ResponsiveContainer`, `LineChart`, `ReferenceArea`, `Tooltip`, `Area`) + Maxsus SVG animatsiyalangan xavf o'lchagich (Health Gauge & Circle).
- **Icons & Styling:** Lucide-react (yoki toza Tailwind/CSS modules).
- **Dizayn tizimi:** `contracts/types.ts` dagi `COLORS` va `LEVEL_COLOR`:
  - `good` (#2E7D5B) — Barqaror, me'yorida.
  - `attention` (#C77A0A) — Diqqat, erta ehtiyot choralari.
  - `risk` (#B3261E) — Yuqori xavf, darhol chora.
  - `nodata` (#8A8780) — Ma'lumot uzatilmayapti.
- **Ekran moslashuvchanligi:** 100% Responsive — Mobil telefonda qulay boshqaruv, planshet va noutbukda kengaytirilgan tahliliy dashboard.
- **Tillar:** `src/i18n.ts` (O'zbekcha va Ruscha to'liq tarjima, til almashtirgich).

---

## 3. Sahifalar va Ekran Tuzilishi

### 3.1 Kirish Ekrani (`/r/login` yoki `/r/:token`)
- **Telefon raqam** + **6 xonali PIN kod** (`112233` demo).
- Katta, qulay sensor klaviatura elementlari.
- Muvaffaqiyatli kirishda:
  - Token saqlanadi (30 kunlik refresh token).
  - Qarovchiga biriktirilgan barcha bemorlar ro'yxati olinadi (`RelativePatientItem[]`).
  - Agar token URL orqali kelgan bo'lsa (`/r/:token`), to'g'ridan-to'g'ri o'sha bemor ochiladi.

---

### 3.2 Boshqaruv Markazi (Dashboard) Strukturasi

```
┌─────────────────────────────────────────────────────────────┐
│ [LOGO] WMAX Qarovchi Portali       [UZ | RU]  [Chiqish]  │
├─────────────────────────────────────────────────────────────┤
│ 1. KO'P BEMORLIK SWITCHER (Multi-Patient Switcher Card)     │
│    [ Otam: Olim aka (Diqqat) ]  [ Onam: Salomat opa (Yaxshi) ]│
├─────────────────────────────────────────────────────────────┤
│ 2. HOLAT MARKAZI & AI PROGNOZ HUB                           │
│  ┌─────────────────────────┐ ┌───────────────────────────┐  │
│  │   Dinamik Holat Doirasi │ │  AI 72-soatlik Prognozi   │  │
│  │     [ E'TIBOR TALAB ]   │ │  "Dekommutatsiya xavfi:   │  │
│  │    Kompozit og'ish: 2.8 │ │   O'rta (65%). Oxirgi     │  │
│  │   Oxirgi yangilanish:   │ │   48 soatda SpO2 va puls  │  │
│  │      2 daqiqa oldin     │ │   salbiy tendensiyada."   │  │
│  └─────────────────────────┘ └───────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ 3. ANIQLANGAN MUAMMOLAR TAHLILI (Root-Cause Breakdown)      │
│  • SpO2 (Kislorod) pasaygan: 92% (Shaxsiy me'yor: 96-98%)   │
│  • Tungi puls ko'tarilgan: 88 bpm (Shaxsiy me'yor: 65-72 bpm)│
│  • Teri harorati: 37.2°C (Barqaror)                          │
├─────────────────────────────────────────────────────────────┤
│ 4. INTERAKTIV PARAMETR DINAMIKASI (Baseline Corridors)      │
│    Vaqt filtri: [ 24 soat ] [ 3 kun ] [ 7 kun ]             │
│    Tablar: [Puls] [SpO2] [HRV/Stress] [Harorat] [Uyqu] [Faollik]
│    ┌──────────────────────────────────────────────────────┐  │
│    │ Recharts LineChart:                                  │  │
│    │ - Yashil soyali zona: Shaxsiy me'yor (Baseline Low..High)│
│    │ - Haqiqiy o'lchov chizig'i va nuqtalari             │  │
│    │ - Qizil/Sariq og'ish zonalari                        │  │
│    └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ 5. SHIFO KOR TAVSIYALARI & TEZKOR HARAKATLAR               │
│  [ Qo'ng'iroq: Dr. Abdullayev ] [ Telegram ] [ Tez yordam 103 ]│
│  Tavsiya: "Bugun bemor tinch yotishi va dori ichishi zarur" │
│  Aktiv chaqiruv holati: "Shifokor ko'rigi rejalashtirilgan" │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Qadamma-qadam Bajarish Bosqichlari

### 1-qadam: Loyiha va Tiplarni Sinxronlash
- [ ] Vite React-TS skaffoldini tayyorlash (`base: '/r/'`, port 5174).
- [ ] `contracts/types.ts` ni `src/lib/types.ts` ga to'liq nusxalash (yangi `ProblemItem`, `PrognosisInfo`, `RelativePatientItem`, `RelativeLoginResponse`, `RelativeView` bilan).
- [ ] `vite.config.ts` da proxy sozlash: `/api` -> `http://localhost:8000`.

### 2-qadam: API Klient va Autentifikatsiya
- [ ] `src/lib/api.ts`:
  - `loginRelative(phone, pin)` -> `RelativeLoginResponse` (token va bemorlar ro'yxati).
  - `getRelativeView(token)` -> `RelativeView` (to'liq tahliliy ma'lumotlar).
  - Tokenni va tanlangan bemor `token`ini `localStorage`da saqlash.

### 3-qadam: Xalqaro Tarjima (i18n)
- [ ] `src/i18n.ts`:
  - O'zbekcha va Ruscha barcha atamalar, tibbiy ko'rsatkich nomlari, tushuntirishlar, holatlar va tavsiyalar.

### 4-qadam: Bemorlar Switcher Komponenti (`PatientSwitcher.tsx`)
- [ ] Agar qarovchiga 2+ bemor biriktirilgan bo'lsa, tepada zamonaviy gorizontal kartochkalar:
  - Bemor ismi, qarindoshligi ("Otam", "Onam"), yoshi, holat rangi nishoni (badge).
  - Bosilganda faol bemor almashadi va ma'lumotlar yangilanadi.

### 5-qadam: Holat Markazi va AI Prognoz Hub (`HeroStatusPrognosis.tsx`)
- [ ] **Animatsiyalangan Holat Doirasi / Gauge:**
  - Yashil / Sariq / Qizil / Kulrang fon.
  - Markazda 32-40px qalin holat so'zi: `YAXSHI` / `E'TIBOR TALAB` / `XAVF` / `MA'LUMOT YO'Q`.
  - Kompozit og'ish bali ko'rsatkichi (masalan: `Z = 2.8`).
- [ ] **AI 72-soatlik Erta Ogohlantirish Prognozi Kartasi:**
  - Xavf darajasi: Past, O'rta, Yuqori.
  - Dekommutatsiya ehtimolligi foizda (`65%`).
  - Tushunarli klinik tahlil xulosasi.

### 6-qadam: Muammolar Tahlili Kartalari (`ProblemBreakdown.tsx`)
- [ ] `problems: ProblemItem[]` ro'yxatini vizual kartalar sifatida chiqarish:
  - Parametr belgisi (masalan: O₂ kislorod, Yurak urishi, Harorat).
  - Og'ish darajasi va yo'nalishi (masalan, "SpO2 -4% me'yordan past").
  - Haqiqiy qiymat va shaxsiy norma koridori taqqoslanishi.
  - Qisqa insoniy izoh: *"Bemorning kislorod darajasi odatdagidan pastroq, chuqur nafas mashqlari tavsiya etiladi."*

### 7-qadam: Shaxsiy Norma Koridorli Interaktiv Grafiklar (`InteractiveMetrics.tsx`)
- [ ] Vaqt filtri: Bugun (24s), 3 kun, 7 kun.
- [ ] Ko'rsatkichlar tablari: Puls, SpO2, HRV, Teri harorati, Nafas tezligi, Uyqu, Faollik.
- [ ] Recharts `LineChart`:
  - `ReferenceArea` orqali `baseline_low` dan `baseline_high` gacha bo'lgan oraliqni yashil/kulrang mayin fon bilan soyalash.
  - Haqiqiy o'lchovlar nuqtalari (`points`).
  - Og'ish yuz bergan davrlar (`deviated_ranges`) maxsus rangli chiziq bilan yoritiladi.
  - Tooltip: vaqt, ko'rsatkich qiymati va norma bilan farqi.

### 8-qadam: Tezkor Harakatlar va Shifokor bilan Aloqa (`ActionContactBar.tsx`)
- [ ] Biriktirilgan shifokor kartasi (Ismi, mutaxassisligi, telefoni).
- [ ] Bir tugma bilan qo'ng'iroq qilish (`tel:...`) va Telegram havolasi.
- [ ] Favqulodda "103 Tez yordam" tugmasi.
- [ ] Shifokor tayinlagan "Aktiv chaqiruv" vazifasining holati va taymeri.

### 9-qadam: no_data Rejimi Himoyasi
- [ ] Agar oxirgi o'lchov 45 daqiqadan oshgan bo'lsa:
  - Holat doirasi KULRANG bo'ladi.
  - Sarlavha: `MA'LUMOT YO'Q`.
  - Tushuntirish: *"Aqlli soat 45 daqiqadan beri ma'lumot uzatmayapti. Soat yechilgan yoki zaryadi tugagan bo'lishi mumkin."*
  - **Hech qachon ma'lumot yo'q holatda yashil ko'rinmaydi!**

### 10-qadam: Dockerfile va Build
- [ ] `web-relative/Dockerfile`: Multi-stage build (Node -> Nginx Alpine), `/r/` bazasi bilan SPA konfiguratsiyasi.

---

## 5. Majburiy Checkpoint
Multi-patient switcher, AI prognoz kartasi va shaxsiy koridorli interaktiv Recharts grafiklari real API (yoki types.ts mock) ma'lumotlari bilan to'liq ekranda chizilgach to'xtab hisobot berish.

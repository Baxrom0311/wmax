# A3: web-doctor — Bajarish Rejasi (PLAN.md) — 100% PRO KLINIK WORKSTATION

Papka: `web-doctor/`  
Mas'ul: **A3 agenti**  
Chegaralar: Faqat `web-doctor/`. `web-relative/`, `backend/`, `contracts/` ga tegilmaydi.

---

## 1. Konsepsiya va Maqsad

Oilaviy shifokor va patronaj hamshiralar uchun pas zichlikdagi, aniq, professional klinik boshqaruv stoli (Clinical Workstation).
Shifokor 100-300 bemor orasidan aynan bugun kimga birinchi navbatda e'tibor qaratish kerakligini 3 soniyada tushunadi. 24 soatlik aktiv chaqiruvlarni boshqaradi, 7 kunlik ko'p parametrli koridorlarni tahlil qiladi va shaxsiy normativ bazani tasdiqlaydi (`Human-in-the-loop`).

---

## 2. Texnologik Stek va Arxitektura

- **Framework:** React 18, TypeScript, Vite (Port: 5173, proxy `/api` -> `http://localhost:8000`).
- **Grafiklar:** Recharts (`LineChart`, `ReferenceArea`, `ResponsiveContainer`, `Tooltip`, `Brush`).
- **Dizayn tamoyili:** Klinik zichlik — ortiqcha gradientlar, ulkan bo'shliqlar va samarasiz SaaS animatsiyalarisiz. Faqat kerakli tibbiy ma'lumotlar, aniq rangli statuslar.
- **Dizayn tokenlari:** Faqat `contracts/types.ts` dagi `COLORS` va `LEVEL_COLOR`.
- **Tillar:** `src/i18n.ts` (O'zbekcha va Ruscha).

---

## 3. Sahifalar va Funksional Bloklar

### 3.1 Kirish Ekrani (`/login`)
- Shifokor va hamshira kirishi: Telefon (`+998901234567`) + Parol (`wmax123`).
- `POST /api/v1/auth/login` orqali JWT token olib, `localStorage` ga saqlash.

---

### 3.2 Bosh Sahifa: Klinik Ish Ro'yxati (`/patients`)
- **Yuqori xulosa paneli:**
  - "Bugun e'tibor talab qiladiganlar: N bemor" (Qizil va Sariq darajadagilar).
  - Tuman filtri: Urganch, Xiva, Xonqa, Shovot.
  - Holat filtri: Barchasi | Qizil | Ma'lumot yo'q | Sariq | Yashil.
- **Bemorlar Ishchi Jadvali (Worklist Table):**
  - **Saralash qoidasi:** `red` > `no_data` > `amber` > `green`.
  - Ustunlar:
    1. Holat nishoni (Qizil, Sariq, Yashil, Kulrang).
    2. Bemor F.I.Sh, yoshi, jinsi, tashxisi.
    3. AI Xavf Trendi (↗ Yomonlashmoqda, → Barqaror, ↘ Yaxshilanmoqda).
    4. Aniqlangan muammolar (masalan: `SpO2: -2.4σ, HR: +3.1σ`).
    5. Ochiq topshiriq / 24 soatlik Aktiv chaqiruv holati (qolgan vaqt indikatori).
    6. Amallar: "Bemor kartasi" tugmasi.

---

### 3.3 Bemorning Kengaytirilgan Klinik Profili (`/patients/:id`)
- **1. Bemorning Pasport Qismi:**
  - Ism, yoshi, tashxis, tuman, faza (`calib` / `learning` / `full`).
  - Shaxsiy baza holati: "Shifokor tomonidan tasdiqlangan" yoki "Tasdiqlash kutilmoqda".
- **2. 24 Soatlik Aktiv Chaqiruv Kartasi (Muammo 11):**
  - Taymer: Masalan, "Qolgan vaqt: 6 soat 24 daqiqa".
  - Agar 4 soat qolsa -> sariq ogohlantirish, muddati o'tsa -> qizil "Muddati o'tgan" nishoni.
  - **"Tashrifni tasdiqlash" tugmasi:** Shifokor ko'rik o'tkazgach, izoh yozib topshiriqni yopadi (`POST /api/v1/tasks/{id}/confirm`).
- **3. AI 72-soatlik Prognoz va Muammolar Tahlili:**
  - AI dekommutatsiya prognozi foizi va tavsiya.
  - Aniqlangan og'ishlar ro'yxati (parametr, me'yordan farqi va Z-score).
  - IsolationForest anomaliya indeksi (advisory yorliq).
- **4. 7 Kunlik Ko'p Parametrli Klinik Grafiklar:**
  - Har bir ko'rsatkich uchun alohida panel:
    - Yurak urishi (HR mean, min, max).
    - SpO2 (Kislorod to'yinishi).
    - RMSSD / SDNN (Yurak ritmi variabilligi).
    - Teri harorati.
    - Nafas tezligi (RR).
    - Qadamlar va jismoniy faollik.
    - Uyqu davomiyligi va uzilishi.
  - **Recharts LineChart xususiyatlari:**
    - `ReferenceArea`: Bemorning shaxsiy normativ bazasi (`baseline_low` dan `baseline_high` gacha soyalangan koridor).
    - Bemor o'lchovlari chizig'i.
    - Normadan og'igan nuqtalar va oraliqlar (`deviated_ranges`) rangli belgilangan.
- **5. "Bazani tasdiqlash" Tugmasi (`Approve Baseline`):**
  - Agar bemor `phase === 'learning'` (5-7 kunlik o'rganish) bo'lsa, shifokor profilni ko'rib, bitta tugma bilan bazani tasdiqlaydi (`POST /api/v1/patients/{id}/approve-baseline`). Bemor `full` fazaga o'tadi.
- **6. Signallar Tarixi (`alerts`):**
  - Oxirgi signallar ro'yxati, sana, sababi va darajasi.

---

### 3.4 Dockerfile va Build
- `web-doctor/Dockerfile`: Multi-stage build (`node:20-alpine` build -> `nginx:alpine` 80-port).

---

## 4. Majburiy Checkpoint
`/patients` ish ro'yxati va `/patients/:id` tahliliy kartalari real API (yoki mock) orqali to'liq ko'rsatilgach to'xtab hisobot berish.

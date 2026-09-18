# A3: web-doctor — Bajarish Rejasi (PLAN.md)

Papka: `web-doctor/`  
Mas'ul: **A3 agenti**  
Chegaralar: Faqat `web-doctor/`. `web-relative/`, `backend/`, `contracts/` ga tegmaydi!

---

## 1. Asosiy Vazifa
Shifokor va patronaj hamshiralar uchun klinik boshqaruv panelini qurish. Zich, ortiqcha vizual shovqinsiz (gradientlar, og'ir soyalar va animatsiyalarsiz) ish maydoni.

---

## 2. Texnologik Stek va Arxitektura
- React 18 / Vite / TypeScript (Port: 5173, `/api` proxy `http://localhost:8000`).
- Recharts (LineChart, ReferenceArea).
- Dizayn tokenlari: Faqat `contracts/types.ts` dagi `COLORS` va `LEVEL_COLOR`.
- Ko'p tilli qo'llab-quvvatlash: `uz` va `ru`.

---

## 3. Fayllar Tuzilmasi va Qadamlar

### 3.1 Boshlang'ich Sozlash va Tiplar
- [ ] Vite React-TS loyihasini initsializatsiya qilish.
- [ ] `contracts/types.ts` faylini `web-doctor/src/lib/types.ts` ga NUSXALASH (to'g'ridan-to'g'ri import taqiqlangan).
- [ ] `vite.config.ts`: port `5173`, proxy sozlash.

### 3.2 Yordamchi Modullar
- [ ] `src/lib/api.ts`: Fetch klient, `Authorization: Bearer <token>` sarlavhasi bilan. 401 bo'lsa `/login` ga yo'naltiradi.
- [ ] `src/i18n.ts`: Bitta faylda `uz` va `ru` lug'atlari. `I18N_KEYS` dagi barcha backend kalitlari tarjimasi. Yuqori o'ng burchakda til tugmasi (`UZ` | `RU`).
- [ ] `src/lib/mock.ts`: Backend hali to'liq ulanmagan paytda sinash uchun `types.ts` ga mos vaqtinchalik mock (bir flag bilan o'chiriladi).

### 3.3 Sahifalar va Komponentlar
- [ ] `/login`:
  - Shifokor/hamshira kirishi (Telefon: `+998901234567`, Parol: `nazorat123`).
  - `POST /api/v1/auth/login` chaqirib tokenni saqlash.
- [ ] `/patients` (Ish ro'yxati / Worklist):
  - Yuqorida indikator: "Bugun e'tibor talab qiladi — N bemor".
  - Bemorlar qatorlari: holat rangi (`green`, `amber`, `red`, `no_data`), ism, yosh, tashxis, trend o'qi (↗, →, ↘), chetlangan parametrlar qisqa matni, "Ko'rish" tugmasi.
  - Saralash: Backend tartibi bo'yicha (`red` > `no_data` > `amber` > `green`).
- [ ] `/patients/:id` (Bemor Profili):
  - Har parametr uchun (Puls, SpO2, Teri harorati, HRV, RR, Qadamlar) alohida Recharts grafigi:
    - O'lchov nuqtalari (`points`).
    - Shaxsiy norma koridori: `ReferenceArea` orqali `baseline_low` dan `baseline_high` gacha bo'lgan soyalangan fon.
    - Og'ish oralig'i (`deviated_ranges`) rangli belgilangan.
  - **Aktiv chaqiruv kartasi:**
    - Topshiriq turi va qolgan vaqt taymeri (24 soatdan qancha qoldi).
    - "Tasdiqlash" tugmasi -> modal oyna, shifokor izohi -> `POST /api/v1/tasks/{id}/confirm`.
  - **"Bazani tasdiqlash" tugmasi:** Agar `phase === 'learning'` bo'lsa -> `POST /api/v1/patients/{id}/approve-baseline`.
  - Signallar tarixi ro'yxati (`alerts`), `anomaly_score` kichik ikkinchi darajali yorliq sifatida.

### 3.4 Dockerfile
- [ ] `web-doctor/Dockerfile`: Multi-stage: `node:20-alpine` build -> `nginx:alpine` 80-port.

---

## 4. Majburiy Checkpoint
`/patients` sahifasi API (yoki mock) orqali 3 bemorni ko'rsatgach to'xtab hisobot berish.

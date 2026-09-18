# A4: web-relative — Bajarish Rejasi (PLAN.md)

Papka: `web-relative/`  
Mas'ul: **A4 agenti**  
Chegaralar: Faqat `web-relative/`. `web-doctor/`, `backend/`, `contracts/` ga tegmaydi!

---

## 1. Asosiy Vazifa
Bemorning yaqin kishisi uchun mo'ljallangan, mobil telefonlarga moslashtirilgan, 1 soniyada tushuniladigan "WOW" ekran.  
Asosiy tamoyil: Foydalanuvchi 60+ yoshda bo'lishi mumkin. Katta shrift, ulkan ko'rgazmali doira, tinchlantiruvchi yondashuv.

---

## 2. Texnologik Stek
- React 18 / Vite / TypeScript (Port: 5174, `base: '/r/'`, proxy `/api` -> `http://localhost:8000`).
- SVG Sparkline (toza shakl, Recharts shart emas).
- Ranglar: Faqat `contracts/types.ts` dagi `COLORS` va `LEVEL_COLOR`.
- Ko'p tilli qo'llab-quvvatlash: `uz` va `ru`.

---

## 3. Fayllar Tuzilmasi va Qadamlar

### 3.1 Boshlang'ich Sozlash
- [x] Vite React-TS skaffoldini yaratish.
- [x] `vite.config.ts`: `base: '/r/'`, port `5174`, `/api` proxy.
- [x] `contracts/types.ts` ni `src/lib/types.ts` ga NUSXALASH.

### 3.2 Modullar va Yordamchilar
- [x] `src/lib/api.ts`: API so'rovlari (`GET /api/v1/relatives/{token}/view`, `POST /api/v1/auth/relative/login`).
- [x] `src/i18n.ts`: `uz` va `ru` lug'atlari. `I18N_KEYS` ning to'liq tarjimasi. Til almashtirgich yuqori o'ng burchakda.

### 3.3 Sahifalar va UI Arxitekturasi
- [x] **Kirish oynasi (`/r/:token` login):**
  - Oddiy telefon maydoni, 6 xonali PIN maydoni (`112233`), katta tugma.
  - 30 kunlik refresh token localStorage'da saqlanadi.
- [x] **Asosiy Ko'rinish (Yuqoridan pastga):**
  - **1. ULKAN HOLAT DOIRASI:**
    - Ekran kengligining 55% diametrida.
    - Fon rangi: `LEVEL_COLOR` (yashil, sariq, qizil yoki kulrang).
    - Ichida 48px qalin oq yozuv: `YAXSHI` / `E'TIBOR` / `XAVF` / `MA'LUMOT YO'Q` (`level_word_key` bo'yicha).
    - Sahifa ochilganda BIR MARTA 300ms lik pop-scale animatsiyasi.
  - **2. Bemor ismi va yangilanish vaqti:**
    - "Otabek Rahimov · 2 daqiqa oldin".
  - **3. Bitta jumlalik trend tavsifi:**
    - Masalan: "Uch kundan beri holat yaxshilanmoqda".
  - **4. 7 kunlik Sparkline:**
    - O'qlarsiz, raqamlarsiz, to'rlarsiz — toza SVG egri chiziq va mayin fon zonasi (bu grafik emas, holat shakli).
  - **5. Uchta ikkilamchi ko'rsatkich (pastki qism):**
    - Puls · SpO₂ · Uyqu (kichik shriftda).
- [x] **no_data Holati:**
  - Doira KULRANG (`#8A8780`), yozuv: `MA'LUMOT YO'Q`.
  - Tagidagi izoh: "Soat 45 daqiqadan beri ma'lumot yubormayapti."
  - **QAT'IY QOIDA:** Ma'lumot yo'q bo'lsa, hech qachon yashil ko'rinmaydi!

### 3.4 Dockerfile
- [x] `web-relative/Dockerfile`: Multi-stage: Node build -> Nginx Alpine 80-port. SPA routing `/r/` bazasi bilan sozlandi.

---

## 4. Majburiy Checkpoint
Holat doirasi real API (yoki mock) ma'lumotlari bilan to'g'ri rang va matn bilan chiqqach to'xtab hisobot berish.

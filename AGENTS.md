# NAZORAT — parallel qurilish qoidalari

Bu faylni **har bir agent** ishni boshlashdan oldin o'qiydi.

## Qattiq qoidalar

1. **Faqat o'z papkangda yoz.** Boshqa papkadagi faylni o'zgartirish — taqiqlanadi.
   Kerak bo'lsa — to'xta va hisobot ber, o'zing tuzatma.
2. **`contracts/` MUZLATILGAN.** Undan faqat o'qiysan. Shartnoma noto'g'ri
   bo'lsa — to'xta va ayt, o'zing o'zgartirma.
3. **Root fayllarga tegma**: `docker-compose.yml`, `Caddyfile`, `.env*`,
   `deploy.sh`, `AGENTS.md`, `README.md`.
4. **Commit qilma.** Faqat fayl yoz.
5. **Kod ingliz tilida** (o'zgaruvchi, funksiya, kommentariy). **UI matnlari
   o'zbek + rus**, va faqat `i18n` faylida.
6. **`.env` o'qi, qiymat qattiq yozma.** Namuna: `.env.example`.

## Egalik jadvali

| Agent | Papka(lar) | Tegmaydigan joylar |
|---|---|---|
| A1 backend-core | `backend/app/`, `backend/Dockerfile`, `backend/requirements.txt` | `backend/algo/`, `backend/auth/` |
| A2 algo | `backend/algo/`, `scripts/simulate.py` | DB, FastAPI, boshqa hamma joy |
| A3 web-doctor | `web-doctor/` | `web-relative/` |
| A4 web-relative | `web-relative/` | `web-doctor/` |
| A5 wear | `wear/`, `scripts/watch_sim.py` | backend, frontend |
| A6 notifier+auth | `notifier/`, `backend/auth/` | `backend/app/`, `backend/algo/` |

## Uchta integratsiya nuqtasi

1. `contracts/algo_interface.py` — A1 ↔ A2 (sof funksiya imzolari)
2. `contracts/openapi.yaml` — A1 ↔ A3/A4/A5/A6
3. `backend/auth/deps.py` — A6 → A1 (`get_current_user`; A1 uchun stub tayyor)

## Domen qarorlari (o'zgartirilmaydi)

- Holatlar: `green` | `amber` | `red` | `no_data`
- Vaqt oynalari **`Asia/Tashkent`** bo'yicha: 0=00–06, 1=06–12, 2=12–18, 3=18–24
- z-score **yo'nalishli**: spo2/rmssd faqat pasayish, hr/skin_temp/rr faqat ko'tarilish
- Chetlanish **3 ketma-ket oyna** (15 daqiqa) saqlansa signal
- Ingest **idempotent**: `UNIQUE(patient_id, ts)`
- IsolationForest — **advisory**, qarorga ta'sir qilmaydi
- 45 daqiqa o'lchov kelmasa → `no_data` (yashil emas)

---

## Task 0 natijasi (qo'shimcha qarorlar)

- **ORM hamma joyda.** `backend/app` — SQLAlchemy. `notifier` **bir xil image**da
  ishlaydi (`command: python -m notifier.main`) va **o'sha modellarni import qiladi**.
  Nusxa yo'q, drift yo'q. A6 `app.models` dan faqat **o'qiydi**, yozmaydi.
- **Alembic yo'q.** `contracts/schema.sql` — yagona haqiqat. Sxema o'zgarsa:
  `docker compose down -v && docker compose up -d`.
- **Uchta `requirements.txt`**: `backend/`, `backend/algo/`, `backend/auth/`,
  va `notifier/`. Har agent faqat o'zinikiga yozadi. `backend/Dockerfile`
  to'rttasini ham o'rnatadi va **MUZLATILGAN**.
- **Import shakli** (PYTHONPATH `/srv:/srv/backend:/srv/contracts`):
  ```python
  from app.models import Patient          # A1
  from algo.signal import evaluate_alert  # A2 -> A1 chaqiradi
  from auth.deps import get_current_user  # A6 -> A1 chaqiradi
  import timewin                          # umumiy, contracts/
  ```
- **Lokal portlar:** api `8000` · web-doctor vite `5173` · web-relative vite `5174`
  · postgres `5432`. Vite proxy: `/api` -> `http://localhost:8000`.
- **`web-relative` `base: '/r/'` bilan build qilinadi** (Caddy shu yo'lda xizmat qiladi).
- **i18n:** backend **tayyor jumla qaytarmaydi**, faqat kalit
  (`rec.contact_today`, `state.good`). Tarjima frontendda, uz + ru.
  Kalitlar ro'yxati: `contracts/types.ts` -> `I18N_KEYS`.
- **Demo hisoblari:** shifokor `+998901234567` / `nazorat123`,
  hamshira `+998901234568` / `nazorat123`, yaqin kishi PIN `112233`.

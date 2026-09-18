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

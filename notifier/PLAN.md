# A6: notifier + auth — Bajarish Rejasi (PLAN.md)

Papkalar: `backend/auth/` va `notifier/`  
Mas'ul: **A6 agenti**  
Chegaralar: Faqat `backend/auth/` va `notifier/`. `backend/app/` dan faqat ORM modellarni import qiladi, model nusxalamaydi yoki o'zgartirmaydi!

---

## 1. Asosiy Vazifa
1. **Autentifikatsiya (backend/auth/):** Shifokor/hamshiralar uchun JWT (telefon + parol), bemor yaqinlari uchun PIN-kodli login, token yangilash (refresh) va `backend/auth/deps.py` stub faylini haqiqiy implementatsiya bilan almashtirish.
2. **Xabardor qilish va Eskalatsiya (notifier/):** APScheduler yordamida topshiriqlarni eskalatsiya qilish, bemor holati o'zgarganda (daraja o'zgarganda) Telegram xabarnomalarini yuborish va 24 soatlik muddatli vazifalar yaratish.

---

## 2. Fayllar Tuzilmasi va Qadamlar

### 2.1 Autentifikatsiya Qismi (`backend/auth/`)
- [ ] `backend/auth/security.py`:
  - `bcrypt` orqali parollarni tekshirish (`verify_password`) va xeshilash (`hash_password`).
  - `pyjwt` orqali access va refresh token yaratish va dekodlash.
  - `.env` dan parametrlarni o'qish: `JWT_SECRET`, `JWT_ALG`, `ACCESS_TOKEN_TTL_MIN`, `REFRESH_TOKEN_TTL_DAYS`.
- [ ] `backend/auth/deps.py` (STUB almashtiriladi):
  - Qat'iy talab: Mavjud funksiya nomlari va shakli o'zgarmaydi! (`get_current_user`, `require_role`, `auth_router`, `CurrentUser`).
  - Haqiqiy `Authorization: Bearer <token>` tekshiruvi, xato bo'lsa 401 qaytarish.
- [ ] `backend/auth/router.py`:
  - Prefix: `/api/v1/auth`.
  - `POST /login`: Shifokor/hamshira kirishi (telefon + parol, `users` jadvali bo'yicha).
  - `POST /relative/login`: Yaqin kishi kirishi (telefon + 6 xonali PIN, `relatives.pin_hash` bo'yicha).
  - `POST /refresh`: Refresh token rotatsiyasi (`refresh_tokens` jadvali).
  - `GET /me`: Joriy avtorizatsiyadan o'tgan foydalanuvchi ma'lumotlari.

### 2.2 Notifier Qismi (`notifier/`)
> `notifier` api bilan bir xil Docker image'da ishlaydi (`command: python -m notifier.main`).
> Shuning uchun ORM modellar to'g'ridan-to'g'ri import qilinadi: `from app.models import Patient, Alert, Task, ...`.
- [ ] `notifier/telegram.py`:
  - `python-telegram-bot` integratsiyasi.
  - `.env` dan `TELEGRAM_BOT_TOKEN` va `PUBLIC_BASE_URL` o'qish.
  - Agar token bo'sh bo'lsa: qulamasdan faqat loggerga xabar yozish (test va demoda qulaylik).
  - Xabar matnlari o'zbek tilida, tashxis qo'ymasdan: *"Hurmatli fuqaro, [Ism]ning holati e'tibor talab qilmoqda. Havola: {PUBLIC_BASE_URL}/r/{token}"*.
- [ ] `notifier/main.py`:
  - `APScheduler` fon drayveri.
  - **1-ish: Topshiriq Eskalatsiyasi (har 5 daqiqada):**
    - `due_at - now <= 4 soat` va `reminded_at IS NULL` bo'lsa -> shifokorga eslatma, `reminded_at = now`.
    - `now > due_at` va topshiriq bajarilmagan bo'lsa -> `status = 'overdue'`, `escalated_at = now`, admin (boshliq) ga xabar.
  - **2-ish: Signal Kuzatuvchisi (har 1 daqiqada):**
    - `alerts` jadvalidagi oxirgi darajani oldingi daraja bilan solishtirish.
    - **Faqat daraja o'zgarganda xabar yuborish (green -> amber -> red)!**
    - Cooldown tekshiruvi: Agar oxirgi xabar `ALERT_COOLDOWN_HOURS` (6 soat) ichida yuborilgan bo'lsa — takroriy yuborilmaydi.
    - `amber`: Faqat yaqin kishiga (kuniga maksimum 1 marta).
    - `red`: Yaqin kishiga + shifokorga, hamda avtomatik ravishda 24 soatlik `red_alert` Task yaratish (`due_at = now + 24h`).
    - Barcha xabarlarni `notifications` jadvaliga qayd etish.
  - **3-ish: No-data Kuzatuvchisi (har 15 daqiqada):**
    - Agar oxirgi o'lchov 45 daqiqadan oshgan bo'lsa -> yaqin kishiga: "Soat ma'lumot yubormayapti" (kuniga 1 marta).

---

## 3. Majburiy Checkpoint
`/api/v1/auth/login` ishlagach va bitta test Telegram xabari (yoki log) chiqqach to'xtab hisobot berish.

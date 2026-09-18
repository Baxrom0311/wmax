# A6: backend/auth/ — Bajarish Rejasi (PLAN.md)

Papka: `backend/auth/`  
Mas'ul: **A6 agenti**  

Ushbu papka A6 agentining autentifikatsiya qismini o'z ichiga oladi.
Batafsil umumiy reja: [notifier/PLAN.md](file:///Users/baxrom/ish_full/wmax/notifier/PLAN.md)

---

## 1. Asosiy Vazifalar
1. `backend/auth/security.py`:
   - `bcrypt` orqali parol tekshirish va xeshlash.
   - `pyjwt` orqali access va refresh tokenlarni imzolash va verifikatsiya qilish.
   - `.env` dan `JWT_SECRET`, `JWT_ALG`, `ACCESS_TOKEN_TTL_MIN`, `REFRESH_TOKEN_TTL_DAYS` ni o'qish.
2. `backend/auth/deps.py`:
   - Task 0 dagi stub'ni almashtirish.
   - Imzolar qat'iy saqlanadi: `CurrentUser`, `get_current_user`, `require_role`, `auth_router`.
   - Haqiqiy `Authorization: Bearer <token>` tekshiruvi va 401 xatoliklar.
3. `backend/auth/router.py`:
   - Prefix: `/api/v1/auth`.
   - `POST /login` (shifokor/hamshira parolli login).
   - `POST /relative/login` (yaqin kishi PIN login -> `RelativeLoginResponse`: JWT token + biriktirilgan barcha bemorlar ro'yxati `patients: RelativePatientItem[]`).
   - `POST /refresh` (refresh token yangilash).
   - `GET /me` (joriy foydalanuvchi ma'lumotlari).

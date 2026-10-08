# WMAX — Loyiha Tahlili va Brainstorming Hisoboti

## 1. Loyihaning Joriy Holati
- **Backend:** FastAPI, PostgreSQL (RLS & partitsiyalash), Redis, to'liq domen chegaralari (`domain/`). Testlar holati: 195 ta test va 11 ta algoritm testlari muvaffaqiyatli o'tgan (jami 206+ test).
- **Algoritmik Yadro (`backend/algo/signal.py`):** Z-score, sirkadiyalik ritm, harakat artefaktlarini filtrlash (Activity Masking), vaqt bo'yicha barqarorlik (Persistence) va o'rganish fazasi (Learning Phase).
- **Mobil qatlam (`mobile_flutter`):** Wear OS (Samsung Health / Health Services), Android Health Connect va iOS Apple HealthKit integratsiyalari mavjud. Offline rejim uchun Outbox mexanizmi kiritilgan.
- **Frontend panellari:** Shifokorlar uchun (`web-doctor`) va Qarindoshlar uchun (`web-relative`) alohida ixtisoslashtirilgan interfeyslar.
- **Xabarnomalar (`notifier`):** Telegram orqali eskalatsiya zanjiri va tahliliy hisobotlar.

---

## 2. Asosiy Kuchli Jihatlar
1. **Falsafiy va huquqiy aniqlik:** "Tizim o'lchaydi va xabar beradi, tashxisni odam qo'yadi, javobgarlikni muassasa oladi" tamoyili tibbiy sertifikatsiyalash va xatarlarni kamaytirish uchun to'g'ri tanlangan.
2. **Soxta signallarni (False Positives) kamaytirish:** Puls birdan ko'tarilganda qadamlar soni tekshiriladi (agar yugurayotgan bo'lsa, qizil signal berilmaydi); vaqtinchalik o'zgarishlar darhol vahima uyg'otmaydi.
3. **Offline-first Outbox arxitekturasi:** Soat internetga ulanmagan vaqtda ham biometrik ma'lumotlar yo'qolmaydi va aloqa tiklanganda paketlanib jo'natiladi.

---

## 3. Aniqlangan Xatarlar va Muammolar
1. **Lokal testlar va muhit:** Lokal Docker muhitida PostgreSQL ma'lumotlar bazasi `0B` bo'lib turibdi (`docs/DATA_AUDIT.md` bo'yicha A/B migratsiya qarori to'liq bajarilishi lozim).
2. **Git statusdagi to'plangan o'zgarishlar:** 30 dan ortiq faylda stage qilinmagan o'zgarishlar bor. SDLC intizomiga ko'ra ularni kichik, atomik commitlarga ajratish kerak.
3. **Wearable batareya sarfi:** WearOS'da biometrik ma'lumotlarni uzluksiz o'qish batareyani tez tugatishi mumkin. Sampling intervallarini moslashuvchan (dinamik) qilish zarur.

---

## 4. Brainstorming: Kelgusi Rivojlanish Yo'nalishlari

### A. Mahsulot va Foydalanuvchi Tajribasi (UX/Product)
- **"Tinchlik Ko'rsatkichi" (Peace of Mind Index):** Oila a'zolariga murakkab tibbiy raqamlar emas, tushunarli holat indikatori (masalan, "Otasining holati barqaror, barcha ko'rsatkichlar me'yorda") berilishi.
- **Shifokorlar uchun 1-bosqich qabul xulosasi:** Bemor klinika qabuliga kelganda, oxirgi 14 kunlik sirkadiyalik anomaliyalar va o'rtacha ko'rsatkichlar bo'yicha 1 varaqli PDF avtomatik shakllantirilishi.

### B. Texnik va Algoritmik Innovatsiyalar
- **On-Device (Edge) Filtering:** Oddiy shovqinlarni soatning o'zida filtrlash orqali backend yuklamasini va tarmoq trafigini 60-70% ga qisqartirish.
- **Bemor profillari klasteri:** Gipertoniya, qandli diabet yoki insultdan keyingi reabilitatsiya guruhlari uchun individual sezgirlik profillarini joriy etish.

### C. Monetizatsiya va Biznes Modeli
- **Klinikalar uchun B2B SaaS:** Har bir faol bemor o'rni uchun oylik litsenziya + shifokorlar SLA nazorati.
- **B2C Premium Oila Obunasi:** SMS/Telegram zudlik bilan qo'ng'iroq qilish, chuqur tahliliy hisobotlar va tezkor shifokor konsultatsiyasi integratsiyasi.

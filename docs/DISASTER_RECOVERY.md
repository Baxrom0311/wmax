# WMAX Enterprise — Disaster Recovery & SRE Runbook

Ushbu hujjat **WMAX** telemonitoring tizimining kutilmagan favqulodda vaziyatlar (avariya, server qulashi, ma'lumotlar buzilishi, xakerlik hujumlari) vaqtida tizimni tiklash bo'yicha rasmiy **Disaster Recovery (DR)** qo'llanmasidir.

---

## 1. RTO & RPO Maqsadlari

| Ko'rsatkich | Maqsad | Izoh |
|---|---|---|
| **RTO (Recovery Time Objective)** | **< 15 daqiqa** | Tizim to'xtagan paytdan boshlab qayta to'liq ishga tushish vaqti. |
| **RPO (Recovery Point Objective)** | **< 1 soat (AOF) / < 24 soat (Dump)** | Yo'qotilishi mumkin bo'lgan ma'lumotlarning maksimal vaqt oralig'i. |

---

## 2. Avariya Ssenariylari va Qadamma-qadam Harakatlar

### Ssenariy A: Server Qulashi (Cloud VPS / Hardware Crash)
**Holat:** Droplet yoki VM to'liq ishdan chiqdi yoki o'chirildi.

**Tiklash tartibi:**
1. Yangi Ubuntu 24.04 LTS VPS oching.
2. Repozitoriyni klonlang:
   ```bash
   git clone <repo_url> /opt/wmax
   cd /opt/wmax
   ```
3. Serverni 1 buyruq bilan avtomatik sozlang:
   ```bash
   sudo ./scripts/setup_server.sh
   ```
4. `.env` faylini tiklang va Restic yoki oxirgi zaxira nusxasini ko'chiring:
   ```bash
   cp .env.production.example .env
   # Sirli kalitlarni kiriting
   ```
5. Bazani zaxiradan tiklang:
   ```bash
   ./scripts/restore.sh backups/wmax_db_oxirgi.sql.gz
   ```
6. SSL sertifikatini oling va konteynerlarni yoqing:
   ```bash
   ./scripts/renew_ssl.sh
   ./scripts/deploy.sh
   ```

---

### Ssenariy B: Ma'lumotlar Bazasi Buzilishi (Database Corruption / Bad Migration)
**Holat:** Noto'g'ri SQL so'rov, buzilgan migratsiya yoki tasodifiy ma'lumot yo'qolishi.

**Tiklash tartibi:**
1. Servislarga tashqi oqimni vaqtincha to'xtatish uchun Nginx'da texnik tanaffus (maintenance) sahifasini yoqish yoki API ni to'xtatish:
   ```bash
   docker compose -f docker/compose/docker-compose.yml stop api worker
   ```
2. Zaxira nusxasini tekshirish (Dry-Run Test):
   ```bash
   ./scripts/restore.sh backups/wmax_db_20260918_120000.sql.gz --test
   ```
   *Agar test muvaffaqiyatli o'tsa (`RESTORE TEST PASSED`)*:
3. Haqiqiy bazaga tiklashni bajaring:
   ```bash
   ./scripts/restore.sh backups/wmax_db_20260918_120000.sql.gz
   ```
4. API va Worker servislarni qayta ishga tushiring:
   ```bash
   docker compose -f docker/compose/docker-compose.yml start api worker
   ./scripts/healthcheck.sh
   ```

---

### Ssenariy C: Docker Volume O'chib Ketishi (`pgdata` yo'qolishi)
**Holat:** `docker volume rm` yoki fayl tizimi xatosi tufayli `pgdata` jild o'chib ketdi.

**Tiklash tartibi:**
1. Konteynerlarni to'xtating:
   ```bash
   docker compose -f docker/compose/docker-compose.yml down
   ```
2. Yangi jild yaratib, stackni ko'taring:
   ```bash
   docker compose -f docker/compose/docker-compose.yml up -d postgres
   ```
3. PostgreSQL sog'lom holatga o'tishini kuting (`pg_isready`):
   ```bash
   docker compose -f docker/compose/docker-compose.yml exec postgres pg_isready
   ```
4. Oxirgi SQL dumpni import qiling:
   ```bash
   ./scripts/restore.sh backups/wmax_db_LATEST.sql.gz
   ```
5. Qolgan servislarni ko'taring:
   ```bash
   ./scripts/deploy.sh
   ```

---

### Ssenariy D: SSL Sertifikati Buzilishi yoki Muddati O'tib Ketishi
**Holat:** Nginx 443 portda SSL xatosi berdi yoki sertifikat muddati tugadi.

**Tiklash tartibi:**
1. Certbot konteyneri orqali zudlik bilan sertifikatni yangilang:
   ```bash
   ./scripts/renew_ssl.sh
   ```
2. Agar sertifikat buzilgan bo'lsa:
   ```bash
   docker compose -f docker/compose/docker-compose.yml exec certbot certbot delete --cert-name wmax
   ./scripts/init_ssl.sh
   ```

---

### Ssenariy E: Sirli Kalitlar (Secret Rotation) Almashinuvi
**Holat:** `JWT_SECRET`, `POSTGRES_PASSWORD` yoki `GEMINI_API_KEY` tarqalib ketdi (leak).

**Tiklash tartibi:**
1. **Gemini API Key:**
   - Google Cloud Console'da eski kalitni o'chiring, yangi kalit generatsiya qiling.
   - `.env` da `GEMINI_API_KEY=yangi_kalit` ni yangilang.
   - `docker compose -f docker/compose/docker-compose.yml up -d api` orqali API ni yangilang (0 downtime).
2. **JWT Secret:**
   - Yangi 64-baytli tasodifiy kalit generatsiya qiling: `openssl rand -hex 32`.
   - `.env` da `JWT_SECRET` ni almashtiring.
   - Foydalanuvchilar sessiyalari yangilanadi (qayta login talab qilinadi).
3. **Postgres Password:**
   - Baza ichida parolni almashtiring:
     ```bash
     docker compose -f docker/compose/docker-compose.yml exec postgres psql -U wmax -c "ALTER USER wmax WITH PASSWORD 'yangi_parol';"
     ```
   - `.env` dagi `POSTGRES_PASSWORD` va `DATABASE_URL` ni yangilang.
   - `docker compose -f docker/compose/docker-compose.yml restart api worker` bajaring.

---

## 3. Zaxiralash Monitoringi
Kunlik zaxira olinayotganini tekshirish uchun:
```bash
systemctl status wmax-backup.timer
journalctl -u wmax-backup.service -n 50 --no-pager
```

# NAZORAT — DevOps & Nginx Infratuzilmasi

Ushbu hujjat **NAZORAT** telemonitoring tizimining to'liq DevOps infratuzilmasi, Nginx Gateway arxitekturasi, xavfsizlik, zaxira nusxalash (backup), CI/CD va serverni sozlash bo'yicha to'liq qo'llanmani taqdim etadi.

---

## 1. Umumiy Arxitektura va Qismlar

```
                        [ Internet / Mijozlar ]
                                   │
                     HTTPS (443) / HTTP (80 - ACME)
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │               NGINX REVERSE PROXY               │
          │  - TLS 1.2/1.3 + HSTS + Security Headers        │
          │  - Gzip Siqish + JSON Structured Logging        │
          │  - Rate Limiting (auth: 5r/m, ingest: 60r/m)    │
          └───────┬─────────────────┬─────────────────┬─────┘
                  │                 │                 │
           /api/* │              /r/* │                 │ / (boshqa barchasi)
                  ▼                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │  FastAPI     │  │ Web-Relative │  │  Web-Doctor  │
          │  (api:8000)  │  │ (React:80)   │  │ (React:80)   │
          └───────┬──────┘  └──────────────┘  └──────────────┘
                  │
        PostgreSQL 16 (internal_net)
                  ▲
                  │
          ┌───────┴──────┐
          │   Notifier   │
          │  (Telegram)  │
          └──────────────┘
```

---

## 2. Nginx Sozlamalari (Gateway)

Barcha Nginx konfiguratsiyalari `ops/nginx/` papkasida joylashgan:

| Fayl | Tavsifi |
|---|---|
| `ops/nginx/nginx.conf` | Asosiy Nginx konfiguratsiyasi (Worker processes, epoll, bufferlar, gzip, JSON log formati, Rate limiting zonalari). |
| `ops/nginx/conf.d/nazorat.conf` | Production virtual host (HTTP -> HTTPS redirect, Let's Encrypt ACME challenge, SSL hardening, upstream keepalive, marshrutlash). |
| `ops/nginx/conf.d/nazorat-local.conf.example` | Lokal test va ishlab chiqish uchun SSL'siz (HTTP 80) konfiguratsiya. |
| `ops/nginx/Dockerfile` | Maxsus Nginx container imidji (healthcheck va sozlamalar bilan). |

### Marshrutlash Qoidalari:
1. **`/api/v1/auth/`** — Qat'iy rate limit (`zone=auth_zone rate=5r/m burst=10`). PIN kod va parollarni bruteforce qilishdan himoya.
2. **`/api/v1/ingest`** — Aqlli soat ma'lumotlar oqimi (`zone=ingest_zone rate=60r/m burst=30`), `client_max_body_size 25M`.
3. **`/api/`** — Umumiy REST API (`rate=30r/s burst=50`) va WebSocket qo'llab-quvvatlash.
4. **`/docs`, `/redoc`, `/openapi.json`** — API hujjatlari.
5. **`/r/`** — Bemorning yaqin kishisi portali (`X-Robots-Tag "noindex, nofollow"` xavfsizlik sarlavhasi bilan).
6. **`/`** — Shifokor va hamshira klinik paneli.
7. **`/healthz`** — Cloud Load Balancer va monitoring tizimlari uchun 200 OK qaytaruvchi endpoint.

---

## 3. Lokal Muhitda Nginx Bilan Ishga Tushirish

Lokal kompyuterda Nginx orqali barcha servislarni sinab ko'rish:

```bash
# 1. Muhit o'zgaruvchilarini tayyorlash
cp .env.example .env

# 2. Nginx local compose orqali ishga tushirish
docker compose -f ops/docker-compose.nginx-local.yml up -d --build

# 3. Statusni tekshirish
docker compose -f ops/docker-compose.nginx-local.yml ps
```

Brauzerda:
- Shifokor paneli: `http://localhost/`
- Yaqin kishi portali: `http://localhost/r/`
- API hujjatlari: `http://localhost/docs`
- Health check: `http://localhost/healthz`

---

## 4. Production Serverni Sozlash va Ishga Tushirish

### 4.1 Serverni tayyorlash (Ubuntu 22.04 / 24.04 LTS)
Yangi VPS (masalan DigitalOcean Droplet) ga SSH orqali kirib, provisioning skriptini bajaring:

```bash
# Serverda:
sudo ./ops/scripts/setup-server.sh
```
Bu skript:
- Vaqt mintaqasini **`Asia/Tashkent`** ga sozlaydi;
- Docker Engine va Docker Compose plaginini o'rnatadi;
- 2GB Swap xotira ajratadi (OOM xatolarini oldini olish uchun);
- UFW xavfsizlik devorini yoqadi (faqat 22, 80, 443 ochiq qoladi);
- Fail2ban o'rnatadi.

### 4.2 SSL Sertifikatini Olish (Let's Encrypt)
Domain DNS'i server IP manziliga yo'naltirilganidan so'ng:

```bash
# .env faylida DOMAIN va ACME_EMAIL to'ldirilgan bo'lishi kerak
./ops/scripts/init-letsencrypt.sh
```

### 4.3 Production Deploy
```bash
./ops/scripts/deploy-prod.sh
```

---

## 5. Zaxira Nusxalash (Backup & Restore)

### Avtomatik Zaxira (Systemd Timer)
Serverda kunlik avtomatik zaxiralashni yoqish:
```bash
sudo cp ops/systemd/nazorat-backup.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nazorat-backup.timer
```
Zaxira har kuni soat 03:30 da olinadi va oxirgi 7 kunlik zaxiralar saqlanadi.

### Qo'lda Zaxira Olish:
```bash
./ops/scripts/backup-db.sh ./ops/backups
```

### Zaxiradan Qayta Tiklash:
```bash
./ops/scripts/restore-db.sh ops/backups/nazorat_db_20260918_143000.sql.gz
```

---

## 6. CI/CD Pipeline (GitHub Actions)

`.github/workflows/` papkasida 2 ta workflow sozlangan:

1. **`ci.yml`**:
   - Har bir push va Pull Request'da backend kod sifatini (`ruff`), testlarni (`pytest`), frontend build'larini (`npm run build`) va Docker imidjlari xatosiz yig'ilishini tekshiradi.
2. **`cd.yml`**:
   - `main` branch'iga push bo'lganda production serverga rsync orqali yangi kodni uzatadi va `./ops/scripts/deploy-prod.sh` ni ishga tushiradi.
   - Talab qilinadigan GitHub Secrets: `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`.

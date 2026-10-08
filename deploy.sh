#!/usr/bin/env bash
# WMAX Enterprise Production Deployment Script
# DigitalOcean Droplet: 159.89.101.106 (wmax.boos.uz)
set -euo pipefail

TARGET="${1:-root@159.89.101.106}"
SSH_KEY="${SSH_KEY:-$HOME/docean}"
REMOTE_DIR="/opt/wmax"
BACKUP_DIR="/opt/wmax-backups"

SSH_CMD="ssh"
SCP_CMD="scp"
RSYNC_SSH="ssh"
if [ -f "$SSH_KEY" ]; then
  SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no"
  SCP_CMD="scp -i $SSH_KEY -o StrictHostKeyChecking=no"
  RSYNC_SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=no"
fi

echo "========================================================"
echo "  🚀 WMAX Production Deployment: $(date)"
echo "  Target: $TARGET | Key: $SSH_KEY"
echo "========================================================"

# 1. Connectivity Check
echo "[1/6] Tekshiruv: Server bilan aloqa..."
$SSH_CMD "$TARGET" "uptime; free -m; df -h /"

# 2. Pre-deployment Database Safety Backup
echo "[2/6] Xavfsizlik: PostgreSQL ma'lumotlar bazasi zaxira qilinmoqda..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
$SSH_CMD "$TARGET" "mkdir -p $BACKUP_DIR && \
  CONTAINER_ID=\$(docker ps -q -f name=postgres | head -n 1) && \
  if [ -n \"\$CONTAINER_ID\" ]; then \
    docker exec \"\$CONTAINER_ID\" pg_dump -U wmax -d wmax --clean --if-exists | gzip > \"$BACKUP_DIR/wmax_db_${TIMESTAMP}.sql.gz\" && \
    echo '[✓] Zaxira saqlandi: $BACKUP_DIR/wmax_db_${TIMESTAMP}.sql.gz' && \
    ls -lh \"$BACKUP_DIR/wmax_db_${TIMESTAMP}.sql.gz\"; \
  else \
    echo '[!] Ogohlantirish: Postgres konteyneri topilmadi, zaxira olinmadi.'; \
  fi"

# 3. Synchronize Application Files
echo "[3/6] Sinxronizatsiya: Yangilangan fayllar serverga yuborilmoqda..."
rsync -az --delete -e "$RSYNC_SSH" \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude '.venv' \
  --exclude 'pgdata' \
  --exclude 'caddy_data' \
  --exclude 'caddy_config' \
  --exclude 'dist' \
  --exclude 'build' \
  --exclude '.gradle' \
  --exclude '.dart_tool' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude 'backups' \
  --exclude '*.tar.gz' \
  --exclude '*.sql.gz' \
  --exclude 'notifier/*.json' \
  --exclude '*.log' \
  ./ "$TARGET:$REMOTE_DIR/"

# 4. Remote Build & Container Restart
echo "[4/6] Build & Ishga tushirish: Docker konteynerlar yangilanmoqda..."
$SSH_CMD "$TARGET" "cd $REMOTE_DIR && \
  docker compose --env-file .env -f docker/compose/docker-compose.yml build && \
  docker rm -f compose-web-doctor-1 compose-web-relative-1 compose-api-1 compose-notifier-1 compose-postgres-1 6031c705d8f7 2>/dev/null || true; \
  docker compose --env-file .env -f docker/compose/docker-compose.yml up -d && \
  docker compose --env-file .env -f docker/compose/docker-compose.yml ps"

# 5. Database Migrations (Alembic)
echo "[5/6] Migratsiyalar: Alembic ma'lumotlar sxemasini yangilash..."
$SSH_CMD "$TARGET" "cd $REMOTE_DIR && \
  API_CONTAINER=\$(docker ps -q -f name=compose-api | head -n 1) && \
  if [ -n \"\$API_CONTAINER\" ]; then \
    docker exec \"\$API_CONTAINER\" sh -c 'cd /srv/backend && alembic upgrade head' && \
    echo '[✓] Alembic migratsiyasi muvaffaqiyatli yakunlandi.'; \
  else \
    echo '[-] Xato: API konteyneri topilmadi!' && exit 1; \
  fi"

# 6. Host Nginx Gateway & Routing Update
echo "[6/6] Nginx Gateway: Sayt yo'naltirishlari va SSL yangilanmoqda..."
$SSH_CMD "$TARGET" 'cat << "EOF" > /etc/nginx/sites-available/wmax
# wmax.boos.uz — WMAX Enterprise RPM Platform Gateway
server {
    server_name wmax.boos.uz;

    # Cloudflare Real-IP headers
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 131.0.72.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    real_ip_header CF-Connecting-IP;

    client_max_body_size 16M;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript image/svg+xml;

    # 1. Landing Page (Bosh sahifa)
    location = / {
        root /opt/wmax/landing;
        try_files /index.html =404;
    }

    # Landing page static images & assets
    location /images/ {
        root /opt/wmax/landing;
        try_files $uri =404;
    }

    # 2. Backend REST API
    location /api/ {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # WebSocket for realtime clinical updates
    location /api/v1/realtime/ws {
        proxy_pass http://127.0.0.1:8090/api/v1/realtime/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
    }

    location = /health { proxy_pass http://127.0.0.1:8090/health; }
    location = /ready  { proxy_pass http://127.0.0.1:8090/ready; }

    # Interactive API documentation
    location ~ ^/(docs|redoc|openapi\.json)$ {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Internal metrics
    location = /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:8090/metrics;
    }

    # 3. Relative / Caregiver Portal (/r/ & /relative)
    location = /relative {
        return 301 /r/;
    }

    location /r/ {
        add_header X-Robots-Tag "noindex, nofollow" always;
        proxy_pass http://127.0.0.1:8092/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 4. Doctor Clinical Dashboard (/doctor/ & /doctor)
    location = /doctor {
        return 301 /doctor/;
    }

    location = /login {
        return 302 /doctor/;
    }

    location /doctor/ {
        proxy_pass http://127.0.0.1:8091;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen [::]:443 ssl ipv6only=on;
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/wmax.boos.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wmax.boos.uz/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = wmax.boos.uz) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    listen [::]:80;
    server_name wmax.boos.uz;
    return 404;
}
EOF
cp /etc/nginx/sites-available/wmax /etc/nginx/sites-enabled/wmax
nginx -t && systemctl reload nginx
'

# 7. Verification & Health Check
echo "========================================================"
echo "  🔍 Deploy Tekshiruvi: Xizmatlar salomatligi..."
echo "========================================================"
$SSH_CMD "$TARGET" "curl -sI https://wmax.boos.uz/health | head -n 1 && \
  curl -sI https://wmax.boos.uz/ready | head -n 1 && \
  curl -sI https://wmax.boos.uz/ | head -n 1 && \
  curl -sI https://wmax.boos.uz/doctor/ | head -n 1 && \
  curl -sI https://wmax.boos.uz/r/ | head -n 1"

echo "========================================================"
echo "  ✅ WMAX MUVAFFAQIYATLI DEPLOY QILINDI!"
echo "  Bosh sahifa:         https://wmax.boos.uz/"
echo "  Shifokor portali:    https://wmax.boos.uz/doctor/"
echo "  Qarovchi portali:    https://wmax.boos.uz/r/"
echo "  API Hujjati (Docs):  https://wmax.boos.uz/docs"
echo "========================================================"

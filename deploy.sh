#!/usr/bin/env bash
# DigitalOcean Droplet'ga deploy. Birinchi marta: ssh orqali docker o'rnatilgan bo'lsin.
#   ./deploy.sh root@<droplet-ip>
set -euo pipefail
TARGET="${1:?Foydalanish: ./deploy.sh root@<droplet-ip>}"
REMOTE_DIR="/opt/wmax"

echo "→ Fayllar yuborilmoqda..."
rsync -az --delete \
  --exclude '.git' --exclude 'node_modules' --exclude '.venv' \
  --exclude 'pgdata' --exclude 'caddy_data' --exclude 'caddy_config' \
  --exclude 'dist' --exclude 'build' --exclude '.gradle' \
  ./ "$TARGET:$REMOTE_DIR/"

echo "→ Build va ishga tushirish..."
ssh "$TARGET" "cd $REMOTE_DIR && docker compose up -d --build && docker compose ps"
echo "✓ Tayyor."

#!/usr/bin/env bash
# WMAX SSL Bootstrap Script (Nginx + Let's Encrypt Certbot)
# Resolves the chicken-and-egg problem of Nginx SSL startup.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"
cd "${ROOT_DIR}"

# Load domain and email from .env safely
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DOMAIN="${DOMAIN:-wmax.example.uz}"
EMAIL="${ACME_EMAIL:-admin@wmax.uz}"
STAGING="${STAGING:-0}" # Set to 1 for staging testing against Let's Encrypt rate limits

echo "=========================================="
echo "Initializing Let's Encrypt SSL for: ${DOMAIN}"
echo "Contact Email: ${EMAIL}"
echo "=========================================="

CERT_DIR="certbot_etc"
DATA_PATH="./certbot_data"

# Create dummy certificates first if none exist
echo "[+] Step 1: Creating temporary dummy certificates..."
docker compose -f "${COMPOSE_FILE}" run --rm --entrypoint "\
  mkdir -p /etc/letsencrypt/live/wmax && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '/etc/letsencrypt/live/wmax/privkey.pem' \
    -out '/etc/letsencrypt/live/wmax/fullchain.pem' \
    -subj '/CN=localhost'" certbot

echo "[+] Step 2: Starting Nginx..."
docker compose -f "${COMPOSE_FILE}" up -d --force-recreate nginx

echo "[+] Step 3: Removing dummy certificates..."
docker compose -f "${COMPOSE_FILE}" run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/wmax" certbot

echo "[+] Step 4: Requesting genuine Let's Encrypt certificate..."
STAGING_ARG=""
if [ "${STAGING}" != "0" ]; then
  STAGING_ARG="--staging"
fi

docker compose -f "${COMPOSE_FILE}" run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    ${STAGING_ARG} \
    --email ${EMAIL} \
    -d ${DOMAIN} \
    --cert-name wmax \
    --rsa-key-size 4096 \
    --agree-tos \
    --non-interactive \
    --force-renewal" certbot

echo "[+] Step 5: Reloading Nginx with new certificate..."
docker compose -f "${COMPOSE_FILE}" exec nginx nginx -s reload

echo "[✓] Let's Encrypt SSL successfully configured for ${DOMAIN}!"

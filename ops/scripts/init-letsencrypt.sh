#!/usr/bin/env bash
# NAZORAT SSL Bootstrap Script (Nginx + Let's Encrypt Certbot)
# Resolves the chicken-and-egg problem of Nginx SSL startup.

set -euo pipefail

COMPOSE_FILE="ops/docker-compose.prod.yml"

# Load domain and email from .env
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

DOMAIN="${DOMAIN:-nazorat.example.uz}"
EMAIL="${ACME_EMAIL:-admin@example.uz}"
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
  mkdir -p /etc/letsencrypt/live/nazorat && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '/etc/letsencrypt/live/nazorat/privkey.pem' \
    -out '/etc/letsencrypt/live/nazorat/fullchain.pem' \
    -subj '/CN=localhost'" certbot

echo "[+] Step 2: Starting Nginx..."
docker compose -f "${COMPOSE_FILE}" up -d --force-recreate nginx

echo "[+] Step 3: Removing dummy certificates..."
docker compose -f "${COMPOSE_FILE}" run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/nazorat" certbot

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
    --cert-name nazorat \
    --rsa-key-size 4096 \
    --agree-tos \
    --non-interactive \
    --force-renewal" certbot

echo "[+] Step 5: Reloading Nginx with new certificate..."
docker compose -f "${COMPOSE_FILE}" exec nginx nginx -s reload

echo "[✓] SSL successfully configured for https://${DOMAIN}!"

#!/usr/bin/env bash
# WMAX Let's Encrypt SSL Automated Renewal Script
# Usage: ./scripts/renew_ssl.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"
COMPOSE_PROJECT="${COMPOSE_PROJECT_NAME:-compose}"
compose() { docker compose -p "${COMPOSE_PROJECT}" --profile edge -f "${COMPOSE_FILE}" "$@"; }

echo "========================================================"
echo "  Checking SSL Certificate Expiration & Renewal: $(date)"
echo "========================================================"

# Run certbot renew
compose run --rm --entrypoint certbot certbot renew --quiet

# Gracefully reload Nginx to load newly issued certificate
echo "[+] Reloading Nginx configuration without connection drop..."
compose exec nginx nginx -s reload

echo "[✓] SSL Renewal Verification Complete."

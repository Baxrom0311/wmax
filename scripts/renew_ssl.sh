#!/usr/bin/env bash
# NAZORAT Let's Encrypt SSL Automated Renewal Script
# Usage: ./scripts/renew_ssl.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"

echo "========================================================"
echo "  Checking SSL Certificate Expiration & Renewal: $(date)"
echo "========================================================"

# Run certbot renew
docker compose -f "${COMPOSE_FILE}" run --rm certbot renew --quiet

# Gracefully reload Nginx to load newly issued certificate
echo "[+] Reloading Nginx configuration without connection drop..."
docker compose -f "${COMPOSE_FILE}" exec nginx nginx -s reload

echo "[✓] SSL Renewal Verification Complete."

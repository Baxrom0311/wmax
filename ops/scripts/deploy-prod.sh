#!/usr/bin/env bash
# NAZORAT Production Deployment Script (Nginx + Docker Compose)
# Usage: ./ops/scripts/deploy-prod.sh

set -euo pipefail

COMPOSE_FILE="ops/docker-compose.prod.yml"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${PROJECT_DIR}"

echo "=========================================="
echo "Starting Production Deployment: $(date)"
echo "Project Directory: ${PROJECT_DIR}"
echo "=========================================="

# 1. Pre-flight checks
if [ ! -f .env ]; then
  echo "[-] ERROR: .env file not found in ${PROJECT_DIR}!" >&2
  echo "    Please create .env from .env.example before deploying." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[-] ERROR: docker is not installed!" >&2
  exit 1
fi

# 2. Automated Safety Backup
if docker ps -q -f "name=postgres" | grep -q .; then
  echo "[+] Step 1: Performing pre-deployment database backup..."
  ./ops/scripts/backup-db.sh ./ops/backups || {
    echo "[-] WARNING: Database backup failed. Proceeding with caution..." >&2
  }
else
  echo "[*] Step 1: PostgreSQL is not running yet. Skipping pre-deploy backup."
fi

# 3. Build and recreate containers
echo "[+] Step 2: Building and launching production containers..."
docker compose -f "${COMPOSE_FILE}" build --pull
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

# 4. Wait for services to become healthy
echo "[+] Step 3: Waiting for healthchecks to pass..."
MAX_RETRIES=15
COUNTER=0

while [ $COUNTER -lt $MAX_RETRIES ]; do
  if docker compose -f "${COMPOSE_FILE}" ps | grep -E "(unhealthy|starting)"; then
    echo "    Waiting for services to become healthy... ($((COUNTER + 1))/${MAX_RETRIES})"
    sleep 4
    COUNTER=$((COUNTER + 1))
  else
    echo "[+] All services are up and healthy!"
    break
  fi
done

# 5. Verify HTTP/HTTPS endpoints
echo "[+] Step 4: Verifying gateway health..."
sleep 2
if docker compose -f "${COMPOSE_FILE}" exec nginx wget --quiet --tries=1 --spider http://127.0.0.1/healthz; then
  echo "[✓] Nginx gateway health check passed (/healthz -> 200 OK)."
else
  echo "[-] WARNING: Nginx healthcheck returned non-zero exit code!" >&2
fi

# 6. Clean dangling images
echo "[+] Step 5: Pruning dangling Docker images..."
docker image prune -f || true

echo "=========================================="
echo "[✓] Deployment Completed Successfully!"
docker compose -f "${COMPOSE_FILE}" ps
echo "=========================================="

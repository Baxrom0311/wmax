#!/usr/bin/env bash
# WMAX Enterprise Zero-Downtime Deployment Script
# Role: Principal SRE / Release Engineer
# Usage: ./scripts/deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"

cd "${ROOT_DIR}"

echo "========================================================"
echo "  WMAX Enterprise Deployment: $(date)"
echo "========================================================"

# 1. Environment & Secret Pre-flight Validation
if [ ! -f .env ]; then
  echo "[-] ERROR: .env file missing in ${ROOT_DIR}!" >&2
  exit 1
fi

REQUIRED_VARS=("POSTGRES_PASSWORD" "JWT_SECRET")
for var in "${REQUIRED_VARS[@]}"; do
  if ! grep -q "^${var}=" .env; then
    echo "[-] FATAL: Required secret '${var}' missing in .env!" >&2
    exit 1
  fi
done

# 2. Automated Pre-Deployment Database Backup
echo "[1/5] Running automated safety backup..."
"${SCRIPT_DIR}/backup.sh" || {
  echo "[-] Pre-deployment backup failed. Halting deployment for safety." >&2
  exit 1
}

# 3. Save current container state for rollback
mkdir -p "${ROOT_DIR}/.deploy_state"
if docker compose -f "${COMPOSE_FILE}" ps -q api >/dev/null 2>&1; then
  docker compose -f "${COMPOSE_FILE}" ps -q > "${ROOT_DIR}/.deploy_state/previous_containers.txt" || true
fi

# 4. Build Images & Launch Stack
echo "[2/5] Building images and launching containers..."
docker compose -f "${COMPOSE_FILE}" build --pull
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

# 5. Deep Health Check Verification
echo "[3/5] Verifying system health and readiness..."
HEALTHY=false
RETRIES=15
WAIT_SEC=4

for ((i=1; i<=RETRIES; i++)); do
  echo "      Probe ${i}/${RETRIES}: checking /ready and /healthz..."
  
  API_READY=$(docker compose -f "${COMPOSE_FILE}" exec -T api curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ready || echo "000")
  NGINX_READY=$(docker compose -f "${COMPOSE_FILE}" exec -T nginx wget -q -O /dev/null --spider http://127.0.0.1/healthz && echo "200" || echo "000")

  if [ "${API_READY}" == "200" ] && [ "${NGINX_READY}" == "200" ]; then
    HEALTHY=true
    break
  fi
  sleep "${WAIT_SEC}"
done

if [ "${HEALTHY}" = false ]; then
  echo "[-] ERROR: Health check timed out! Initiating AUTOMATIC ROLLBACK..." >&2
  "${SCRIPT_DIR}/rollback.sh"
  exit 1
fi

# 6. Cleanup dangling resources
echo "[4/5] Pruning obsolete dangling docker images..."
docker image prune -f >/dev/null 2>&1 || true

# 7. Record Success State
git rev-parse HEAD > "${ROOT_DIR}/.deploy_state/last_successful_commit.txt" 2>/dev/null || true

echo "[5/5] Deployment Successful!"
echo "========================================================"
docker compose -f "${COMPOSE_FILE}" ps
echo "========================================================"

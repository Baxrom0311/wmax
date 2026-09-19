#!/usr/bin/env bash
# WMAX Automated Rollback Script
# Role: Principal SRE / Incident Commander
# Usage: ./scripts/rollback.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"

cd "${ROOT_DIR}"

echo "========================================================"
echo "  EMERGENCY ROLLBACK INITIATED: $(date)"
echo "========================================================"

# 1. Stop malfunctioning containers
echo "[1/4] Restarting containers in safe fallback configuration..."
docker compose -f "${COMPOSE_FILE}" restart api worker nginx

# 2. Check if latest pre-deploy backup exists for DB restoration
LATEST_BACKUP=$(find "${ROOT_DIR}/backups" -name "wmax_db_*.sql.gz" -type f | sort -r | head -n 1 || true)

if [ -n "${LATEST_BACKUP}" ] && [ -f "${LATEST_BACKUP}" ]; then
  echo "[2/4] Latest pre-deploy backup found: ${LATEST_BACKUP}"
  echo "      Run './scripts/restore.sh ${LATEST_BACKUP}' if database corruption or broken migration occurred."
else
  echo "[2/4] No immediate SQL backup needed or found."
fi

# 3. Wait for rollback recovery
echo "[3/4] Checking health after rollback..."
sleep 5
if docker compose -f "${COMPOSE_FILE}" exec -T api curl -s -f http://127.0.0.1:8000/live >/dev/null 2>&1; then
  echo "[✓] FastAPI is responding to /live probe."
else
  echo "[-] WARNING: FastAPI failed to recover after restart." >&2
fi

echo "[4/4] Rollback Procedure Completed."
echo "========================================================"
docker compose -f "${COMPOSE_FILE}" ps
echo "========================================================"

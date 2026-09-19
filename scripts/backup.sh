#!/usr/bin/env bash
# WMAX Enterprise Automated Backup Script (PostgreSQL + Restic)
# Retention Policy: 7 Days Daily, 30 Days Weekly, 90 Days Monthly Archive
# Usage: ./scripts/backup.sh [backup_dir]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${1:-${ROOT_DIR}/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/wmax_db_${TIMESTAMP}.sql.gz"

cd "${ROOT_DIR}"
mkdir -p "${BACKUP_DIR}"

# Load environment safely
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DB_USER="${POSTGRES_USER:-wmax}"
DB_NAME="${POSTGRES_DB:-wmax}"

echo "========================================================"
echo "  Starting Database Backup: ${TIMESTAMP}"
echo "========================================================"

# Find running postgres container
CONTAINER_ID=$(docker compose -f "${ROOT_DIR}/docker/compose/docker-compose.yml" ps -q postgres 2>/dev/null || docker ps -q -f "name=postgres" | head -n 1)

if [ -z "${CONTAINER_ID}" ]; then
  echo "[-] ERROR: PostgreSQL container is not running!" >&2
  exit 1
fi

echo "[1/4] Dumping database '${DB_NAME}' via container ${CONTAINER_ID}..."
docker exec -t "${CONTAINER_ID}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"

# Verify backup integrity
if [ ! -s "${BACKUP_FILE}" ]; then
  echo "[-] ERROR: Backup file was created empty!" >&2
  rm -f "${BACKUP_FILE}"
  exit 1
fi

# Generate SHA256 Checksum
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
elif command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
fi

echo "[✓] Local dump created: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Restic Cloud / Offsite snapshot integration
if command -v restic >/dev/null 2>&1 && [ -n "${RESTIC_REPOSITORY:-}" ]; then
  echo "[2/4] Uploading snapshot to Restic remote repository..."
  
  if ! restic snapshots >/dev/null 2>&1; then
    echo "      Initializing Restic repository..."
    restic init
  fi

  restic backup "${BACKUP_DIR}" --tag "postgres,daily"
  
  # Enforce Retention: 7 daily, 4 weekly (~30 days), 3 monthly (~90 days)
  echo "[3/4] Enforcing Restic retention policy (7d, 30d, 90d)..."
  restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune
else
  echo "[2/4] Local backup retention enforcement (7 days daily)..."
  find "${BACKUP_DIR}" -name "wmax_db_*.sql.gz*" -type f -mtime +7 -exec rm -f {} \;
fi

echo "[4/4] Backup completed successfully!"
ls -lh "${BACKUP_DIR}"

#!/usr/bin/env bash
# NAZORAT Database Automated Backup Script
# Usage: ./ops/scripts/backup-db.sh [backup_directory]

set -euo pipefail

BACKUP_DIR="${1:-./ops/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/nazorat_db_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=7

# Load environment variables from .env if present
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

DB_USER="${POSTGRES_USER:-nazorat}"
DB_NAME="${POSTGRES_DB:-nazorat}"

mkdir -p "${BACKUP_DIR}"

echo "=========================================="
echo "Starting PostgreSQL Backup: ${TIMESTAMP}"
echo "Database: ${DB_NAME} (User: ${DB_USER})"
echo "=========================================="

# Find running postgres container
CONTAINER_ID=$(docker ps -q -f "name=postgres" | head -n 1)

if [ -z "${CONTAINER_ID}" ]; then
  echo "[-] ERROR: PostgreSQL container is not running!" >&2
  exit 1
fi

echo "[+] Container found: ${CONTAINER_ID}"
echo "[+] Dumping database to ${BACKUP_FILE}..."

docker exec -t "${CONTAINER_ID}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip > "${BACKUP_FILE}"

# Verify backup was created and not empty
if [ -s "${BACKUP_FILE}" ]; then
  SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
  echo "[+] Backup successfully created! Size: ${SIZE}"
  
  # Generate SHA256 checksum
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
  fi
else
  echo "[-] ERROR: Backup file is empty or was not created!" >&2
  rm -f "${BACKUP_FILE}"
  exit 1
fi

# Clean up backups older than RETENTION_DAYS
echo "[+] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "nazorat_db_*.sql.gz*" -type f -mtime +"${RETENTION_DAYS}" -exec rm -f {} \;

echo "[+] Done. Backups retained in ${BACKUP_DIR}:"
ls -lh "${BACKUP_DIR}"

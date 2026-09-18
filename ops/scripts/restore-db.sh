#!/usr/bin/env bash
# NAZORAT Database Restore Script
# Usage: ./ops/scripts/restore-db.sh <path_to_backup_file.sql.gz>

set -euo pipefail

BACKUP_FILE="${1:?Usage: ./ops/scripts/restore-db.sh <path_to_backup_file.sql.gz>}"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "[-] ERROR: File '${BACKUP_FILE}' does not exist!" >&2
  exit 1
fi

# Load environment variables
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

DB_USER="${POSTGRES_USER:-nazorat}"
DB_NAME="${POSTGRES_DB:-nazorat}"

echo "=========================================="
echo "WARNING: DATABASE RESTORE OPERATION"
echo "Target DB: ${DB_NAME}"
echo "Source file: ${BACKUP_FILE}"
echo "This will OVERWRITE the current database data!"
echo "=========================================="

read -r -p "Are you absolutely sure you want to proceed? [y/N]: " CONFIRM
if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
  echo "[*] Aborted by user."
  exit 0
fi

CONTAINER_ID=$(docker ps -q -f "name=postgres" | head -n 1)

if [ -z "${CONTAINER_ID}" ]; then
  echo "[-] ERROR: PostgreSQL container is not running!" >&2
  exit 1
fi

echo "[+] Restoring database into container ${CONTAINER_ID}..."

if [[ "${BACKUP_FILE}" == *.gz ]]; then
  gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${DB_NAME}"
else
  cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${DB_NAME}"
fi

echo "[+] Database restore completed successfully."

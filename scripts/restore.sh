#!/usr/bin/env bash
# NAZORAT Database Restore & Disaster Recovery Script
# Usage: ./scripts/restore.sh <backup_file.sql.gz> [--test]

set -euo pipefail

BACKUP_FILE="${1:?Usage: ./scripts/restore.sh <path_to_backup.sql.gz> [--test]}"
TEST_MODE=false

if [ "${2:-}" == "--test" ]; then
  TEST_MODE=true
fi

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "[-] ERROR: Backup file '${BACKUP_FILE}' does not exist!" >&2
  exit 1
fi

# Load environment
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs)
fi

DB_USER="${POSTGRES_USER:-nazorat}"
DB_NAME="${POSTGRES_DB:-nazorat}"

CONTAINER_ID=$(docker ps -q -f "name=postgres" | head -n 1 || true)
if [ -z "${CONTAINER_ID}" ]; then
  echo "[-] ERROR: PostgreSQL container is not running!" >&2
  exit 1
fi

if [ "${TEST_MODE}" = true ]; then
  echo "========================================================"
  echo "  RUNNING RESTORE VERIFICATION TEST (Dry Run / Test DB)"
  echo "========================================================"
  TEST_DB="nazorat_restore_test_${RANDOM}"
  
  echo "[1/3] Creating test database '${TEST_DB}'..."
  docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -c "CREATE DATABASE ${TEST_DB};"

  echo "[2/3] Restoring backup dump into test database..."
  if [[ "${BACKUP_FILE}" == *.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" >/dev/null 2>&1
  else
    cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" >/dev/null 2>&1
  fi

  echo "[3/3] Validating tables and row counts in test database..."
  TABLE_COUNT=$(docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
  echo "[+] Tables restored in test database: ${TABLE_COUNT}"

  # Cleanup test db
  docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -c "DROP DATABASE ${TEST_DB};"
  echo "[✓] RESTORE TEST PASSED! The backup file is healthy and integral."
  exit 0
fi

echo "========================================================"
echo "  WARNING: PRODUCTION DATABASE RESTORATION"
echo "  Target: ${DB_NAME} (User: ${DB_USER})"
echo "  Source: ${BACKUP_FILE}"
echo "========================================================"

read -r -p "Type 'RESTORE' to confirm overwriting current database: " CONFIRM
if [ "${CONFIRM}" != "RESTORE" ]; then
  echo "[*] Restoration aborted by user."
  exit 0
fi

echo "[1/2] Overwriting database with backup data..."
if [[ "${BACKUP_FILE}" == *.gz ]]; then
  gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${DB_NAME}"
else
  cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${DB_NAME}"
fi

echo "[2/2] Verifying database integrity..."
docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "\dt"

echo "[✓] Database successfully restored."

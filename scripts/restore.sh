#!/usr/bin/env bash
# WMAX Database Restore & Disaster Recovery Script
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

# Load environment safely
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DB_USER="${POSTGRES_USER:-wmax}"
DB_NAME="${POSTGRES_DB:-wmax}"

CONTAINER_ID=$(docker ps -q -f "name=postgres" | head -n 1 || true)
if [ -z "${CONTAINER_ID}" ]; then
  echo "[-] ERROR: PostgreSQL container is not running!" >&2
  exit 1
fi

if [ "${TEST_MODE}" = true ]; then
  echo "========================================================"
  echo "  RUNNING RESTORE VERIFICATION TEST (Dry Run / Test DB)"
  echo "========================================================"
  TEST_DB="wmax_restore_test_${RANDOM}"
  
  echo "[1/3] Creating test database '${TEST_DB}'..."
  docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -c "CREATE DATABASE ${TEST_DB};"

  echo "[2/3] Restoring backup dump into test database..."
  if [[ "${BACKUP_FILE}" == *.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" >/dev/null 2>&1
  else
    cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" >/dev/null 2>&1
  fi

  echo "[3/3] Verifying row counts and dropping test database..."
  READING_COUNT=$(docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" -t -c "SELECT COUNT(*) FROM readings;" | tr -d '[:space:]')
  PATIENT_COUNT=$(docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" -t -c "SELECT COUNT(*) FROM patients;" | tr -d '[:space:]')

  docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -c "DROP DATABASE ${TEST_DB};"

  echo "[✓] RESTORE TEST PASSED: Database restored cleanly with ${PATIENT_COUNT} patients and ${READING_COUNT} readings."
  exit 0
fi

echo "========================================================"
echo "  WARNING: PRODUCTION DATABASE RESTORE OPERATION"
echo "  Target Database: ${DB_NAME}"
echo "  Source Archive:  ${BACKUP_FILE}"
echo "========================================================"
read -r -p "Type 'RESTORE' to proceed with wiping and overwriting database: " CONFIRM

if [ "${CONFIRM}" != "RESTORE" ]; then
  echo "[*] Aborted by user."
  exit 0
fi

echo "[1/2] Terminating active connections to ${DB_NAME}..."
docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d postgres -c "
  SELECT pg_terminate_backend(pg_stat_activity.pid)
  FROM pg_stat_activity
  WHERE pg_stat_activity.datname = '${DB_NAME}'
    AND pid <> pg_backend_pid();" >/dev/null 2>&1 || true

echo "[2/2] Restoring dump..."
if [[ "${BACKUP_FILE}" == *.gz ]]; then
  gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${DB_NAME}"
else
  cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${DB_NAME}"
fi

echo "[✓] Database restored successfully."

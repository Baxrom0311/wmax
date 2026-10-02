#!/usr/bin/env bash
# WMAX Database Restore & Disaster Recovery Script
# Usage: ./scripts/restore.sh <backup_file.sql.gz> [--test]

set -euo pipefail

BACKUP_FILE="${1:?Usage: ./scripts/restore.sh <path_to_backup.sql.gz> [--test]}"
TEST_MODE=false
case "${BACKUP_FILE}" in
  /*) ;;
  *) BACKUP_FILE="${PWD}/${BACKUP_FILE}" ;;
esac
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"
cd "${ROOT_DIR}"

if [ "${2:-}" == "--test" ]; then
  TEST_MODE=true
fi

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "[-] ERROR: Backup file '${BACKUP_FILE}' does not exist!" >&2
  exit 1
fi

if [[ "${BACKUP_FILE}" == *.gz ]] && ! gzip -t "${BACKUP_FILE}"; then
  echo "[-] ERROR: Backup archive failed gzip integrity verification." >&2
  exit 1
fi

CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
  EXPECTED_CHECKSUM="$(awk 'NR == 1 { print $1 }' "${CHECKSUM_FILE}")"
  if command -v sha256sum >/dev/null 2>&1; then
    ACTUAL_CHECKSUM="$(sha256sum "${BACKUP_FILE}" | awk '{ print $1 }')"
  else
    ACTUAL_CHECKSUM="$(shasum -a 256 "${BACKUP_FILE}" | awk '{ print $1 }')"
  fi
  if [ -z "${EXPECTED_CHECKSUM}" ] || [ "${EXPECTED_CHECKSUM}" != "${ACTUAL_CHECKSUM}" ]; then
    echo "[-] ERROR: Backup checksum verification failed." >&2
    exit 1
  fi
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

if [ "${TEST_MODE}" = true ]; then
  if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo "[-] ERROR: POSTGRES_PASSWORD is required for isolated restore verification." >&2
    exit 1
  fi
  echo "========================================================"
  echo "  RUNNING ISOLATED BACKUP RESTORE VERIFICATION"
  echo "========================================================"
  TEST_DB="wmax_restore_test_${RANDOM}_$$"
  TEST_CONTAINER="wmax-restore-test-$$"
  docker run -d --rm --network none \
    --cpus "${RESTORE_TEST_CPUS:-1.0}" \
    --memory "${RESTORE_TEST_MEMORY:-512m}" \
    --name "${TEST_CONTAINER}" \
    -e "POSTGRES_USER=${DB_USER}" \
    -e "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" \
    -e "POSTGRES_DB=${DB_NAME}" postgres:16-alpine >/dev/null
  CONTAINER_ID="${TEST_CONTAINER}"
  cleanup_test_db() { docker rm -f "${TEST_CONTAINER}" >/dev/null 2>&1 || true; }
  trap cleanup_test_db EXIT

  ready=false
  for _ in $(seq 1 30); do
    if docker exec "${CONTAINER_ID}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 1
  done
  if [ "${ready}" != true ]; then
    echo "[-] ERROR: Temporary PostgreSQL did not become ready." >&2
    exit 1
  fi
  
  echo "[1/3] Creating test database '${TEST_DB}'..."
  docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -c "CREATE DATABASE ${TEST_DB};"

  echo "[2/3] Restoring backup dump into test database..."
  if [[ "${BACKUP_FILE}" == *.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${TEST_DB}" >/dev/null 2>&1
  else
    docker exec -i "${CONTAINER_ID}" psql -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${TEST_DB}" < "${BACKUP_FILE}" >/dev/null 2>&1
  fi

  echo "[3/3] Verifying row counts and dropping test database..."
  READING_COUNT=$(docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" -t -c "SELECT COUNT(*) FROM readings;" | tr -d '[:space:]')
  PATIENT_COUNT=$(docker exec -i "${CONTAINER_ID}" psql -U "${DB_USER}" -d "${TEST_DB}" -t -c "SELECT COUNT(*) FROM patients;" | tr -d '[:space:]')

  cleanup_test_db
  trap - EXIT

  echo "[✓] RESTORE TEST PASSED: Database restored cleanly with ${PATIENT_COUNT} patients and ${READING_COUNT} readings."
  exit 0
fi

CONTAINER_ID=$(docker compose -p "${COMPOSE_PROJECT_NAME:-compose}" -f "${COMPOSE_FILE}" ps -q postgres 2>/dev/null || true)
if [ -z "${CONTAINER_ID}" ]; then
  echo "[-] ERROR: PostgreSQL container is not running!" >&2
  exit 1
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
  gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_ID}" psql -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}"
else
  docker exec -i "${CONTAINER_ID}" psql -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}" < "${BACKUP_FILE}"
fi

echo "[✓] Database restored successfully."

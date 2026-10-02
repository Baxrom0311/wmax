#!/usr/bin/env bash
# WMAX Automated Rollback Script
# Role: Principal SRE / Incident Commander
# Usage: ./scripts/rollback.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"
COMPOSE_PROJECT="${COMPOSE_PROJECT_NAME:-compose}"
LAST_SUCCESS="${ROOT_DIR}/.deploy_state/last_successful_release.txt"

RELEASE_TAG="${DEPLOY_RELEASE:-local}"
if [ -s "${LAST_SUCCESS}" ]; then
  RELEASE_TAG="$(tr -d '[:space:]' < "${LAST_SUCCESS}")"
fi

compose() {
  RELEASE_TAG="${RELEASE_TAG}" docker compose -p "${COMPOSE_PROJECT}" --profile edge -f "${COMPOSE_FILE}" "$@"
}

cd "${ROOT_DIR}"

if [ ! -s "${LAST_SUCCESS}" ]; then
  if [ -s "${ROOT_DIR}/.deploy_state/release_started.txt" ] \
    || [ -s "${ROOT_DIR}/.deploy_state/candidate_release.txt" ]; then
    echo "[-] No prior release image exists; stopping candidate app services and preserving data services."
    compose stop api worker web-doctor web-relative nginx
    rm -f "${ROOT_DIR}/.deploy_state/release_started.txt" \
      "${ROOT_DIR}/.deploy_state/candidate_release.txt" \
      "${ROOT_DIR}/.deploy_state/deploying_release.txt"
  else
    echo "[-] No release was started and there is no previous release to restore." >&2
  fi
  exit 1
fi

echo "========================================================"
echo "  EMERGENCY ROLLBACK INITIATED: $(date)"
echo "========================================================"

# Restore services to the last release that passed health checks. Never restore
# the database dump automatically: doing so could discard valid new writes.
echo "[1/3] Restoring last successful application release ${RELEASE_TAG}..."
compose up -d --no-build --remove-orphans

# 2. Check if latest pre-deploy backup exists for DB restoration
LATEST_BACKUP=$(find "${ROOT_DIR}/backups" -name "wmax_db_*.sql.gz" -type f | sort -r | head -n 1 || true)

if [ -n "${LATEST_BACKUP}" ] && [ -f "${LATEST_BACKUP}" ]; then
  echo "[2/3] Pre-deploy backup exists: ${LATEST_BACKUP}"
  echo "      Database was not downgraded. Restore only through the documented recovery procedure."
else
  echo "[2/3] No pre-deploy SQL backup was found." >&2
fi

# Check readiness through both API and edge proxy.
echo "[3/3] Checking restored release health..."
healthy=false
for _ in $(seq 1 15); do
  if compose exec -T api curl -fsS http://127.0.0.1:8000/ready >/dev/null \
    && compose exec -T nginx wget -q -O /dev/null --spider http://127.0.0.1/healthz; then
    healthy=true
    break
  fi
  sleep 4
done
if [ "${healthy}" = true ]; then
  rm -f "${ROOT_DIR}/.deploy_state/candidate_release.txt" \
    "${ROOT_DIR}/.deploy_state/deploying_release.txt" \
    "${ROOT_DIR}/.deploy_state/release_started.txt"
  echo "[✓] Last successful release is healthy."
else
  echo "[-] Restored release failed health checks." >&2
  exit 1
fi

echo "[4/4] Rollback Procedure Completed."
echo "========================================================"
compose ps
echo "========================================================"

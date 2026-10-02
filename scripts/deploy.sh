#!/usr/bin/env bash
# WMAX release deployment script
# Role: Principal SRE / Release Engineer
# Usage: ./scripts/deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"
COMPOSE_PROJECT="${COMPOSE_PROJECT_NAME:-compose}"
RELEASE_TAG="${DEPLOY_RELEASE:-$(git -C "${ROOT_DIR}" rev-parse --short=12 HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
STATE_DIR="${ROOT_DIR}/.deploy_state"
LAST_SUCCESS="${STATE_DIR}/last_successful_release.txt"

compose() {
  RELEASE_TAG="${RELEASE_TAG}" docker compose -p "${COMPOSE_PROJECT}" --profile edge -f "${COMPOSE_FILE}" "$@"
}

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

if ! compose config --quiet; then
  echo "[-] Compose configuration is invalid; deployment stopped before touching the database." >&2
  exit 1
fi

# A fresh host has no running PostgreSQL yet. Start only the data services,
# then wait for them before taking the mandatory pre-deploy backup.
echo "[+] Ensuring PostgreSQL and Redis are running..."
compose up -d postgres redis
DATA_READY=false
for _ in $(seq 1 30); do
  if compose exec -T postgres pg_isready >/dev/null 2>&1 \
    && compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    DATA_READY=true
    break
  fi
  sleep 4
done
if [ "${DATA_READY}" != true ]; then
  echo "[-] PostgreSQL/Redis did not become ready; deployment stopped." >&2
  exit 1
fi

# 2. Automated Pre-Deployment Database Backup
echo "[1/6] Running automated safety backup..."
"${SCRIPT_DIR}/backup.sh" || {
  echo "[-] Pre-deployment backup failed. Halting deployment for safety." >&2
  exit 1
}

# 3. Build immutable, release-tagged images before changing live containers.
mkdir -p "${STATE_DIR}"
rm -f "${STATE_DIR}/candidate_release.txt"

# Adopt images from an existing unversioned Compose deployment as the initial
# rollback point before the first tagged release replaces its containers.
if [ ! -s "${LAST_SUCCESS}" ]; then
  BASELINE_TAG="baseline-${RELEASE_TAG:0:12}"
  BASELINE_READY=true
  for service in api web-doctor web-relative; do
    container_id="$(compose ps -q "${service}" | head -n 1)"
    if [ -z "${container_id}" ]; then
      BASELINE_READY=false
      break
    fi
    image_id="$(docker inspect --format '{{.Image}}' "${container_id}")"
    case "${service}" in
      api|nginx) image_name="wmax/${service}" ;;
      web-doctor|web-relative) image_name="wmax/${service}" ;;
    esac
    docker tag "${image_id}" "${image_name}:${BASELINE_TAG}"
  done
  if [ "${BASELINE_READY}" = true ]; then
    nginx_id="$(compose ps -q nginx | head -n 1)"
    if [ -n "${nginx_id}" ]; then
      nginx_image="$(docker inspect --format '{{.Image}}' "${nginx_id}")"
      docker tag "${nginx_image}" "wmax/nginx:${BASELINE_TAG}"
    fi
  else
    echo "[!] No complete running release was available to seed a rollback baseline."
    BASELINE_TAG=""
  fi
fi

printf '%s\n' "${RELEASE_TAG}" > "${STATE_DIR}/deploying_release.txt"

# 4. Build immutable images, then apply schema using the new release image.
echo "[2/6] Building release ${RELEASE_TAG}..."
compose build --pull
if [ -n "${BASELINE_TAG:-}" ] && ! docker image inspect "wmax/nginx:${BASELINE_TAG}" >/dev/null 2>&1; then
  docker tag "wmax/nginx:${RELEASE_TAG}" "wmax/nginx:${BASELINE_TAG}"
fi
if [ -n "${BASELINE_TAG:-}" ] && [ ! -s "${LAST_SUCCESS}" ]; then
  printf '%s\n' "${BASELINE_TAG}" > "${LAST_SUCCESS}"
  echo "[+] Existing release captured as rollback baseline ${BASELINE_TAG}."
fi
echo "[3/6] Applying database migrations..."
compose run --rm --no-deps -e RUN_MIGRATIONS=false api alembic upgrade head

# 5. Launch only after the schema upgrade succeeds.
echo "[4/6] Starting release ${RELEASE_TAG}..."
printf '%s\n' "${RELEASE_TAG}" > "${STATE_DIR}/release_started.txt"
compose up -d --remove-orphans --no-build

# 5. Deep Health Check Verification
echo "[5/6] Verifying system health and readiness..."
HEALTHY=false
RETRIES=15
WAIT_SEC=4

for ((i=1; i<=RETRIES; i++)); do
  echo "      Probe ${i}/${RETRIES}: checking /ready and /healthz..."
  
  API_READY=$(compose exec -T api curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ready || echo "000")
  NGINX_READY=$(compose exec -T nginx wget -q -O /dev/null --spider http://127.0.0.1/healthz && echo "200" || echo "000")

  if [ "${API_READY}" == "200" ] && [ "${NGINX_READY}" == "200" ]; then
    HEALTHY=true
    break
  fi
  sleep "${WAIT_SEC}"
done

if [ "${HEALTHY}" = false ]; then
  echo "[-] ERROR: Health check timed out. The deploy workflow will restore the last successful release." >&2
  exit 1
fi

# 6. Cleanup dangling resources
echo "[6/6] Pruning dangling images only..."
docker image prune -f >/dev/null 2>&1 || true

# External smoke test is the release acceptance gate. Keep the prior successful
# tag until that check calls mark_release_success.sh.
printf '%s\n' "${RELEASE_TAG}" > "${STATE_DIR}/candidate_release.txt"
rm -f "${STATE_DIR}/deploying_release.txt" "${STATE_DIR}/release_started.txt"

echo "[+] Internal health passed; waiting for external release acceptance."
echo "========================================================"
compose ps
echo "========================================================"

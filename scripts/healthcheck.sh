#!/usr/bin/env bash
# WMAX Comprehensive System Health Check Script
# Role: Principal SRE / Monitoring Engineer
# Usage: ./scripts/healthcheck.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker/compose/docker-compose.yml"

echo "========================================================"
echo "  WMAX Enterprise Health Check Audit: $(date)"
echo "========================================================"

FAILED=0

check_service() {
  local name="$1"
  local cmd="$2"

  echo -n "Checking ${name}... "
  if eval "${cmd}" >/dev/null 2>&1; then
    echo -e "\e[32m[PASS]\e[0m"
  else
    echo -e "\e[31m[FAIL]\e[0m"
    FAILED=$((FAILED + 1))
  fi
}

check_service "Nginx Gateway (/healthz)" "docker compose -f ${COMPOSE_FILE} exec -T nginx wget -q -O /dev/null --spider http://127.0.0.1/healthz"
check_service "FastAPI Liveness (/live)" "docker compose -f ${COMPOSE_FILE} exec -T api curl -s -f http://127.0.0.1:8000/live"
check_service "FastAPI Readiness (/ready)" "docker compose -f ${COMPOSE_FILE} exec -T api curl -s -f http://127.0.0.1:8000/ready"
check_service "PostgreSQL Database" "docker compose -f ${COMPOSE_FILE} exec -T postgres pg_isready"
check_service "Redis Cache" "docker compose -f ${COMPOSE_FILE} exec -T redis redis-cli ping"
check_service "Prometheus Server" "docker compose -f ${COMPOSE_FILE} exec -T prometheus wget -q -O /dev/null --spider http://127.0.0.1:9090/-/healthy"
check_service "Loki Log Engine" "docker compose -f ${COMPOSE_FILE} exec -T loki wget -q -O /dev/null --spider http://127.0.0.1:3100/ready"

echo "========================================================"
if [ $FAILED -eq 0 ]; then
  echo -e "\e[32m[✓] ALL ENTERPRISE SERVICES ARE HEALTHY!\e[0m"
  exit 0
else
  echo -e "\e[31m[-] CRITICAL: ${FAILED} service(s) failed health probes!\e[0m" >&2
  exit 1
fi

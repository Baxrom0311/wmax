#!/usr/bin/env bash
# WMAX — Quick launcher for Wear OS smartwatch simulator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================================"
echo "  WMAX — Smartwatch Streaming Simulator Launcher"
echo "========================================================"

PROFILE="${1:-healthy}"
INTERVAL="${2:-2.0}"
PATIENT_ID="${3:-11111111-1111-1111-1111-111111111111}"
BASE_URL="${4:-http://127.0.0.1:8000}"

echo "Profile:    $PROFILE (options: healthy, worsening, recovering)"
echo "Interval:   ${INTERVAL}s per 5-min window"
echo "Patient ID: $PATIENT_ID"
echo "Backend:    $BASE_URL"
echo "========================================================"
echo ""

python3 "$PROJECT_ROOT/scripts/watch_sim.py" \
    --profile "$PROFILE" \
    --interval "$INTERVAL" \
    --patient-id "$PATIENT_ID" \
    --base-url "$BASE_URL"

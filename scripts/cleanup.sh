#!/usr/bin/env bash
# WMAX Safe System Resource Cleanup Script
# Usage: ./scripts/cleanup.sh

set -euo pipefail

echo "========================================================"
echo "  WMAX Safe Maintenance Cleanup: $(date)"
echo "========================================================"

echo "[1/4] Pruning stopped containers..."
docker container prune -f

echo "[2/4] Pruning dangling and untagged images..."
docker image prune -f

echo "[3/4] Pruning dangling Docker build caches older than 7 days..."
docker builder prune --filter "until=168h" -f

echo "[4/4] Truncating oversized container log files > 100MB..."
find /var/lib/docker/containers/ -name "*-json.log" -size +100M -exec truncate -s 10M {} + 2>/dev/null || true

echo "========================================================"
echo "[✓] System Cleanup Completed Successfully."
df -h /
echo "========================================================"

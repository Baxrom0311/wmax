#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/backups}"

LATEST_BACKUP="$(find "${BACKUP_DIR}" -maxdepth 1 -name 'wmax_db_*.sql.gz' -type f -printf '%T@ %p\n' \
  | sort -nr | head -n 1 | cut -d' ' -f2-)"
if [ -z "${LATEST_BACKUP}" ]; then
  echo "[-] No database backup is available for restore verification." >&2
  exit 1
fi

echo "[+] Verifying isolated restore of ${LATEST_BACKUP}"
bash "${SCRIPT_DIR}/restore.sh" "${LATEST_BACKUP}" --test

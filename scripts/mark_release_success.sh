#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${ROOT_DIR}/.deploy_state"
CANDIDATE="${STATE_DIR}/candidate_release.txt"
LAST_SUCCESS="${STATE_DIR}/last_successful_release.txt"

if [ ! -s "${CANDIDATE}" ]; then
  echo "[-] No internally healthy candidate release is awaiting acceptance." >&2
  exit 1
fi

RELEASE_TAG="$(tr -d '[:space:]' < "${CANDIDATE}")"
if [ -n "${DEPLOY_RELEASE:-}" ] && [ "${DEPLOY_RELEASE}" != "${RELEASE_TAG}" ]; then
  echo "[-] Candidate ${RELEASE_TAG} does not match requested ${DEPLOY_RELEASE}." >&2
  exit 1
fi

mv "${CANDIDATE}" "${LAST_SUCCESS}"
echo "[✓] Release ${RELEASE_TAG} accepted and recorded as successful."

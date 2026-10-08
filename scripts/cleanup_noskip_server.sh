#!/usr/bin/env bash
set -Eeuo pipefail

# Back up NoSkipAI and its server-side data, then remove only NoSkipAI
# resources. The wildcard TLS certificate and shared logs are intentionally kept.
SERVER="${NOSKIP_SERVER:-root@159.89.101.106}"
SSH_KEY="${NOSKIP_SSH_KEY:-$HOME/docean}"
BACKUP_DIR="${NOSKIP_BACKUP_DIR:-$HOME/Backups/wmax-server-cleanup}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
STAMP="${NOSKIP_BACKUP_STAMP:-$STAMP}"
ARCHIVE="$BACKUP_DIR/noskip-server-$STAMP.tar.gz"
IMAGE_ARCHIVE="$BACKUP_DIR/noskip-backend-image-$STAMP.tar.gz"
ARCHIVE_PARTIAL="$ARCHIVE.partial"
IMAGE_PARTIAL="$IMAGE_ARCHIVE.partial"
QUIESCED=0
BACKUPS_VERIFIED=0

MODE="${1:-}"
if [[ "$MODE" != "--apply" && "$MODE" != "--resume" && "$MODE" != "--finish" ]]; then
  echo "Usage: $0 --apply | --resume | --finish"
  echo "--apply creates source/data and image backups before cleanup."
  echo "--resume refreshes source/data backup and uses an already saved image archive."
  echo "--finish verifies existing local backups and completes an interrupted cleanup."
  exit 2
fi
[[ -r "$SSH_KEY" ]] || { echo "SSH key is not readable: $SSH_KEY" >&2; exit 1; }
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=12)

restart_if_backup_fails() {
  status=$?
  if [[ "$QUIESCED" == 1 && "$BACKUPS_VERIFIED" == 0 ]]; then
    "${SSH[@]}" "$SERVER" 'systemctl start noskip-backend.service noskip-frontend.service' || true
  fi
  exit "$status"
}
trap restart_if_backup_fails EXIT

echo "Checking NoSkipAI scope on $SERVER..."
"${SSH[@]}" "$SERVER" "MODE=$MODE bash -s" <<'REMOTE_PREFLIGHT'
set -Eeuo pipefail
test "$(hostname -s)" = burxon || { echo "Unexpected host; refusing." >&2; exit 20; }
if [[ "$MODE" == "--finish" ]]; then
  docker image inspect noskip-backend:latest >/dev/null 2>&1 || true
  echo "Finish mode: continuing an interrupted, already backed-up cleanup."
else
test -d /var/www/noskip
test -f /var/www/noskip/noskipai-backend/data/noskipai.db
test -f /etc/nginx/sites-available/noskip
test -L /etc/nginx/sites-enabled/noskip
test -f /etc/nginx/sites-available/noskip.bak-1786543091
test -f /etc/systemd/system/noskip-backend.service
test -f /etc/systemd/system/noskip-frontend.service
test -f /usr/local/bin/noskip-db-backup.sh
test -f /var/spool/cron/crontabs/root
[[ "$(crontab -l -u root | grep -Fc /usr/local/bin/noskip-db-backup.sh || true)" == 1 ]]
nginx -t
docker image inspect noskip-backend:latest >/dev/null
if [[ -n "$(docker ps -a --filter ancestor=noskip-backend:latest --format '{{.ID}}')" ]]; then
  echo "A container still uses noskip-backend; refusing incomplete cleanup." >&2
  exit 21
fi
echo "Preflight passed. App, SQLite database, systemd, cron, Nginx and image are identified."
fi
REMOTE_PREFLIGHT

if [[ "$MODE" == "--finish" ]]; then
  echo "Verifying existing local backups before finishing cleanup..."
  (cd "$BACKUP_DIR" && shasum -a 256 -c "$(basename "$ARCHIVE").sha256")
  (cd "$BACKUP_DIR" && shasum -a 256 -c "$(basename "$IMAGE_ARCHIVE").sha256")
  gzip -t "$ARCHIVE"
  gzip -t "$IMAGE_ARCHIVE"
  BACKUPS_VERIFIED=1
else
echo "Stopping NoSkipAI while making the consistent backup..."
"${SSH[@]}" "$SERVER" 'systemctl stop noskip-backend.service noskip-frontend.service'
QUIESCED=1

echo "Copying source, SQLite database, daily backups and server configuration locally..."
"${SSH[@]}" "$SERVER" 'tar -czpf - --absolute-names \
  /var/www/noskip \
  /etc/nginx/sites-available/noskip \
  /etc/nginx/sites-available/noskip.bak-1786543091 \
  /etc/nginx/sites-enabled/noskip \
  /etc/systemd/system/noskip-backend.service \
  /etc/systemd/system/noskip-frontend.service \
  /etc/systemd/system/multi-user.target.wants/noskip-backend.service \
  /etc/systemd/system/multi-user.target.wants/noskip-frontend.service \
  /usr/local/bin/noskip-db-backup.sh \
  /var/log/noskip-db-backup.log \
  /var/spool/cron/crontabs/root \
  /root/.cache/pip/selfcheck \
  /root/.docker/buildx/refs/default/default \
  /var/lib/letsencrypt/backups/1787120425.5847824 \
  /var/lib/letsencrypt/backups/1787120426.693013 \
  /var/lib/letsencrypt/backups/1789786201.5510006 \
  /var/lib/letsencrypt/backups/1789786202.7634916' > "$ARCHIVE_PARTIAL"
chmod 600 "$ARCHIVE_PARTIAL"
gzip -t "$ARCHIVE_PARTIAL"
tar -tzf "$ARCHIVE_PARTIAL" >/dev/null
archive_hash="$(shasum -a 256 "$ARCHIVE_PARTIAL" | awk '{print $1}')"
printf "%s  %s\n" "$archive_hash" "$(basename "$ARCHIVE")" > "$ARCHIVE.sha256.partial"
chmod 600 "$ARCHIVE.sha256.partial"
mv -f "$ARCHIVE_PARTIAL" "$ARCHIVE"
mv -f "$ARCHIVE.sha256.partial" "$ARCHIVE.sha256"

if [[ "$MODE" == "--apply" ]]; then
  echo "Copying the tagged NoSkipAI container image locally..."
  "${SSH[@]}" "$SERVER" 'bash -o pipefail -c "docker save noskip-backend:latest | gzip -1"' > "$IMAGE_PARTIAL"
  chmod 600 "$IMAGE_PARTIAL"
  gzip -t "$IMAGE_PARTIAL"
  gzip -dc "$IMAGE_PARTIAL" | tar -tf - >/dev/null
  image_hash="$(shasum -a 256 "$IMAGE_PARTIAL" | awk '{print $1}')"
  printf "%s  %s\n" "$image_hash" "$(basename "$IMAGE_ARCHIVE")" > "$IMAGE_ARCHIVE.sha256.partial"
  chmod 600 "$IMAGE_ARCHIVE.sha256.partial"
  mv -f "$IMAGE_PARTIAL" "$IMAGE_ARCHIVE"
  mv -f "$IMAGE_ARCHIVE.sha256.partial" "$IMAGE_ARCHIVE.sha256"
else
  echo "Verifying previously saved NoSkipAI image archive..."
  [[ -s "$IMAGE_ARCHIVE" && -s "$IMAGE_ARCHIVE.sha256" ]]
  (cd "$BACKUP_DIR" && shasum -a 256 -c "$(basename "$IMAGE_ARCHIVE").sha256")
  gzip -t "$IMAGE_ARCHIVE"
  gzip -dc "$IMAGE_ARCHIVE" | tar -tf - >/dev/null
fi
(cd "$BACKUP_DIR" && shasum -a 256 -c "$(basename "$ARCHIVE").sha256")
BACKUPS_VERIFIED=1
fi

echo "Removing NoSkipAI services, site config, database/backups, cron and image..."
"${SSH[@]}" "$SERVER" 'bash -s' <<'REMOTE_CLEANUP'
set -Eeuo pipefail
for unit in noskip-backend.service noskip-frontend.service; do
  systemctl disable "$unit" 2>/dev/null || true
  systemctl stop "$unit" 2>/dev/null || true
done
rm -f -- \
  /etc/systemd/system/noskip-backend.service \
  /etc/systemd/system/noskip-frontend.service \
  /etc/systemd/system/multi-user.target.wants/noskip-backend.service \
  /etc/systemd/system/multi-user.target.wants/noskip-frontend.service
systemctl daemon-reload

cron_tmp=$(mktemp)
crontab -l -u root | awk 'index($0, "/usr/local/bin/noskip-db-backup.sh") == 0' > "$cron_tmp"
crontab -u root "$cron_tmp"
rm -f "$cron_tmp"

rm -f -- /etc/nginx/sites-enabled/noskip \
  /etc/nginx/sites-available/noskip \
  /etc/nginx/sites-available/noskip.bak-1786543091
rm -f -- /usr/local/bin/noskip-db-backup.sh /var/log/noskip-db-backup.log
rm -rf -- /var/www/noskip

python3 - <<'PY'
import json
from pathlib import Path

for cache_file in Path("/root/.cache/pip/selfcheck").glob("*"):
    if cache_file.is_file() and "/var/www/noskip" in cache_file.read_text(errors="ignore"):
        cache_file.unlink()

refs = Path("/root/.docker/buildx/refs")
for ref_file in refs.rglob("*"):
    if not ref_file.is_file():
        continue
    try:
        metadata = json.loads(ref_file.read_text())
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        continue
    if not isinstance(metadata, dict):
        continue
    local_path = str(metadata.get("LocalPath", ""))
    if local_path == "/var/www/noskip" or local_path.startswith("/var/www/noskip/"):
        ref_file.unlink()

root = Path("/var/lib/letsencrypt/backups")
needles = ("noskip.bakhromdev.uz", "/var/www/noskip", "noskip-backend", "noskip-frontend", "noskip-db-backup", "noskipai")
for directory in root.iterdir():
    if not directory.is_dir():
        continue
    for path in list(directory.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith("noskip_"):
            path.unlink()
            continue
        if path.name not in {"CHANGES_SINCE", "FILEPATHS"}:
            continue
        try:
            lines = path.read_text().splitlines(keepends=True)
        except UnicodeDecodeError:
            continue
        kept = [line for line in lines if not any(needle in line for needle in needles)]
        if kept != lines:
            path.write_text("".join(kept))
PY

docker image rm noskip-backend:latest
nginx -t
systemctl reload nginx
if systemctl is-enabled noskip-backend.service noskip-frontend.service >/dev/null 2>&1; then
  echo "A NoSkipAI unit remains enabled." >&2
  exit 31
fi
if nginx -T 2>&1 | grep -Fq "noskip.bakhromdev.uz"; then
  echo "NoSkip domain remains in active nginx config." >&2
  exit 32
fi
if crontab -l -u root | grep -Fq "/usr/local/bin/noskip-db-backup.sh"; then
  echo "NoSkip backup cron remains." >&2
  exit 33
fi
for p in /var/www/noskip /etc/nginx/sites-available/noskip \
  /etc/nginx/sites-enabled/noskip /etc/systemd/system/noskip-backend.service \
  /etc/systemd/system/noskip-frontend.service /usr/local/bin/noskip-db-backup.sh; do
  [[ ! -e "$p" ]] || { echo "NoSkip artifact remains: $p" >&2; exit 34; }
done
if docker image inspect noskip-backend:latest >/dev/null 2>&1; then
  echo "NoSkip image remains." >&2
  exit 35
fi
echo "NoSkipAI resources removed; shared wildcard TLS and other apps preserved."
REMOTE_CLEANUP

QUIESCED=0
trap - EXIT
echo "Verified local backups:"
echo "  $ARCHIVE"
echo "  $IMAGE_ARCHIVE"

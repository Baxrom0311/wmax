#!/usr/bin/env bash
set -Eeuo pipefail

# Back up and remove only the server-side signal.boos.uz TLS lineage and its
# Certbot history fragments. The unrelated WMAX/NoSkip services are preserved.
SERVER="${SIGNAL_SERVER:-root@159.89.101.106}"
SSH_KEY="${SIGNAL_SSH_KEY:-$HOME/docean}"
BACKUP_DIR="${SIGNAL_BACKUP_DIR:-$HOME/Backups/wmax-server-cleanup}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$BACKUP_DIR/signal.boos.uz-$STAMP.tar.gz"

if [[ "${1:-}" != "--apply" ]]; then
  echo "Usage: $0 --apply"
  echo "Creates and verifies a private local archive, then removes the domain TLS files."
  exit 2
fi

if [[ ! -r "$SSH_KEY" ]]; then
  echo "SSH key is not readable: $SSH_KEY" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=12)

echo "Checking server scope and active references on $SERVER..."
"${SSH[@]}" "$SERVER" 'bash -s' <<'REMOTE_PREFLIGHT'
set -Eeuo pipefail
test "$(hostname -s)" = burxon || { echo "Unexpected host; refusing." >&2; exit 20; }
if nginx -T 2>&1 | grep -Fq "signal.boos.uz"; then
  echo "An active nginx config still references signal.boos.uz; refusing cleanup." >&2
  exit 21
fi
if ss -lnt 2>/dev/null | grep -Eq "(^|[[:space:]])[^[:space:]]*:8002([[:space:]]|$)"; then
  echo "Port 8002 is listening; refusing to remove any service data." >&2
  exit 22
fi
if [[ -e /opt/trust-signal ]]; then
  echo "/opt/trust-signal exists and needs a fresh content review; refusing." >&2
  exit 23
fi
for p in \
  /etc/letsencrypt/renewal/signal.boos.uz.conf \
  /etc/letsencrypt/live/signal.boos.uz \
  /etc/letsencrypt/archive/signal.boos.uz; do
  [[ -e "$p" ]] || { echo "Expected domain artifact missing: $p" >&2; exit 24; }
done
echo "Preflight passed. Active domain vhost/app not found; TLS lineage exists."
REMOTE_PREFLIGHT

echo "Creating local backup: $ARCHIVE"
"${SSH[@]}" "$SERVER" 'tar -czf - --absolute-names \
  /etc/letsencrypt/renewal/signal.boos.uz.conf \
  /etc/letsencrypt/live/signal.boos.uz \
  /etc/letsencrypt/archive/signal.boos.uz \
  /var/lib/letsencrypt/backups/1787120425.5847824 \
  /var/lib/letsencrypt/backups/1787120426.693013 \
  /var/lib/letsencrypt/backups/1789786201.5510006 \
  /var/lib/letsencrypt/backups/1789786202.7634916 \
  /root/.cache/pip/selfcheck/96a74de8593fa7a0f3f623f0110f332584da93ccc155a69f3b555503' > "$ARCHIVE"
chmod 600 "$ARCHIVE"
gzip -t "$ARCHIVE"
tar -tzf "$ARCHIVE" >/dev/null
shasum -a 256 "$ARCHIVE" | tee "$ARCHIVE.sha256"
chmod 600 "$ARCHIVE.sha256"

echo "Removing only the signal.boos.uz TLS lineage and historical nginx fragments..."
"${SSH[@]}" "$SERVER" 'bash -s' <<'REMOTE_CLEANUP'
set -Eeuo pipefail
rm -rf -- /etc/letsencrypt/live/signal.boos.uz /etc/letsencrypt/archive/signal.boos.uz
rm -f -- /etc/letsencrypt/renewal/signal.boos.uz.conf
python3 - <<'PY'
from pathlib import Path

root = Path("/var/lib/letsencrypt/backups")
needles = ("signal.boos.uz", "trust-signal")
for directory in root.iterdir():
    if not directory.is_dir():
        continue
    # Certbot snapshots contain other vhosts too, so preserve the snapshots
    # and edit only the Trust Signal fragment and its path/history references.
    for path in list(directory.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith("trust-signal_"):
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

cache_dir = Path("/root/.cache/pip/selfcheck")
for pip_cache in cache_dir.glob("*"):
    if pip_cache.is_file() and "/opt/trust-signal/venv" in pip_cache.read_text(errors="ignore"):
        pip_cache.unlink()
PY
if nginx -T 2>&1 | grep -Fq "signal.boos.uz"; then
  echo "Domain reference remains in active nginx configuration." >&2
  exit 31
fi
if grep -RIl --exclude-dir=pgdata --exclude=*.log --exclude=*.pyc \
  -E "signal\.boos\.uz|trust-signal" \
  /etc/nginx /etc/letsencrypt /var/lib/letsencrypt/backups /etc/systemd /etc/cron* /var/spool/cron /opt /root/.cache/pip/selfcheck 2>/dev/null \
  | grep -v '^/opt/wmax/'; then
  echo "Unexpected server-side domain reference remains; inspect before further cleanup." >&2
  exit 32
fi
nginx -t
echo "Server-side domain artifacts removed; unrelated services/configs preserved."
REMOTE_CLEANUP

echo "Backup retained locally at: $ARCHIVE"

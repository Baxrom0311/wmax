# Server inventory and Signal domain cleanup

Inspection date: 2026-10-07 UTC  
Host: `burxon` (`159.89.101.106`, Ubuntu 22.04.5, kernel 5.15)  
Scope: read-only inventory, then removal of the explicitly requested `signal.boos.uz` and NoSkipAI server-side resources after verified local archives.

## What was on the server

- Root disk: 25 GB total, about 19 GB used (78%), 5.4 GB available at inspection.
- `/opt/wmax` (about 60 MB): current WMAX source/configuration, Docker Compose setup, a `pgdata` directory, and a production `.env` file. Secret values were not read or copied into this report.
- `/opt/wmax-backups` (about 812 KB): dated application backups and a compressed WMAX PostgreSQL dump.
- Docker: WMAX API, notifier, PostgreSQL 16, doctor web, relative web, and Redis containers; one stale container was in `Created` state. WMAX databases were `postgres` (~7.5 MB) and `wmax` (~13 MB).
- Host Nginx and Certbot were active. Nginx served `wmax.boos.uz`; a separate `noskip.bakhromdev.uz` application used host systemd services on ports 3000 and 8000.
- `/var/www/noskip` (about 317 MB): separate NoSkipAI frontend/backend and daily compressed SQLite backups. Host PostgreSQL 14 had only the default `postgres` database (~8.5 MB).
- No `/opt/trust-signal` project directory, active `signal.boos.uz` Nginx vhost, systemd service, database, or listener on port 8002 was present. Its former Certbot snapshots show that the old vhost proxied to port 8002.
- The only live Signal resources were its Let's Encrypt renewal file and certificate/key lineage. Certbot snapshots also held old Signal vhost fragments alongside unrelated WMAX and other-site configurations.

## Completed cleanup

The domain renewal config, live/archive certificate directories, and exact Signal vhost fragments/references in Certbot's historical snapshots were removed. Shared snapshots were kept, with only Signal-specific fragments and path/history lines removed. The stale pip self-check entry referring to `/opt/trust-signal/venv` was also removed. No active Nginx configuration refers to `signal.boos.uz`; `nginx -t` passed and Nginx remains active.

The local backup is [signal.boos.uz-20261007T063228Z.tar.gz](/Users/baxrom/Backups/wmax-server-cleanup/signal.boos.uz-20261007T063228Z.tar.gz), with SHA-256 `82d8640e90b8626998a69feb2fa50ec06b46f9fd917cdf604a72b7de158c1b7f`. The archive includes the TLS private key and whole affected Certbot snapshot directories, which also contain historical config for other sites. The backup directory is mode 700 and the archive/checksum are mode 600. Keep this backup private.

This was server-side cleanup only. DNS is managed outside this server and was not changed; the public certificate was not revoked at Let's Encrypt. No WMAX, NoSkipAI, host PostgreSQL, or Docker database data was deleted.

## Operational note

During the Signal cleanup check, the WMAX API container was repeatedly restarting. On the later NoSkip cleanup check it was healthy, so that earlier outage appears to have recovered; no WMAX service was changed as part of either cleanup.

## NoSkipAI cleanup

The user later requested removal of the separate NoSkipAI deployment. Before removal, both NoSkip systemd services were stopped to make a consistent backup. The local backup contains the complete `/var/www/noskip` tree (including `.env`, the live 405,504-byte SQLite database, and all 15 daily SQLite backups), its Nginx/systemd/cron/Certbot configuration, and Docker build references. A separate archive contains the `noskip-backend:latest` image.

- Source/config/data archive: [noskip-server-20261007T093119Z.tar.gz](/Users/baxrom/Backups/wmax-server-cleanup/noskip-server-20261007T093119Z.tar.gz), 73 MB, SHA-256 `cd0230ccd0308cfc9e73cff49fd2e14747468193c51c0615ac07b16f7604eb97`.
- Docker image archive: [noskip-backend-image-20261007T093119Z.tar.gz](/Users/baxrom/Backups/wmax-server-cleanup/noskip-backend-image-20261007T093119Z.tar.gz), 207 MB, SHA-256 `092c9e7b51e9f8d8e99194639e5209fe2e3da977054ab98e9a06b103ec7c66b7`.

Both archives passed gzip/tar integrity checks and SHA-256 verification. The backup directory is mode 700; archives and checksums are mode 600. They contain application secrets and patient records; keep them private.

Removed from the server: `/var/www/noskip`, NoSkip systemd units, the Nginx site and its old copy, its DB-backup cron/script/log, `noskip-backend:latest`, NoSkip pip/buildx metadata, and NoSkip fragments from Certbot snapshots. Nginx syntax passed after reload, ports 3000/8000 no longer listen, and WMAX/Redis/PostgreSQL containers remain running. The `*.bakhromdev.uz` origin certificate was preserved because it is shared with other hostnames. DNS was not changed because it is managed externally.

Shared systemd journal, syslog, and Nginx logs remain. They contain mixed records for multiple services; the server's Nginx access format does not record the hostname, so selectively deleting NoSkip request lines would risk damaging unrelated audit logs. NoSkip app files, database, scheduled backups, and service-specific backup log have been removed.

The corrected cleanup script supports `--apply`, `--resume`, and `--finish` to recover safely from partial cleanup: [cleanup_noskip_server.sh](/Users/baxrom/ish_full/wmax/scripts/cleanup_noskip_server.sh).

#!/bin/sh
# Container entrypoint: schema first, then the process.
#
# Migrations run here rather than from a Postgres initdb mount, because initdb
# scripts only ever run on a *brand new* volume — an existing deployment would
# silently keep its old schema. `alembic upgrade head` is idempotent and applies
# to both fresh and existing databases.
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "[entrypoint] Applying database migrations..."
  cd /srv/backend && alembic upgrade head
  echo "[entrypoint] Migrations applied."
fi

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  echo "[entrypoint] Seeding demo data..."
  cd /srv && python scripts/seed_demo.py || echo "[entrypoint] Seeding skipped/failed (non-fatal)."
fi

exec "$@"

# WMAX

Remote patient monitoring: a smartwatch streams 5-minute vitals windows, the
backend scores them against each patient's baseline, and clinicians, family
caregivers and a Telegram bot are alerted when a patient deteriorates.

| Folder | What it is |
|---|---|
| `backend/` | FastAPI API, signal pipeline, AI prognosis, SOS, billing, workers (`backend/app`), algorithms (`backend/algo`), Alembic migrations |
| `contracts/` | OpenAPI spec and shared types/time windows |
| `notifier/` | Telegram alert delivery and bot (runs from the backend image) |
| `web/` | Single React + shadcn/ui web app: landing, Pitch Day (`/aifu`), clinic workstation and SOS dispatcher (`/doctor`), caregiver portal / Telegram Mini App (`/r`) |
| `mobile_flutter/` | Caregiver phone app and Wear OS watch runtime |
| `landing/` | Static marketing page |
| `docker/`, `scripts/` | Production compose stack, nginx, monitoring, deploy/backup scripts |
| `docs/` | Product ideology, architecture, SDLC |

## Run the checks locally

```bash
# Backend + algorithms + notifier tests
pip install -r backend/requirements.txt -r backend/algo/requirements.txt -r notifier/requirements.txt
pip install pytest-asyncio aiosqlite httpx
ENV=testing PYTHONPATH=.:backend:contracts pytest -q backend/app/tests backend/algo/tests notifier/tests

# Web app
(cd web && npm ci && npm run lint && npm run build)

# Mobile
(cd mobile_flutter && flutter pub get && flutter analyze && flutter test)
```

## Deploy

`docker/compose/docker-compose.yml` is the only compose stack. CI deploys with
`scripts/deploy.sh`; copy `.env.production.example` to `.env` first. The API
refuses to start in production with placeholder secrets
(`backend/app/core/config.py`).

See `AGENTS.md` for the code map and the product rules every change must keep.

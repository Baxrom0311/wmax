# WMAX repository guide

WMAX is a remote patient monitoring prototype for Uzbekistan. Read
`docs/IDEOLOGY.md`, `docs/ARCHITECTURE.md`, and `docs/SDLC.md` before changing
clinical behavior, authorization, data contracts, or release procedures.
The ideology is the intended product policy; inspect code to establish what
actually works.

## Repository map

- `backend/app/main.py`: FastAPI application and worker lifecycle.
- `backend/app/domain/`: deterministic product rules, without transport or DB IO.
- `backend/app/services/`, `repositories/`, `api/`: business workflows, persistence,
  and HTTP boundaries respectively.
- `backend/app/models/schema.py`: ORM models; individual model files largely
  re-export these classes. `backend/alembic/`: PostgreSQL migrations.
- `backend/algo/`, `contracts/`: physiological signal calculations, shared types,
  time windows, and OpenAPI contract.
- `notifier/`: Telegram delivery and bot administration.
- `web-doctor/`, `web-relative/`: separate React/TypeScript/Vite applications.
- `mobile_flutter/`: Flutter UI with Android phone/Wear OS and iOS native bridges.
- `landing/`: static marketing page.
- `docker/compose/docker-compose.yml`, `scripts/`: canonical release tooling
  (CI deploys with `scripts/deploy.sh`; root `deploy.sh` is the manual
  rsync deploy to the same compose stack).
- Never commit `backups/`, database dumps or `.env` files (see `.gitignore`).

## Product invariants

- Report measurements and uncertainty. Do not present heuristic percentages as
  clinically validated probabilities or promise ambulance dispatch without proof.
- Patients are not owned by tenants. Clinical memberships and family access are
  different relationships; derive authorization from current relationships.
- Never put SOS or critical alerts behind a paywall.
- A clinical task requires an eligible, explicitly responsible assignee.
- Missing/unreliable data must not imply healthy status.
- Attribute device data by the complete historical assignment interval.
- Persist data before ACK; use idempotency and durable delivery/retry state.
- Consent revocation and deceased status must affect downstream workflows.
- Do not treat a pure domain function's unit test as proof that the runtime
  workflow invokes that function.

## Verification

From repository root, use an isolated test environment:

```sh
ENV=testing ENABLE_WORKERS=false .venv/bin/python -m pytest -q backend/app/tests backend/algo/tests notifier/tests
ruff check backend/ notifier/ contracts/timewin.py
```

Each web application has `npm run lint` and `npm run build`.
For mobile, run `flutter analyze --fatal-infos` and targeted offline widget tests.
Compile Android with `flutter build apk --debug --flavor phone` and
`flutter build apk --debug --flavor wear`.

**Do not run unfiltered `flutter test`: `mobile_flutter/test/api_live_test.dart`
hardcodes a public server and creates an SOS event.** Inspect integration tests
before executing them; use an explicitly disposable server and synthetic users.
This is also an unresolved problem in the existing CI commands.

Database validation needs a disposable PostgreSQL database: `alembic upgrade
head`, `alembic check`, then downgrade/upgrade only in that disposable database.
Production targets PostgreSQL 16. SQLite/mocks do not validate RLS, partitions,
PostgreSQL constraints, or actual asyncpg SQL syntax.

## Working conventions

- Preserve existing uncommitted changes; review the current worktree, not just HEAD.
- Keep fixes scoped to a complete user workflow with a regression test for the
  actual failure. Avoid broad rewrites based only on target architecture.
- Never use live patient data, external SMS, Telegram, payment or SOS delivery in
  routine tests. Do not print secrets or patient records in test output.
- Use a restricted application database role when testing tenant isolation.
- Record skipped checks and missing device/clinical validation explicitly.
- Follow `docs/SDLC.md` for immutable releases, backup, rollback, and human review.
  An audit request is not an instruction to deploy or reset a database.

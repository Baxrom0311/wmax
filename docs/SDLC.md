# WMAX SDLC

This document is the operational source of truth for changes from proposal to
production. `ARCHITECTURE.md` defines product and system design; this document
defines how that design is changed, verified, released, and recovered.

## Change lifecycle

1. **Specify**: describe user/clinical impact, affected API/data contracts, the
   applicable `IDEOLOGY.md` rules, migration/rollback implications, and how the
   change will be observed. Clinical behavior changes require an explicit
   clinical owner review; never infer a diagnosis from an engineering test.
2. **Implement**: keep domain decisions deterministic and outside transport or
   persistence layers. Add a migration for schema changes and preserve old/new
   application compatibility while a release is rolling out.
3. **Review**: require a pull request, human review, and all applicable CI
   checks. Do not deploy directly from a local working tree. Do not merge while
   required checks are red or skipped.
4. **Release**: deploy the exact commit SHA as an immutable image tag. Back up
   the database, build images, apply the migration once, start the release, and
   verify API readiness, edge health, and the public health URL.
5. **Observe**: check service health, error rate, migration outcome, ingest
   acceptance/rejection, queue lag, and alert delivery after release. Record
   incidents and follow-up work.

## Engineering principles

These rules resolve day-to-day implementation tradeoffs. `IDEOLOGY.md` remains
the product authority and `ARCHITECTURE.md` the target design; neither is a
reason to replace working code or data in one broad rewrite.

1. **Ship one complete slice at a time.** Choose a user-visible or operational
   outcome, trace its API, domain rule, persistence, client, and failure path,
   then finish that slice before starting unrelated features. Prefer a small
   deployable change over a large phase that stays unfinished.
2. **Make the rule easy to find.** Each business decision has one clear owner in
   the domain/service layer. Keep endpoints and repositories unsurprising:
   transport validates and delegates; persistence reads/writes; neither hides
   product policy. Refactor only as part of a concrete behavior change.
3. **Optimize for correct, readable behavior, not test count.** Tests protect
   clinical, authorization, data-integrity, and recovery invariants. Avoid
   duplicate tests and mock-heavy checks that merely restate implementation.
   A focused explanation and a clear function are preferable to abstractions
   introduced only to make a test pass.
4. **Persist before notifying.** For device ingest and asynchronous work, make
   accepted data durable and idempotent before acknowledging it. Queues may
   retry; consumers must tolerate duplicate delivery. WebSocket/push is a
   low-latency notification or view-update channel, never the only copy of a
   measurement or command. Reconnects must recover from persisted state/cursors.
5. **Treat every boundary as untrusted.** Derive patient and tenant scope from
   authenticated server-side relationships, not request bodies. Validate
   ownership, consent, freshness, units, and provenance before data affects a
   clinical workflow. Fail closed when scope or provenance is ambiguous.
6. **Change data structures in compatible steps.** Audit existing rows and
   consumers first; use expand, backfill/verify, switch reads/writes, then
   contract. Do not delete legacy code, tables, or records solely because the
   target architecture omits them.
7. **Make failure visible and recoverable.** Give every important async step a
   durable status, bounded retry policy, and actionable structured log/metric.
   A green HTTP response is not proof that downstream work completed; expose
   accepted, rejected, and pending outcomes distinctly.
8. **Spend effort by risk and evidence.** Prioritize data loss, privacy,
   incorrect clinical escalation, and inability to recover above cosmetic
   improvements or speculative algorithms. Add a new signal/algorithm only
   when its inputs, limitations, validation evidence, and operational response
   are defined.

Before implementation, the change proposal should state: the outcome, the
affected data/API boundary, the main failure mode, and how an operator or user
will know it worked. If any answer is unknown, narrow the scope or resolve that
unknown before widening the change.

## Required CI gates

- Python: mandatory `ruff check` and pytest for `backend/app/tests`,
  `backend/algo/tests`, and `notifier/tests`.
- Database: PostgreSQL 16 migration upgrade, `alembic check`, destructive
  downgrade to base, and upgrade to head on a disposable CI database. This only
  exercises migration mechanics; it is not a production rollback procedure.
- Web: install from lockfiles, lint, and production build for both web apps.
- Flutter: dependency resolution, `flutter analyze --fatal-infos`, Flutter
  tests, and debug builds for Android `phone` and `wear` flavors. iOS release
  builds/signing are a separate macOS release check.
- Containers: build each image used by the production Compose stack.
- Contract: API contract tests must detect missing/extra operations and schema
  drift. OpenAPI changes require corresponding client/schema updates.

No CI command may use `|| true` to hide a required check. A documented,
time-bounded exception must name an owner and an issue; it is not a green gate.

## Database and release safety

- Migrations run once as a deploy step, not concurrently in each API replica.
- Migrations must be transactional where PostgreSQL permits it and must be
  backward-compatible with the currently deployed app. Use expand/migrate/
  contract for destructive changes; contract only after old app versions are
  gone and the backup/restore path has been verified.
- Never automatically restore a production database during application
  rollback. A restore can discard valid writes. App rollback uses the last
  successful immutable image tag; database recovery is a separately approved
  incident operation.
- Every deploy takes a database dump, checks gzip integrity, and records a
  checksum. Backup monitoring must alert on missing/failed daily backups.
- The server runs `scripts/verify_backup_restore.sh` monthly. It restores the
  newest dump into a temporary PostgreSQL container with no network or published
  ports, with bounded CPU/memory, and reports recovered key-table counts to the
  systemd journal. Tune `RESTORE_TEST_MEMORY` for large production databases.
- Keep the previous successful release images until the next release has
  passed health checks. Retention cleanup must not remove the rollback target.

## Deploy and rollback

Production deploy is allowed only from the protected `main` branch after the
same commit passes required CI. The deploy uses `DEPLOY_RELEASE=<full commit
SHA>`, the existing Compose project name (`compose` by default), and the `edge`
profile. Promote no source changes between validation and deployment. Secrets are provisioned on the
server/GitHub environment, never committed or copied by `rsync`.

The Enterprise workflow is canonical for `main` and `develop` pushes and `main`
pull requests. The legacy CI workflow remains for `master` pushes and PRs into
`develop` or `master`, avoiding duplicate full client builds on canonical
branches.

Repository administrators must configure `main` branch protection to require
the Enterprise workflow's `Code Quality & Static Analysis`, `Unit & Integration
Tests`, `Web and Flutter Validation`, `iOS Compile Validation`, `PostgreSQL
Migration Gate`, and `Build & Validate Containers` checks. GitHub branch rules
are repository settings and cannot be enforced by workflow YAML alone.
Configure the verified SSH host public key in the repository variable
`SSH_KNOWN_HOSTS`; deployment refuses to trust a key fetched during the
connection itself.

On failed migration, do not start the new application. On failed readiness or
public smoke check, recreate the last successful image tags and verify health.
Do not run Alembic downgrade or restore a dump automatically. If schema changes
are not backward-compatible, stop rollout and use the documented database
incident procedure with an explicit data-loss assessment.
On an initial install without a previous release, failed candidate application
services are stopped while PostgreSQL/Redis and their data are preserved.

## Verification and ownership

Before merging, the author confirms the changed behavior and failure paths;
reviewers check authorization scope, idempotency, data provenance, observability,
and migration compatibility. Tests are evidence for behavior, not a substitute
for readable domain logic or review. Avoid duplicative tests that assert
implementation details without protecting a user-visible or data-integrity
invariant.

Release owner: maintainer on duty. Clinical rule owner: designated clinical
reviewer. Database recovery approver: maintainer plus data owner. These roles
must be assigned before production launch; missing ownership blocks release.

## Current repository notes

- Run backend tests explicitly as
  `pytest -q backend/app/tests backend/algo/tests notifier/tests`;
  pytest's default discovery is intentionally not relied upon by CI.
- Monitoring services are optional Compose profile `monitoring`; edge health
  checks must not require them unless that profile is deployed.
- `web-relative` remains a separately deployed app until a product/API migration
  is implemented and reviewed; architecture intent alone does not remove it.
- Wear OS and phone app code share `mobile_flutter`; native platform bridges
  still require device-level validation for Health Connect/HealthKit behavior.

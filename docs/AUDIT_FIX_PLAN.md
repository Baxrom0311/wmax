# Audit remediation — 2026-10-16

Scope: the 13 findings in REVIEW_2026-10-16.md. Preserve existing records and
migration history. No deployment or live messaging is part of this change.

Outcomes: current relationship/territory/role authorization on HTTP and live
events; missing data remains unknown; consent and death stop active workflows;
SOS and alerts enter durable recipient-specific delivery with visible failures;
honest emergency copy and reproducible Android builds.

Policy: IDEOLOGY B3–B6, D1–D5, F2, I2, J2. The main failure modes are disclosure,
false healthy status, unattended signals and loss of retry state. Regression
tests must exercise service/API paths and persisted state, not just pure rules.

Schema changes are additive (SOS lifecycle and durable delivery fields), with
defaults for legacy rows. Autogenerate a migration against an isolated database;
check upgrade/model drift and downgrade/upgrade there only. Application rollback
keeps the expanded columns; production database restore is not automatic.

Operators observe pending/delivered/failed attempts and clinical tasks in stored
state. Provider credentials and external acceptance remain deployment prerequisites;
automated tests use fakes. Clinical-owner and human release review required by
SDLC remain release gates, not evidence supplied by engineering tests.

## Status — 2026-10-16 (uncommitted, not deployed)

| # | Finding | Change | Regression |
|---|---|---|---|
| 1 | SOS delivery | SOS persisted with lifecycle columns; one durable `notifications` row per responsible staff member and consented caregiver, queued in the SOS transaction; notifier delivers Telegram → SMS with ACK button, retries and logs every attempt; snapshot enrichment can no longer block an SOS | `test_pg_workflows::test_sos_via_api_*`, `test_sos_without_any_recipient_*` |
| 2 | Foreign-clinic billing | current patient access check on subscription GET/checkout | `test_pg_authorization::test_foreign_clinic_nurse_*` |
| 3 | Empty reading → green | only worn windows with a measurement are evidence (pipeline, silence worker, worklist, detail, caregiver views) | `test_reading_without_values_*`, `test_silence_*` |
| 4 | Consent revocation | membership closed, tasks cancelled, both ingest paths and workers share `monitoring_policy`, deliveries re-authorized per attempt | `test_clinical_consent_revocation_*` |
| 5 | Stale WebSocket scope | scope reloaded from DB every 10 s; socket closes on expiry, removal or demotion | `test_pg_realtime` |
| 6 | Role per clinic | `require_role` narrows to clinics where the current membership holds the role; refresh recomputes | `test_doctor_role_in_one_clinic_*`, `test_demoted_*`, `test_refresh_*` |
| 7 | Mahalla scope | one rule (`clinical_scope`) for worklist, detail, realtime, task assignee and staff notifications; territory API; creators place patients in own mahalla | `test_nurse_sees_only_*`, `test_head_doctor_assigns_*`, `test_nurse_creates_*` |
| 8 | Quality → task kind | `domain.quality.assess` + `task_kind` at runtime; technical tasks have no deadline; `unassigned` persisted and retried | `test_reliable_red_*`, `test_unreliable_red_*`, `test_alert_without_responsible_*` |
| 9 | Partial delivery | per-recipient rows and state; one success closes nobody else | `test_sos_via_api_*`, `test_telegram_ack_*` |
| 10 | Production SMS | Eskiz adapter (cached token, re-login, DLR status); production config refuses eskiz without credentials | `test_sms_auth` |
| 11 | 103 promise | landing, doctor SOS UI, mobile confirmation state that 103 is not called automatically; SOS listed as free | build/lint only |
| 12 | Deceased | `lifecycle_service.mark_deceased`: stops tasks (incl. overdue) and deliveries, keeps family history 90 days, creates device-return task | `test_deceased_lifecycle` |
| 13 | Android JVM target | Kotlin `jvmTarget` 17 | phone and wear debug APK built; fails without the fix |

Operational prerequisites before release: assign mahallas to every doctor and
nurse (`PUT /api/v1/tenants/{tenant_id}/members/{account_id}/territories`) and
a primary address mahalla to every patient, otherwise they see no patients and
alerts stay `unassigned`; Eskiz credentials and approved message templates;
Telegram bot token for the notifier. Still open: `PatientContextBuilder` and the
profile admissions API read columns that no migration creates (SOS now degrades
to a minimal snapshot); RLS under a restricted application role was not tested.

# WMAX audit inventari — 2026-10-07

Bu ro‘yxat barcha faylni 100% semantik tekshirildi degani emas. “Mazmuniy ko‘rik”
tegishli funksiyalar/oqimlar o‘qilganini anglatadi, butun fayldagi har qatorni emas.
Qolgan fayllar ochiq belgilangan. Lockfile/platform scaffold va binary assetlar
ishlab chiqarish xavfsizligi isboti hisoblanmaydi. Git tomonidan kuzatiladigan va
ignore qilinmagan yangi fayllar; node_modules, .venv, build, cache kiritilmagan.

Text fayllar: 465; binary assetlar: 44; text satrlari (lockfilelar bilan): 78484; Python AST muvaffaqiyatli: 214; AST xato: 0.

| Fayl | Satr/tur | Ko‘rik dalili va chegarasi |
|---|---:|---|
| `.dockerignore` | 51 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `.env.example` | 61 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `.env.production.example` | 72 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `.github/workflows/ci.yml` | 196 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `.github/workflows/enterprise-ci-cd.yml` | 314 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `.gitignore` | 20 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `Caddyfile` | 25 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `backend/Dockerfile` | 40 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `backend/alembic.ini` | 52 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `backend/alembic/env.py` | 127 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/alembic/script.py.mako` | 28 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `backend/alembic/versions/20260922_0359_c1057cb46015_architecture_base_schema.py` | 912 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/alembic/versions/20260930_2300_health_data_streams.py` | 190 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `backend/alembic/versions/20261001_1200_device_enrollment_claim.py` | 49 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `backend/algo/__init__.py` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/algo/anomaly.py` | 76 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/algo/baseline.py` | 80 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/algo/requirements.txt` | 6 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `backend/algo/signal.py` | 226 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 3 |
| `backend/algo/tests/test_algo.py` | 185 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/algo/tests/test_v2_signal.py` | 87 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/algo/trend.py` | 52 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/__init__.py` | 0 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/ai/__init__.py` | 7 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/ai/breaker.py` | 66 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/ai/cache.py` | 97 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/ai/clinical_ai.py` | 354 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 4 |
| `backend/app/ai/deepseek_provider.py` | 306 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `backend/app/ai/factory.py` | 35 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/ai/gemini_provider.py` | 271 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 6 |
| `backend/app/ai/guardrails.py` | 144 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/ai/prompts.py` | 255 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/ai/provider.py` | 49 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/app/api/access.py` | 28 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/app/api/ai_clinical.py` | 69 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/app/api/alerts.py` | 54 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 5 |
| `backend/app/api/billing.py` | 213 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 18 |
| `backend/app/api/devices.py` | 242 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 18 |
| `backend/app/api/health.py` | 84 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/api/ingest.py` | 117 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 8 |
| `backend/app/api/orphans.py` | 94 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 10 |
| `backend/app/api/patients.py` | 458 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 42 |
| `backend/app/api/platform.py` | 91 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 7 |
| `backend/app/api/profile.py` | 468 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 48 |
| `backend/app/api/realtime.py` | 147 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 6 |
| `backend/app/api/relatives.py` | 33 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/app/api/sos.py` | 267 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 17 |
| `backend/app/api/surveys.py` | 55 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 7 |
| `backend/app/api/tasks.py` | 89 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 12 |
| `backend/app/auth/__init__.py` | 19 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/auth/deps.py` | 164 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 9 |
| `backend/app/auth/device.py` | 135 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 3 |
| `backend/app/auth/field_policy.py` | 133 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/auth/router.py` | 176 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 10 |
| `backend/app/auth/scope.py` | 46 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/auth/service.py` | 442 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 10 |
| `backend/app/billing/__init__.py` | 17 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/billing/entitlements.py` | 130 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/billing/service.py` | 186 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/app/core/config.py` | 202 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/core/db.py` | 105 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/app/core/exceptions.py` | 149 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/core/logging.py` | 51 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/core/metrics.py` | 100 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/core/rate_limit.py` | 133 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 7 |
| `backend/app/core/realtime.py` | 227 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/core/rls.py` | 26 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/core/security.py` | 88 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/app/core/tenant.py` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/db/__init__.py` | 6 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/db/base.py` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/app/db/session.py` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/domain/__init__.py` | 2 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/domain/access.py` | 36 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/domain/attribution.py` | 42 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/domain/billing_calc.py` | 63 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/domain/clinical_cohorts.py` | 108 | Yakuniy bosqichda prototip mazmuniy ko‘rildi; runtime integratsiya alohida tekshirildi; Python AST OK, Ruff 1 |
| `backend/app/domain/device_assignment.py` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/domain/entitlement.py` | 47 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/domain/health_quality.py` | 103 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/domain/monetization_saas.py` | 65 | Yakuniy bosqichda prototip mazmuniy ko‘rildi; runtime integratsiya alohida tekshirildi; Python AST OK |
| `backend/app/domain/peace_of_mind.py` | 103 | Yakuniy bosqichda prototip mazmuniy ko‘rildi; runtime integratsiya alohida tekshirildi; Python AST OK |
| `backend/app/domain/quality.py` | 18 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/domain/responsibility.py` | 46 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/domain/types.py` | 147 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/main.py` | 255 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/middleware/__init__.py` | 11 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/middleware/logging_middleware.py` | 45 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/middleware/metrics_middleware.py` | 43 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/middleware/request_id.py` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/middleware/security_headers.py` | 30 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/__init__.py` | 107 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/models/address.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/admission.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/alert.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/allergy.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/audit.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/base.py` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/models/baseline.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/condition.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/device.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/device_assignment.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/invoice.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/measurement.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/medication.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/models/notification.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/patient.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/payment.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/reading.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/models/refresh_token.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/relative.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/models/risk_factor.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/schema.py` | 835 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 2 |
| `backend/app/models/sos.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/subscription.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/models/task.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/tenant.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/models/twin_snapshot.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/models/user.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/repositories/__init__.py` | 21 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/repositories/access_repo.py` | 42 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/repositories/account_repo.py` | 33 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/repositories/alert_repo.py` | 59 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/repositories/audited_repo.py` | 76 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/repositories/baseline_repo.py` | 54 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/repositories/membership_repo.py` | 33 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/repositories/patient_repo.py` | 68 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 3 |
| `backend/app/repositories/profile_repo.py` | 358 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/repositories/reading_repo.py` | 129 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/repositories/refresh_token_repo.py` | 57 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/repositories/relative_repo.py` | 61 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/repositories/sos_repo.py` | 107 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `backend/app/repositories/task_repo.py` | 137 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/repositories/user_repo.py` | 21 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/schemas/__init__.py` | 56 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/schemas/alert.py` | 17 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/schemas/auth.py` | 67 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/schemas/common.py` | 19 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/schemas/health_data.py` | 163 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/app/schemas/patient.py` | 39 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/schemas/problem.py` | 54 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/schemas/profile.py` | 249 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/schemas/reading.py` | 79 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/schemas/relative.py` | 75 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/schemas/series.py` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/schemas/sos.py` | 65 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/schemas/task.py` | 31 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/schemas/trend.py` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/services/__init__.py` | 27 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/services/access_service.py` | 42 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/services/clinical_intake_service.py` | 113 | Yakuniy bosqichda prototip mazmuniy ko‘rildi; runtime integratsiya alohida tekshirildi; Python AST OK |
| `backend/app/services/clinical_math.py` | 388 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/app/services/compat.py` | 42 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 2 |
| `backend/app/services/device_service.py` | 386 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/services/emergency/dispatcher.py` | 56 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 2 |
| `backend/app/services/health_data_service.py` | 285 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/services/live_event_service.py` | 110 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/services/orphan_service.py` | 183 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/services/patient_context.py` | 302 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 9 |
| `backend/app/services/patient_relationship_service.py` | 197 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/services/patient_service.py` | 407 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 7 |
| `backend/app/services/payment_webhook_service.py` | 106 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/services/pipeline.py` | 18 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/services/pipeline_service.py` | 356 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 2 |
| `backend/app/services/relative_service.py` | 338 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/app/services/sms.py` | 45 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/services/sos_service.py` | 252 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 3 |
| `backend/app/services/survey_service.py` | 95 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/services/task_service.py` | 130 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 2 |
| `backend/app/tests/__init__.py` | 1 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/tests/test_access_service.py` | 81 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_ai_production.py` | 237 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 5 |
| `backend/app/tests/test_api.py` | 216 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 9 |
| `backend/app/tests/test_api_contract.py` | 187 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `backend/app/tests/test_auth.py` | 227 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_billing.py` | 126 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 5 |
| `backend/app/tests/test_billing_scope.py` | 39 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_brainstorming_features.py` | 86 | Yakuniy bosqichda prototip mazmuniy ko‘rildi; runtime integratsiya alohida tekshirildi; Python AST OK |
| `backend/app/tests/test_clinical_math.py` | 454 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 24 |
| `backend/app/tests/test_config.py` | 137 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_deepseek_provider.py` | 273 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `backend/app/tests/test_devices.py` | 154 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/tests/test_domain_rules.py` | 198 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_field_policy.py` | 54 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_ingest_auth.py` | 125 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_orphans.py` | 68 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/tests/test_patient_context.py` | 138 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/tests/test_patient_login.py` | 82 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_patient_relationships.py` | 118 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/tests/test_payment_webhook.py` | 129 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/tests/test_profile_scope.py` | 35 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/tests/test_rate_limit.py` | 45 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_rbac.py` | 122 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `backend/app/tests/test_realtime.py` | 197 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_relative_access.py` | 65 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `backend/app/tests/test_rls.py` | 56 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/app/tests/test_sms_auth.py` | 44 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_sos_service.py` | 159 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/tests/test_surveys.py` | 99 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/app/utils/__init__.py` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/utils/storage.py` | 91 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `backend/app/workers/__init__.py` | 14 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/app/workers/escalation_worker.py` | 137 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 5 |
| `backend/app/workers/manager.py` | 113 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 3 |
| `backend/app/workers/partition_worker.py` | 57 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 4 |
| `backend/app/workers/realtime_outbox_worker.py` | 44 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `backend/auth/__init__.py` | 0 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `backend/auth/deps.py` | 22 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/auth/requirements.txt` | 3 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `backend/auth/router.py` | 22 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/auth/security.py` | 54 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `backend/entrypoint.sh` | 21 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `backend/prompt.txt` | 870 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `backend/requirements.txt` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `conftest.py` | 176 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `contracts/.gitkeep` | 0 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `contracts/algo_interface.py` | 200 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `contracts/openapi.yaml` | 7084 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `contracts/timewin.py` | 51 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK |
| `contracts/types.ts` | 319 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `deploy.sh` | 19 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `docker-compose.yml` | 75 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `docker/compose/docker-compose.yml` | 375 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `docker/monitoring/grafana/dashboards/wmax-enterprise.json` | 123 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/monitoring/grafana/provisioning/dashboards/dashboards.yml` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/monitoring/grafana/provisioning/datasources/datasources.yml` | 20 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/monitoring/loki/loki-config.yml` | 39 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/monitoring/loki/promtail-config.yml` | 52 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/monitoring/prometheus/alerts.yml` | 53 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/monitoring/prometheus/prometheus.yml` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/nginx/Dockerfile` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/nginx/conf.d/default.conf` | 183 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/nginx/nginx.conf` | 88 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/postgres/postgresql.conf` | 60 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docker/redis/redis.conf` | 48 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `docs/ARCHITECTURE.md` | 2472 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `docs/BRAINSTORMING.md` | 38 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `docs/DATA_AUDIT.md` | 167 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `docs/IDEOLOGY.md` | 678 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `docs/SDLC.md` | 164 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `landing/images/doctor_caring_telehealth.png` | binary | Asset inventari; vizual QA qilinmagan |
| `landing/images/family_peace_reunion.png` | binary | Asset inventari; vizual QA qilinmagan |
| `landing/images/hero_parent_smartwatch.png` | binary | Asset inventari; vizual QA qilinmagan |
| `landing/images/worry_distance_son.png` | binary | Asset inventari; vizual QA qilinmagan |
| `landing/index.html` | 1512 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `landing/public/images/doctor_caring_telehealth.png` | binary | Asset inventari; vizual QA qilinmagan |
| `landing/public/images/family_peace_reunion.png` | binary | Asset inventari; vizual QA qilinmagan |
| `landing/public/images/hero_parent_smartwatch.png` | binary | Asset inventari; vizual QA qilinmagan |
| `landing/public/images/worry_distance_son.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/.gitignore` | 45 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/.metadata` | 45 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/analysis_options.yaml` | 28 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/.gitignore` | 14 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/build.gradle.kts` | 82 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/debug/AndroidManifest.xml` | 7 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/AndroidManifest.xml` | 78 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/java/com/wmax/mobile_flutter/MainActivity.java` | 527 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/java/com/wmax/mobile_flutter/WearHealthRegistrationCallback.java` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/java/com/wmax/mobile_flutter/WmaxWearDataListenerService.java` | 190 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `mobile_flutter/android/app/src/main/kotlin/com/wmax/mobile_flutter/HealthConnectReader.kt` | 461 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/res/drawable-v21/launch_background.xml` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/res/drawable/launch_background.xml` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/res/mipmap-hdpi/ic_launcher.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/android/app/src/main/res/mipmap-mdpi/ic_launcher.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/android/app/src/main/res/values-night/styles.xml` | 18 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/main/res/values/styles.xml` | 18 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/phone/AndroidManifest.xml` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/phone/java/com/wmax/mobile_flutter/WearHealthServices.kt` | 17 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/profile/AndroidManifest.xml` | 7 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/wear/AndroidManifest.xml` | 20 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/wear/java/com/wmax/mobile_flutter/RegisterWearHealthWorker.kt` | 43 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/wear/java/com/wmax/mobile_flutter/WearBootReceiver.kt` | 20 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/wear/java/com/wmax/mobile_flutter/WearExerciseService.kt` | 398 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/wear/java/com/wmax/mobile_flutter/WearHealthOutbox.kt` | 212 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `mobile_flutter/android/app/src/wear/java/com/wmax/mobile_flutter/WearHealthOutboxWorker.kt` | 15 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `mobile_flutter/android/app/src/wear/java/com/wmax/mobile_flutter/WearHealthServices.kt` | 109 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/app/src/wear/java/com/wmax/mobile_flutter/WmaxPassiveHealthService.kt` | 136 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `mobile_flutter/android/build.gradle.kts` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/gradle.properties` | 3 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/gradle/wrapper/gradle-wrapper.properties` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/android/settings.gradle.kts` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/.gitignore` | 34 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Flutter/AppFrameworkInfo.plist` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Flutter/Debug.xcconfig` | 2 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Flutter/Release.xcconfig` | 2 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Podfile` | 43 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Podfile.lock` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcodeproj/project.pbxproj` | 735 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcodeproj/project.xcworkspace/contents.xcworkspacedata` | 7 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcodeproj/project.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcodeproj/project.xcworkspace/xcshareddata/WorkspaceSettings.xcsettings` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcodeproj/xcshareddata/xcschemes/Runner.xcscheme` | 101 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcworkspace/contents.xcworkspacedata` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner.xcworkspace/xcshareddata/WorkspaceSettings.xcsettings` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/AppDelegate.swift` | 18 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json` | 122 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-20x20@1x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-20x20@2x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-20x20@3x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-29x29@1x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-29x29@2x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-29x29@3x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-40x40@1x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-40x40@2x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-40x40@3x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-60x60@2x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-60x60@3x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-76x76@1x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-76x76@2x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-83.5x83.5@2x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/Contents.json` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/LaunchImage.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/LaunchImage@2x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/LaunchImage@3x.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/README.md` | 5 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Base.lproj/LaunchScreen.storyboard` | 37 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Base.lproj/Main.storyboard` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/HealthKitBridge.swift` | 314 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Info.plist` | 51 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Runner-Bridging-Header.h` | 1 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/Runner/Runner.entitlements` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/ios/RunnerTests/RunnerTests.swift` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/lib/api/api_service.dart` | 496 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Flutter analyze doirasida |
| `mobile_flutter/lib/main.dart` | 273 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/models/models.dart` | 603 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Flutter analyze doirasida |
| `mobile_flutter/lib/screens/dashboard_screen.dart` | 1634 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Flutter analyze doirasida |
| `mobile_flutter/lib/screens/health_device_screen.dart` | 290 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/screens/login_screen.dart` | 384 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/screens/watch_runtime_screen.dart` | 609 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/services/device_credential_store.dart` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/services/edge_sensor_filter.dart` | 48 | Yakuniy bosqichda prototip mazmuniy ko‘rildi; runtime integratsiya alohida tekshirildi; Flutter analyze doirasida |
| `mobile_flutter/lib/services/native_health_bridge.dart` | 275 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Flutter analyze doirasida |
| `mobile_flutter/lib/services/session_service.dart` | 127 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/utils/launcher_utils.dart` | 17 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/widgets/language_selector.dart` | 99 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/widgets/vitals_card.dart` | 92 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/lib/widgets/watch_sheet.dart` | 992 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Flutter analyze doirasida |
| `mobile_flutter/linux/.gitignore` | 1 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/CMakeLists.txt` | 128 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/flutter/CMakeLists.txt` | 88 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/flutter/generated_plugin_registrant.cc` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/flutter/generated_plugin_registrant.h` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/flutter/generated_plugins.cmake` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/runner/CMakeLists.txt` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/runner/main.cc` | 6 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/runner/my_application.cc` | 148 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/linux/runner/my_application.h` | 21 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/.gitignore` | 7 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Flutter/Flutter-Debug.xcconfig` | 2 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Flutter/Flutter-Release.xcconfig` | 2 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Flutter/GeneratedPluginRegistrant.swift` | 14 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Podfile` | 42 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Podfile.lock` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner.xcodeproj/project.pbxproj` | 801 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner.xcodeproj/project.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner.xcodeproj/xcshareddata/xcschemes/Runner.xcscheme` | 99 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner.xcworkspace/contents.xcworkspacedata` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/AppDelegate.swift` | 13 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json` | 68 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_1024.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_128.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_16.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_256.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_32.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_512.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_64.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/macos/Runner/Base.lproj/MainMenu.xib` | 343 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Configs/AppInfo.xcconfig` | 14 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Configs/Debug.xcconfig` | 2 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Configs/Release.xcconfig` | 2 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Configs/Warnings.xcconfig` | 13 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/DebugProfile.entitlements` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Info.plist` | 32 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/MainFlutterWindow.swift` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/Runner/Release.entitlements` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/macos/RunnerTests/RunnerTests.swift` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/pubspec.lock` | 434 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/pubspec.yaml` | 92 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/test/api_live_test.dart` | 55 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `mobile_flutter/test/widget_test.dart` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/web/favicon.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/web/icons/Icon-192.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/web/icons/Icon-512.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/web/icons/Icon-maskable-192.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/web/icons/Icon-maskable-512.png` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/web/index.html` | 38 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/web/manifest.json` | 35 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/.gitignore` | 17 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/CMakeLists.txt` | 108 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/flutter/CMakeLists.txt` | 109 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/flutter/generated_plugin_registrant.cc` | 14 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/flutter/generated_plugin_registrant.h` | 15 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/flutter/generated_plugins.cmake` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/CMakeLists.txt` | 40 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/Runner.rc` | 121 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/flutter_window.cpp` | 71 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/flutter_window.h` | 33 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/main.cpp` | 43 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/resource.h` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/resources/app_icon.ico` | binary | Asset inventari; vizual QA qilinmagan |
| `mobile_flutter/windows/runner/runner.exe.manifest` | 14 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/utils.cpp` | 65 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/utils.h` | 19 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/win32_window.cpp` | 288 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `mobile_flutter/windows/runner/win32_window.h` | 102 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `notifier/Dockerfile` | 12 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `notifier/__init__.py` | 0 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `notifier/admin_store.py` | 145 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 2 |
| `notifier/admins.json` | 11 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `notifier/ai_assistant.py` | 312 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `notifier/api_manager.py` | 340 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 6 |
| `notifier/excel_exporter.py` | 350 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 4 |
| `notifier/main.py` | 354 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 1 |
| `notifier/requirements.txt` | 4 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `notifier/state.py` | 74 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 2 |
| `notifier/telegram.py` | 1305 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); Python AST OK, Ruff 15 |
| `notifier/tests/test_state.py` | 43 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 1 |
| `notifier/user_tracker.py` | 338 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK, Ruff 3 |
| `notifier/users.json` | 13 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `pytest.ini` | 14 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `scripts/backup.sh` | 88 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/cleanup.sh` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/deploy.sh` | 160 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); fayl tasnifi |
| `scripts/healthcheck.sh` | 54 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/init_ssl.sh` | 70 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/mark_release_success.sh` | 21 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/renew_ssl.sh` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/restore.sh` | 144 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/rollback.sh` | 82 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/seed_demo.py` | 312 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `scripts/setup_server.sh` | 176 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/systemd/wmax-backup.service` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/systemd/wmax-backup.timer` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/systemd/wmax-restore-verify.service` | 12 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/systemd/wmax-restore-verify.timer` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/verify_backup_restore.sh` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `scripts/watch_sim.py` | 429 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; Python AST OK |
| `web-doctor/.dockerignore` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/.gitignore` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/.oxlintrc.json` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/Dockerfile` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/index.html` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/nginx.conf` | 14 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/package-lock.json` | 1712 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/package.json` | 27 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/public/favicon.svg` | 1 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/public/icons.svg` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/src/App.tsx` | 492 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/components/ConfirmModal.tsx` | 157 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/components/DeviceInventoryModal.tsx` | 577 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/components/Navbar.tsx` | 401 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/components/NurseHandoverPanel.tsx` | 274 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/components/ParamChart.tsx` | 171 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/components/SosBanner.tsx` | 73 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/i18n.ts` | 611 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/index.css` | 6678 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/src/lib/api.ts` | 540 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/lib/mock.ts` | 372 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/lib/types.ts` | 343 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/main.tsx` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/pages/HandoffsPage.tsx` | 463 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/pages/PatientDetail.tsx` | 645 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/pages/PatientsList.tsx` | 393 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/pages/ProfilePage.tsx` | 439 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/src/pages/SosDispatcher.tsx` | 452 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-doctor/tsconfig.app.json` | 29 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/tsconfig.json` | 7 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/tsconfig.node.json` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-doctor/vite.config.ts` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/.dockerignore` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/.gitignore` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/.oxlintrc.json` | 8 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/Dockerfile` | 16 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/index.html` | 17 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/nginx.conf` | 20 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/package-lock.json` | 2571 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/package.json` | 33 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/public/favicon.svg` | 1 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/public/icons.svg` | 24 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/src/App.tsx` | 686 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/ActionContactBar.tsx` | 124 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/HandoffNoticeCard.tsx` | 71 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/HeroStatusPrognosis.tsx` | 193 | Kod/oqim bo‘yicha mazmuniy ko‘rik (tegishli qismlar); TS build + web lint doirasida |
| `web-relative/src/components/InteractiveMetrics.tsx` | 250 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/LanguageSelector.tsx` | 36 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/PatientSwitcher.tsx` | 116 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/PlanStatusCard.tsx` | 211 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/ProblemBreakdown.tsx` | 120 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/RelativeProfilePopover.tsx` | 184 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/SosEmergencyBanner.tsx` | 150 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/V2ProfileActions.tsx` | 239 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/components/Vitals.tsx` | 265 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/i18n.ts` | 548 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/index.css` | 192 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/src/lib/api.ts` | 322 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/lib/mock.ts` | 294 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/lib/types.ts` | 319 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/lib/utils.ts` | 6 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/src/main.tsx` | 10 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |
| `web-relative/tsconfig.app.json` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/tsconfig.json` | 7 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/tsconfig.node.json` | 23 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; fayl tasnifi |
| `web-relative/vite.config.ts` | 26 | Inventar/statik qamrov; individual to‘liq qo‘lda ko‘rik tasdiqlanmagan; TS build + web lint doirasida |

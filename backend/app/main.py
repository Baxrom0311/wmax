from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.ai.factory import build_ai_provider
from app.api.ai_clinical import router as ai_clinical_router
from app.api.billing import router as billing_router
from app.api.devices import router as devices_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.patients import router as patients_router
from app.api.profile import router as profile_router
from app.api.relatives import router as relatives_router
from app.api.sos import router as sos_router
from app.api.tasks import router as tasks_router
from app.auth.router import router as auth_router
from app.core.config import settings, validate_production_settings
from app.core.db import check_db_connection
from app.core.exceptions import (
    BaseAppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.middleware.logging_middleware import AccessLoggingMiddleware
from app.middleware.metrics_middleware import PrometheusMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.workers.manager import worker_manager

setup_logging()
logger = logging.getLogger("wmax.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup checks and worker management."""
    logger.info("WMAX API starting up (env=%s)...", settings.ENV)

    # Refuse to serve real clinical traffic with placeholder secrets.
    validate_production_settings()

    # Build the configured LLM client once at boot: it surfaces a bad
    # AI_PROVIDER value immediately and registers the provider's circuit-breaker
    # gauge, so the Grafana panel is populated before the first AI call.
    try:
        provider = build_ai_provider()
        logger.info("AI provider: %s (%s)", settings.AI_PROVIDER, type(provider).__name__)
    except ValueError as err:
        logger.error("AI provider misconfigured: %s", err)

    # Verify DB connectivity
    db_ok = await check_db_connection()
    if db_ok:
        logger.info("Database connection: OK")
    else:
        logger.warning("Database connection: FAILED — will retry on first request")

    # Start background workers
    worker_manager.start_workers()
    logger.info("Background workers: STARTED")

    yield

    # Graceful shutdown
    logger.info("WMAX API shutting down...")
    await worker_manager.stop_workers()
    logger.info("Background workers: STOPPED")


from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

TAGS_METADATA = [
    {
        "name": "auth",
        "description": "Foydalanuvchilar autentifikatsiyasi va JWT tokenlar boshqaruvi (shifokor, hamshira, dispetcher, yaqin qarindosh, bemor).",
    },
    {
        "name": "ingest",
        "description": "Aqlli soat (Wear OS) va sensorlardan 5 daqiqalik o'lchovlar oqimini qabul qilish va signal tekshiruvi (idempotent, X-Ingest-Key himoyalangan).",
    },
    {
        "name": "patients",
        "description": "Bemorlar profili, dispanser nazorati, vital parametrlar, baseline (me'yorlar), audit va kasallik tarixi.",
    },
    {
        "name": "ai-clinical",
        "description": "Sun'iy intellekt (AI) klinik assistenti: prognoz, dekompensatsiya xavfi va shifokor tavsiyalari (fallbacks bilan).",
    },
    {
        "name": "sos",
        "description": "Favqulodda SOS signallari, dispetcherlik boshqaruvi va SSE (Server-Sent Events) real-vaqt monitoringi.",
    },
    {
        "name": "tasks",
        "description": "Patronaj hamshiralar uchun klinik vazifalar va patronaj buyruqlarini boshqarish.",
    },
    {
        "name": "devices",
        "description": "Wearable qurilmalar parki, bemorga biriktirish va qaytarib olish amallari.",
    },
    {
        "name": "relative",
        "description": "Yaqin qarindoshlar portali — cheklangan holat ko'rinishi va xabardorlik.",
    },
    {
        "name": "billing",
        "description": "Monitoring obuna rejalari, to'lovlar va invoyslar hisobi.",
    },
    {
        "name": "profile",
        "description": "Foydalanuvchi shaxsiy hisobi va sozlamalari.",
    },
    {
        "name": "ops",
        "description": "Infratuzilma salomatligi, liveness/readiness tekshiruvlari va monitoring darchalari.",
    },
    {
        "name": "observability",
        "description": "Prometheus metrikalari va monitoring tahlili.",
    },
]

app = FastAPI(
    title="WMAX API",
    description="Remote Patient Monitoring — production-grade clinical signal backend",
    version="2.0.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    # Public API documentation is intentionally available in production.
    # Authentication and authorization remain enforced by each operation;
    # exposing the schema does not bypass endpoint security.
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=[
            {"url": "/", "description": "Standart origin (Lokal dev :8000 yoki reverse proxy ildizi)"},
        ],
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]

# ── Middleware (outermost first) ──────────────────────────────────────────────
app.add_middleware(RequestIdMiddleware)
app.add_middleware(AccessLoggingMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    # Behind Caddy the portals are same-origin, so this list only matters for
    # local dev and split-domain deployments. Configure it with CORS_ORIGINS.
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Ingest-Key"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(BaseAppException, app_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(patients_router)
app.include_router(ai_clinical_router)
app.include_router(profile_router)
app.include_router(sos_router)
app.include_router(tasks_router)
app.include_router(relatives_router)
app.include_router(billing_router)
app.include_router(devices_router)
# /health, /ready, /live and /metrics — scraped by Prometheus and used as the
# container healthcheck.
app.include_router(health_router)


@app.get("/api/v1/health", tags=["ops"], summary="Liveness probe")
async def health_check() -> dict:
    db_ok = await check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unreachable",
        "version": "2.0.0",
    }


# ── Documentation routes (accessible behind Caddy /api/* proxy) ───────────────
@app.get("/api/openapi.json", include_in_schema=False)
@app.get("/api/v1/openapi.json", include_in_schema=False)
async def get_api_openapi_json() -> dict:
    return app.openapi()


@app.get("/api/docs", include_in_schema=False)
@app.get("/api/v1/docs", include_in_schema=False)
async def get_api_swagger_ui() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


@app.get("/api/redoc", include_in_schema=False)
@app.get("/api/v1/redoc", include_in_schema=False)
async def get_api_redoc() -> HTMLResponse:
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


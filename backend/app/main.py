from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.ingest import router as ingest_router
from app.api.patients import router as patients_router
from app.api.relatives import router as relatives_router
from app.api.tasks import router as tasks_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.db import check_db_connection
from app.core.exceptions import (
    BaseAppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.middleware.logging_middleware import AccessLoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.workers.manager import worker_manager

setup_logging()
logger = logging.getLogger("nazorat.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup checks and worker management."""
    logger.info("NAZORAT API starting up (env=%s)...", settings.ENV)

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
    logger.info("NAZORAT API shutting down...")
    await worker_manager.stop_workers()
    logger.info("Background workers: STOPPED")


app = FastAPI(
    title="NAZORAT API",
    description="Remote Patient Monitoring — production-grade clinical signal backend",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
)

# ── Middleware (outermost first) ──────────────────────────────────────────────
app.add_middleware(RequestIdMiddleware)
app.add_middleware(AccessLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # web-doctor dev
        "http://localhost:5174",   # web-relative dev
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
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
app.include_router(tasks_router)
app.include_router(relatives_router)


@app.get("/api/v1/health", tags=["ops"], summary="Liveness probe")
async def health_check() -> dict:
    db_ok = await check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unreachable",
        "version": "2.0.0",
    }

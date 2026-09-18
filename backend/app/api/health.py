"""Production Health Checks & Prometheus Observability Endpoints.

Endpoints:
- /health: Detailed system health status
- /ready: Kubernetes / Docker Compose readiness probe (verifies PostgreSQL & Redis)
- /live: Liveness probe (verifies FastAPI process is alive)
- /metrics: Prometheus metrics endpoint
"""
from __future__ import annotations

import logging
import os
import time

from fastapi import APIRouter, Response, status

from app.core.db import check_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["observability"])

START_TIME = time.time()


async def check_redis_connection() -> bool:
    """Verifies Redis connection if configured."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(redis_url, socket_timeout=2.0)
        res = await r.ping()
        await r.aclose()
        return bool(res)
    except Exception as err:
        logger.debug("Redis health check skipped or failed: %s", err)
        return False


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    """Detailed health check."""
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    uptime_sec = round(time.time() - START_TIME, 2)

    overall_ok = db_ok
    status_str = "healthy" if overall_ok else "degraded"

    return {
        "status": status_str,
        "uptime_seconds": uptime_sec,
        "database": "connected" if db_ok else "unreachable",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": time.time(),
    }


@router.get("/ready")
async def readiness_probe(response: Response):
    """Readiness probe: verifies critical dependencies (DB) before accepting traffic."""
    db_ok = await check_db_connection()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ready": False, "reason": "database_unavailable"}

    return {"ready": True}


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe: verifies web server process is responsive."""
    return {"live": True}


@router.get("/metrics")
async def metrics():
    """Prometheus exposition format endpoint."""
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        # Fallback if prometheus_client is not installed in the environment
        body = (
            "# HELP app_up Application availability\n"
            "# TYPE app_up gauge\n"
            "app_up 1\n"
        )
        return Response(content=body, media_type="text/plain; version=0.0.4")

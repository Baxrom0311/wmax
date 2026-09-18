from __future__ import annotations

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.access")


class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """Tracks latency, status code, and records structured access logs."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Process-Time"] = f"{duration_ms}ms"

            # Avoid spamming logs with routine health checks in production
            if path != "/api/v1/health":
                logger.info(
                    f"{method} {path} -> {response.status_code} ({duration_ms}ms) from {client_ip}"
                )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"{method} {path} FAILED after {duration_ms}ms from {client_ip}: {exc}"
            )
            raise

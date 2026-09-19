from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.metrics import http_request_duration_seconds, http_requests_total


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records request counts and latencies for every HTTP request.

    Labels use the matched route template (`/api/v1/patients/{id}`) rather than
    the raw path, so patient ids never become metric cardinality — or a way to
    read patient identifiers out of Prometheus.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    @staticmethod
    def _route_template(request: Request) -> str:
        route = request.scope.get("route")
        return getattr(route, "path", None) or "unmatched"

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - start
            path = self._route_template(request)
            http_requests_total.labels(
                method=request.method, path=path, status=str(status_code)
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method, path=path
            ).observe(elapsed)

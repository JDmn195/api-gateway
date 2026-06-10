from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api-gateway")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with method, path, target service, status code, and latency.
    The Authorization header value is NEVER logged.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()

        # Resolve service name for logging (best-effort — may be unknown for /health)
        from router import ROUTE_TABLE
        service_name = "gateway"
        for prefix, _, name in ROUTE_TABLE:
            if request.url.path.startswith(prefix):
                service_name = name
                break

        response = await call_next(request)

        latency_ms = round((time.monotonic() - start) * 1000)
        logger.info(
            "%s %s → %s | status=%d | %dms",
            request.method,
            request.url.path,
            service_name,
            response.status_code,
            latency_ms,
        )

        return response


def add_logging(app: FastAPI) -> None:
    app.add_middleware(LoggingMiddleware)

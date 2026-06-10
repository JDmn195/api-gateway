from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("api-gateway")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class LoggingMiddleware:
    """
    Logs every request with method, path, target service, status code, and latency.
    Pure ASGI middleware — does NOT buffer the response body, avoiding the
    BaseHTTPMiddleware double-serialization bug.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request as StarletteRequest
        request = StarletteRequest(scope, receive)

        # Resolve service name for logging (best-effort)
        from router import ROUTE_TABLE
        service_name = "gateway"
        for prefix, _, name in ROUTE_TABLE:
            if request.url.path.startswith(prefix):
                service_name = name
                break

        start = time.monotonic()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)

        latency_ms = round((time.monotonic() - start) * 1000)
        logger.info(
            "%s %s → %s | status=%d | %dms",
            request.method,
            request.url.path,
            service_name,
            status_code,
            latency_ms,
        )


def add_logging(app: FastAPI) -> None:
    app.add_middleware(LoggingMiddleware)

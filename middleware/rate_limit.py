from __future__ import annotations

import asyncio
import json
import time
from collections import deque

from fastapi import FastAPI, Request
from starlette.types import ASGIApp, Receive, Scope, Send

from config import settings

# In-memory store: IP -> deque of request timestamps (unix seconds)
_store: dict[str, deque[float]] = {}
_lock = asyncio.Lock()


class RateLimitMiddleware:
    """
    Sliding window rate limiter per client IP.
    Allows RATE_LIMIT_RPM requests per 60-second window.
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

        # Skip rate limiting for the health check endpoint
        if request.url.path == "/health":
            await self.app(scope, receive, send)
            return

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = 60.0
        limit = settings.RATE_LIMIT_RPM

        async with _lock:
            if ip not in _store:
                _store[ip] = deque()

            timestamps = _store[ip]

            # Evict timestamps outside the sliding window
            while timestamps and now - timestamps[0] > window:
                timestamps.popleft()

            if len(timestamps) >= limit:
                body = json.dumps({"error": "Too many requests", "status": 429}).encode()
                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(body)).encode()],
                    ],
                })
                await send({"type": "http.response.body", "body": body})
                return

            timestamps.append(now)

        await self.app(scope, receive, send)


def add_rate_limit(app: FastAPI) -> None:
    app.add_middleware(RateLimitMiddleware)

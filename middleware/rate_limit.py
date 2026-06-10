from __future__ import annotations

import asyncio
import time
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings

# In-memory store: IP -> deque of request timestamps (unix seconds)
_store: dict[str, deque[float]] = {}
_lock = asyncio.Lock()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter per client IP.
    Allows RATE_LIMIT_RPM requests per 60-second window.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for the health check endpoint
        if request.url.path == "/health":
            return await call_next(request)

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
                return JSONResponse(
                    status_code=429,
                    content={"error": "Too many requests", "status": 429},
                )

            timestamps.append(now)

        return await call_next(request)


def add_rate_limit(app: FastAPI) -> None:
    app.add_middleware(RateLimitMiddleware)

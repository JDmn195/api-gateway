from __future__ import annotations

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, Response

from config import settings

# ---------------------------------------------------------------------------
# Routing table — order matters: more specific prefixes must come first
# ---------------------------------------------------------------------------
ROUTE_TABLE: list[tuple[str, str, str]] = [
    ("/api/auth",            settings.AUTH_SERVICE_URL,            "auth-service"),
    ("/api/catalog",         settings.CATALOG_SERVICE_URL,         "catalog-service"),
    ("/api/inventory",       settings.INVENTORY_SERVICE_URL,       "inventory-service"),
    ("/api/orders",          settings.ORDER_SERVICE_URL,           "order-service"),
    ("/api/cart",            settings.CART_SERVICE_URL,            "cart-service"),
    ("/api/notifications",   settings.NOTIFICATION_SERVICE_URL,    "notification-service"),
    ("/api/payments",        settings.PAYMENT_SERVICE_URL,         "payment-service"),
    ("/api/recommendations", settings.RECOMMENDATION_SERVICE_URL,  "recommendation-service"),
]

# Headers that should not be forwarded downstream
_HOP_BY_HOP = {
    "host",
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
    "upgrade",
    "te",
    "trailers",
}

# Response headers that should not be forwarded back to the client (unused — raw bytes returned directly)
# _DROP_RESPONSE_HEADERS = {"transfer-encoding", "content-encoding", "content-length"}


def resolve_service(path: str) -> tuple[str, str]:
    """
    Match the request path against the routing table.
    Returns (base_url, service_name).
    Raises LookupError if no route matches.
    """
    for prefix, base_url, name in ROUTE_TABLE:
        if path.startswith(prefix):
            return base_url.rstrip("/"), name
    raise LookupError(f"No route found for path: {path}")


async def proxy_request(
    request: Request,
    base_url: str,
    service_name: str,
    claims: dict | None,
) -> Response | JSONResponse:
    """
    Forward the request to the downstream service and return the raw response.
    """
    # Build target URL preserving the full path and query string
    target_url = base_url + str(request.url.path)
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Build forwarded headers — strip Authorization and hop-by-hop headers
    forward_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP and k.lower() != "authorization"
    }

    # Inject identity headers from validated JWT claims
    if claims:
        user_id = claims.get("user_id") or claims.get("sub", "")
        role = claims.get("role", "")
        forward_headers["X-User-Id"] = str(user_id)
        forward_headers["X-User-Role"] = str(role)

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            downstream = await client.request(
                method=request.method,
                url=target_url,
                headers=forward_headers,
                content=body,
            )
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError):
        return JSONResponse(
            status_code=502,
            content={"error": "Service unavailable", "status": 502, "service": service_name},
        )

    # Return raw bytes directly — no parsing or re-serialization
    raw = downstream.content
    return Response(
        content=raw,
        status_code=downstream.status_code,
        media_type=downstream.headers.get("content-type"),
    )

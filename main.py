from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auth import get_token_claims, is_internal, is_public
from middleware.cors import add_cors
from middleware.logging import add_logging
from middleware.rate_limit import add_rate_limit
from router import proxy_request, resolve_service

app = FastAPI(title="MicroShop API Gateway", version="1.0.0", docs_url=None, redoc_url=None)

# ── Middleware (registration order = outermost first) ──────────────────────
# Starlette applies middleware in reverse registration order, so we register:
# Logging first (innermost wrap), then RateLimit, then CORS (outermost wrap).
add_logging(app)
add_rate_limit(app)
add_cors(app)


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Catch-all proxy route ──────────────────────────────────────────────────
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def gateway(request: Request, path: str):
    full_path = "/" + path  # restore leading slash

    # 1. Block internal-only routes
    if is_internal(full_path):
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden", "status": 403},
        )

    # 2. Resolve downstream service
    try:
        base_url, service_name = resolve_service(full_path)
    except LookupError:
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "status": 404},
        )

    # 3. JWT validation (skip for public routes)
    claims: dict | None = None
    if not is_public(request.method, full_path):
        try:
            claims = get_token_claims(request)
            if claims is None:
                # No Authorization header at all
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "status": 401},
                )
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "status": 401},
            )

    # 4. Proxy to downstream service
    return await proxy_request(request, base_url, service_name, claims)

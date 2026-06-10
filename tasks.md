# Tasks — MicroShop API Gateway

## Task 1 — Project scaffold and config
- [ ] Create `api-gateway/` directory structure
- [ ] Create `requirements.txt` with pinned versions
- [ ] Create `config.py` — load and validate all env vars with python-dotenv
- [ ] Create `.env.example` with all variables documented

## Task 2 — JWT auth module
- [ ] Create `auth.py`
- [ ] Define `PUBLIC_ROUTES` set: POST /api/auth/login, POST /api/auth/register
- [ ] Define `INTERNAL_ROUTES` set: /api/notifications
- [ ] Implement `validate_token(token)` using python-jose HS256
- [ ] Implement `get_token_claims(request)` to extract Bearer token

## Task 3 — Routing and proxy
- [ ] Create `router.py`
- [ ] Define `ROUTE_TABLE` ordered list mapping path prefixes to env var names
- [ ] Implement `resolve_service(path)` — match prefix, return (url, name)
- [ ] Implement `proxy_request(request, target_url, service_name, claims)`
  - [ ] Strip `Authorization` header
  - [ ] Inject `X-User-Id` and `X-User-Role` when claims are present
  - [ ] Forward method, headers, query params, body with httpx AsyncClient
  - [ ] Return `StreamingResponse` with downstream status + headers
  - [ ] Catch `httpx.ConnectError` / timeout → return 502 JSON

## Task 4 — Middleware: CORS
- [ ] Create `middleware/cors.py`
- [ ] Configure `CORSMiddleware` with FRONTEND_URL, methods, headers, credentials

## Task 5 — Middleware: Rate limiting
- [ ] Create `middleware/rate_limit.py`
- [ ] Implement sliding window (1-minute window) per IP using in-memory dict
- [ ] Return 429 JSON when limit exceeded
- [ ] Use `asyncio.Lock` for thread safety

## Task 6 — Middleware: Logging
- [ ] Create `middleware/logging.py`
- [ ] Subclass `BaseHTTPMiddleware`
- [ ] Log: timestamp, method, path, service name, response status, latency ms
- [ ] Ensure `Authorization` header value is never logged

## Task 7 — Main app and routes
- [ ] Create `main.py`
- [ ] Register middleware in order: CORS → RateLimit → Logging
- [ ] Implement `GET /health` → `{ "status": "ok" }`
- [ ] Implement catch-all route `/{path:path}` for all HTTP methods:
  - [ ] Check INTERNAL_ROUTES → 403
  - [ ] Check PUBLIC_ROUTES → skip JWT, proxy
  - [ ] Validate JWT → 401 on failure
  - [ ] Proxy with claims

## Task 8 — Dockerfile
- [ ] Create `Dockerfile` following the same pattern as Django services:
  - Base image: `python:3.11-slim`
  - Install requirements
  - Copy source
  - Expose PORT
  - CMD uvicorn

## Task 9 — Documentation
- [ ] Create `README.md` with:
  - [ ] Project description
  - [ ] Local setup instructions
  - [ ] All environment variables documented
  - [ ] Render deploy instructions

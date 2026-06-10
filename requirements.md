# Requirements — MicroShop API Gateway

## Overview
Implement a centralized API Gateway for MicroShop as a new FastAPI microservice.
The gateway is the single entry point for all client requests, handling JWT validation,
routing, CORS, rate limiting, and logging before proxying to the downstream services.

---

## Functional Requirements

### FR-1 — Routing
- The gateway MUST route requests to the correct downstream service based on the URL path prefix.
- All downstream URLs MUST be read from environment variables. No URL may be hardcoded.
- Routing table:

| Path prefix             | Env var                  |
|-------------------------|--------------------------|
| /api/auth/**            | AUTH_SERVICE_URL         |
| /api/catalog/**         | CATALOG_SERVICE_URL      |
| /api/inventory/**       | INVENTORY_SERVICE_URL    |
| /api/orders/**          | ORDER_SERVICE_URL        |
| /api/cart/**            | CART_SERVICE_URL         |
| /api/notifications/**   | NOTIFICATION_SERVICE_URL |
| /api/payments/**        | PAYMENT_SERVICE_URL      |
| /api/recommendations/** | RECOMMENDATION_SERVICE_URL |

### FR-2 — JWT Validation
- The gateway MUST validate the JWT Bearer token on every request except public endpoints.
- JWT_SECRET and algorithm HS256 (same as auth-service) MUST be used.
- On a valid token the gateway MUST extract `user_id` and `role` claims and forward them
  as `X-User-Id` and `X-User-Role` headers to the downstream service.
- On an invalid or missing token the gateway MUST return:
  ```json
  { "error": "Unauthorized", "status": 401 }
  ```

### FR-3 — Public Endpoints (no JWT required)
- POST /api/auth/login
- POST /api/auth/register

### FR-4 — Internal-Only Endpoints
- `/api/notifications/**` MUST return 403 to any external request and never be proxied.

### FR-5 — Proxy Behavior
- The gateway MUST forward the original HTTP method, query parameters, headers, and body.
- The `Authorization` header MUST be stripped before forwarding.
- The downstream response (status code, headers, body) MUST be returned as-is to the client.
- If a downstream service is unreachable the gateway MUST return:
  ```json
  { "error": "Service unavailable", "status": 502, "service": "<name>" }
  ```

### FR-6 — CORS
- Allowed origin: value of FRONTEND_URL env var.
- Allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS.
- Allowed headers: Authorization, Content-Type.
- Credentials: allowed.

### FR-7 — Rate Limiting
- Limit per client IP address.
- Limit configurable via RATE_LIMIT_RPM env var (default 60 requests/minute).
- On limit exceeded return:
  ```json
  { "error": "Too many requests", "status": 429 }
  ```

### FR-8 — Logging
- Every request MUST be logged with: method, path, target service, response status, latency (ms).
- The value of the Authorization header MUST never appear in logs.

### FR-9 — Health Check
- GET /health MUST return `{ "status": "ok" }` with HTTP 200.
- Used by Render for health checks.

---

## Non-Functional Requirements

### NFR-1 — Performance
- All proxying MUST be async (httpx AsyncClient) to avoid blocking the event loop.

### NFR-2 — Security
- JWT secret MUST be loaded from environment, never hardcoded.
- Notification service MUST be completely unreachable from outside the gateway.

### NFR-3 — Deployability
- MUST be deployable on Render as a Docker container.
- Dockerfile MUST follow the same pattern as the existing MicroShop Django services.
- Port MUST be configurable via PORT env var (default 8000).

### NFR-4 — Configuration
- All configuration MUST be loaded from environment variables via python-dotenv.
- A `.env.example` file MUST document every required variable.

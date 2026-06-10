# MicroShop API Gateway

Centralized API Gateway for MicroShop built with FastAPI.
Single entry point for all client requests — handles JWT validation, routing, CORS, rate limiting, and logging.

---

## Project structure

```
api-gateway/
├── main.py               # FastAPI app, middleware registration, catch-all route
├── router.py             # Routing table and proxy logic (httpx)
├── auth.py               # JWT validation, public/internal route lists
├── config.py             # Environment variable loading (python-dotenv)
├── middleware/
│   ├── cors.py           # CORS configuration
│   ├── rate_limit.py     # Per-IP sliding window rate limiter
│   └── logging.py        # Request/response structured logging
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## Local setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your service URLs and JWT_SECRET

# 4. Run the gateway
uvicorn main:app --reload --port 8000
```

Health check: http://localhost:8000/health

---

## Environment variables

| Variable                   | Required | Default | Description |
|----------------------------|----------|---------|-------------|
| `AUTH_SERVICE_URL`         | yes      | —       | Base URL of auth-service |
| `CATALOG_SERVICE_URL`      | yes      | —       | Base URL of catalog-service |
| `INVENTORY_SERVICE_URL`    | yes      | —       | Base URL of inventory-service |
| `ORDER_SERVICE_URL`        | yes      | —       | Base URL of order-service |
| `CART_SERVICE_URL`         | yes      | —       | Base URL of cart-service |
| `NOTIFICATION_SERVICE_URL` | yes      | —       | Base URL of notification-service (internal only, never proxied to clients) |
| `PAYMENT_SERVICE_URL`      | yes      | —       | Base URL of payment-service |
| `RECOMMENDATION_SERVICE_URL` | yes    | —       | Base URL of recommendation-service |
| `JWT_SECRET`               | yes      | —       | Shared JWT secret — must match auth-service |
| `FRONTEND_URL`             | yes      | —       | Allowed CORS origin (Vercel URL) |
| `RATE_LIMIT_RPM`           | no       | `60`    | Max requests per minute per IP |
| `PORT`                     | no       | `8000`  | Uvicorn listening port |

---

## Routing table

| Path prefix             | Downstream service     | Auth required |
|-------------------------|------------------------|---------------|
| /api/auth/login         | auth-service           | No (public)   |
| /api/auth/register      | auth-service           | No (public)   |
| /api/auth/**            | auth-service           | Yes           |
| /api/catalog/**         | catalog-service        | Yes           |
| /api/inventory/**       | inventory-service      | Yes           |
| /api/orders/**          | order-service          | Yes           |
| /api/cart/**            | cart-service           | Yes           |
| /api/notifications/**   | —                      | 403 (blocked) |
| /api/payments/**        | payment-service        | Yes           |
| /api/recommendations/** | recommendation-service | Yes           |

---

## Deploy on Render

1. Push `api-gateway/` to its own GitHub repository (or subfolder with root directory set).
2. Create a new **Web Service** on Render.
3. Set **Environment** → Docker.
4. Set **Health Check Path** → `/health`.
5. Add all environment variables from `.env.example` in the Render dashboard.
6. After deploy, copy the Render URL and set it as `VITE_GATEWAY_URL` in the frontend.

---

## Frontend migration

After deploying the gateway, the React frontend only needs one env var:

```env
VITE_GATEWAY_URL=https://your-gateway.onrender.com
```

Replace all `VITE_*_URL` references with `VITE_GATEWAY_URL`.

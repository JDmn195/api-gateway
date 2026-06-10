import os
from dotenv import load_dotenv

load_dotenv()


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {var}")
    return value


class Settings:
    # Downstream service URLs
    AUTH_SERVICE_URL: str = _require("AUTH_SERVICE_URL")
    CATALOG_SERVICE_URL: str = _require("CATALOG_SERVICE_URL")
    INVENTORY_SERVICE_URL: str = _require("INVENTORY_SERVICE_URL")
    ORDER_SERVICE_URL: str = _require("ORDER_SERVICE_URL")
    CART_SERVICE_URL: str = _require("CART_SERVICE_URL")
    NOTIFICATION_SERVICE_URL: str = _require("NOTIFICATION_SERVICE_URL")
    PAYMENT_SERVICE_URL: str = _require("PAYMENT_SERVICE_URL")
    RECOMMENDATION_SERVICE_URL: str = _require("RECOMMENDATION_SERVICE_URL")

    # Auth
    JWT_SECRET: str = _require("JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"

    # Gateway config
    FRONTEND_URL: str = _require("FRONTEND_URL")
    RATE_LIMIT_RPM: int = int(os.getenv("RATE_LIMIT_RPM", "60"))
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()

from __future__ import annotations

from fastapi import Request
from jose import JWTError, jwt

from config import settings

# ---------------------------------------------------------------------------
# Public routes — JWT validation is skipped for these (method, path) pairs
# ---------------------------------------------------------------------------
PUBLIC_ROUTES: set[tuple[str, str]] = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/register"),
    ("GET",  "/api/auth/verify-email"),
    ("GET",  "/api/auth/validate-token"),
    ("POST", "/api/auth/forgot-password"),
    ("POST", "/api/auth/reset-password"),
}

# ---------------------------------------------------------------------------
# Internal routes — blocked from any external access (403)
# ---------------------------------------------------------------------------
INTERNAL_PREFIXES: tuple[str, ...] = ("/api/notifications",)


def is_public(method: str, path: str) -> bool:
    """Return True if the request should bypass JWT validation."""
    return (method.upper(), path.rstrip("/")) in {
        (m, p.rstrip("/")) for m, p in PUBLIC_ROUTES
    }


def is_internal(path: str) -> bool:
    """Return True if the path targets an internal-only service."""
    return path.startswith(INTERNAL_PREFIXES)


def validate_token(token: str) -> dict:
    """
    Decode and validate a JWT.
    Returns the payload dict on success.
    Raises ValueError on any validation failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc


def get_token_claims(request: Request) -> dict | None:
    """
    Extract the Bearer token from the Authorization header and validate it.
    Returns the claims dict, or None if no Authorization header is present.
    Raises ValueError if the header is present but the token is invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    return validate_token(token)

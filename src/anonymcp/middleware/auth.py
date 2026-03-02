"""API key authentication middleware for HTTP transport.

When ANONYMCP_REQUIRE_AUTH=true, every HTTP request must include
a valid API key in the Authorization header:

    Authorization: Bearer <api-key>

Valid keys are set via ANONYMCP_API_KEYS (comma-separated).
"""

from __future__ import annotations

import hmac
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Reject requests that don't carry a valid Bearer token."""

    def __init__(self, app: ASGIApp, valid_keys: set[str]) -> None:
        super().__init__(app)
        self._valid_keys = valid_keys

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        auth_header = request.headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            logger.warning(
                "auth_missing",
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                {"error": "Missing Authorization header. Use: Bearer <api-key>"},
                status_code=401,
            )

        token = auth_header[7:]  # strip "Bearer "

        if not self._is_valid_key(token):
            logger.warning(
                "auth_rejected",
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                {"error": "Invalid API key"},
                status_code=403,
            )

        return await call_next(request)

    def _is_valid_key(self, token: str) -> bool:
        """Constant-time comparison against all valid keys."""
        return any(
            hmac.compare_digest(token.encode(), key.encode())
            for key in self._valid_keys
        )

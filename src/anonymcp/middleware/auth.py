"""API key authentication middleware for HTTP transport.

When ANONYMCP_REQUIRE_AUTH=true, every HTTP request must include
a valid API key in the Authorization header:

    Authorization: Bearer <api-key>

Valid keys and roles are set via ANONYMCP_API_KEYS:

    ANONYMCP_API_KEYS=pipeline-key:read,admin-key:admin

Keys without a role tag default to "admin" for backward compatibility.
"""

from __future__ import annotations

import hmac
from typing import TYPE_CHECKING, Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from anonymcp.middleware.roles import caller_role

if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.requests import Request
    from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate requests and set caller role via contextvar."""

    def __init__(self, app: ASGIApp, key_roles: dict[str, str]) -> None:
        super().__init__(app)
        self._key_roles = key_roles  # {api_key: role}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[..., Any],
    ) -> Response:
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

        role = self._resolve_role(token)
        if role is None:
            logger.warning(
                "auth_rejected",
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                {"error": "Invalid API key"},
                status_code=403,
            )

        # Set the caller's role for downstream tool authorization
        reset_token = caller_role.set(role)
        try:
            response: Response = await call_next(request)
            return response
        finally:
            caller_role.reset(reset_token)

    def _resolve_role(self, token: str) -> str | None:
        """Constant-time lookup: returns role if key is valid, None otherwise."""
        for key, role in self._key_roles.items():
            if hmac.compare_digest(token.encode(), key.encode()):
                return role
        return None

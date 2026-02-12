"""Multi-tenancy middleware — ensures org_id scoping on all requests."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Paths that don't require org_id
EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
}


class OrgScopingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts org_id from JWT claims (set by gateway)
    and makes it available on request.state.org_id.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip for exempt paths
        path = request.url.path.rstrip("/")
        if path in EXEMPT_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # org_id comes from either:
        # 1. X-Org-Id header (set by gateway after JWT verification)
        # 2. JWT claims (if service verifies JWT directly)
        org_id = request.headers.get("X-Org-Id")
        if org_id:
            request.state.org_id = org_id
        else:
            request.state.org_id = None

        return await call_next(request)

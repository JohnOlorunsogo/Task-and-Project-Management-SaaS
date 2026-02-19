"""Shared middleware for org scoping."""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Paths that don't require org context
EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
EXEMPT_PREFIXES = ("/auth",)


class OrgScopingMiddleware(BaseHTTPMiddleware):
    """Extract org_id from headers and attach to request.state.

    Returns 400 for non-exempt paths if org_id is missing.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip exempt paths
        is_exempt = path in EXEMPT_PATHS or any(path.startswith(p) for p in EXEMPT_PREFIXES)

        org_id = request.headers.get("x-org-id")
        request.state.org_id = org_id

        if not is_exempt and not org_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "X-Org-Id header is required"},
            )

        response = await call_next(request)
        return response

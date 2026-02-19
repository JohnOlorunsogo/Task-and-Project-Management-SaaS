from __future__ import annotations

import uuid
import logging
from typing import Any, Optional

import httpx
from fastapi import Depends, HTTPException, status

from shared.auth import TokenData
from shared.auth.rbac import (
    PermissionResult,
    ProjectPermission,
    check_project_permission,
)
from app.config import get_settings
from app.dependencies import get_current_user, get_db

logger = logging.getLogger("task_service")

# Module-level client for connection pooling (M2 fix)
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=5.0)
    return _http_client


async def get_project_membership(
    project_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
) -> Optional[dict[str, Any]]:
    """
    Fetch project membership for the current user via Project Service HTTP call.
    """
    settings = get_settings()
    client = _get_http_client()

    try:
        url = f"{settings.project_service_url}/projects/{project_id}/check-membership"
        resp = await client.get(
            url,
            params={"user_id": current_user.user_id},
            headers={"x-internal-service-key": settings.internal_service_key},
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning("Failed to check project membership: %s", e)

    return None


def require_project_permission(permission: ProjectPermission):
    """
    Request-scoped dependency to check project permissions.
    """
    async def _dependency(
        project_id: uuid.UUID,
        current_user: TokenData = Depends(get_current_user),
        membership: Optional[dict[str, Any]] = Depends(get_project_membership),
    ) -> PermissionResult:
        return check_project_permission(current_user, membership, permission)

    return _dependency

"""Task Service — Project-Level Permission Dependencies.

For endpoints where `project_id` is available as a path or query param,
use `require_project_permission` directly.

For endpoints where only `task_id` is available, use
`require_task_project_permission` which resolves the project from the task
record first, then checks membership.
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Optional

import httpx
from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData
from shared.auth.rbac import (
    PermissionResult,
    ProjectPermission,
    check_project_permission,
)
from app.config import get_settings
from app.dependencies import get_current_user, get_db

logger = logging.getLogger("task_service")

# Module-level client for connection pooling
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
    """Fetch project membership for the current user via Project Service HTTP call."""
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
    """Permission dependency when `project_id` is available as a path/query param."""

    async def _dependency(
        project_id: uuid.UUID,
        current_user: TokenData = Depends(get_current_user),
        membership: Optional[dict[str, Any]] = Depends(get_project_membership),
    ) -> PermissionResult:
        return check_project_permission(current_user, membership, permission)

    return _dependency


# ---- Task-level permission (resolves project_id from task record) ----


async def _resolve_project_id_from_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    """Look up which project a task belongs to."""
    from app.models import Task

    stmt = select(Task.project_id).where(Task.id == task_id)
    result = await db.execute(stmt)
    project_id = result.scalar_one_or_none()
    if project_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return project_id


async def _get_membership_for_task(
    project_id: uuid.UUID = Depends(_resolve_project_id_from_task),
    current_user: TokenData = Depends(get_current_user),
) -> tuple[uuid.UUID, Optional[dict[str, Any]]]:
    """Fetch membership using the project resolved from the task."""
    settings = get_settings()
    client = _get_http_client()

    membership = None
    try:
        url = f"{settings.project_service_url}/projects/{project_id}/check-membership"
        resp = await client.get(
            url,
            params={"user_id": current_user.user_id},
            headers={"x-internal-service-key": settings.internal_service_key},
        )
        if resp.status_code == 200:
            membership = resp.json()
    except Exception as e:
        logger.warning("Failed to check project membership for task: %s", e)

    return project_id, membership


def require_task_project_permission(permission: ProjectPermission):
    """Permission dependency when only `task_id` is available.

    Resolves the task's project_id from DB, then checks project membership.
    """

    async def _dependency(
        task_id: uuid.UUID,
        current_user: TokenData = Depends(get_current_user),
        resolved: tuple[uuid.UUID, Optional[dict[str, Any]]] = Depends(
            _get_membership_for_task
        ),
    ) -> PermissionResult:
        _project_id, membership = resolved
        return check_project_permission(current_user, membership, permission)

    return _dependency

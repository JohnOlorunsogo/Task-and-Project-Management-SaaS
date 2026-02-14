
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData
from shared.auth.rbac import (
    PermissionResult,
    ProjectPermission,
    check_project_permission,
)
from app.dependencies import get_current_user, get_db


async def get_project_membership(
    project_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
) -> Optional[dict[str, Any]]:
    """
    Fetch project membership for the current user via Project Service HTTP call.
    """
    import httpx
    from app.config import get_settings
    settings = get_settings()

    # Create a new client or use a singleton in production
    async with httpx.AsyncClient() as client:
        # project_service_url is e.g. http://project_service:8003
        try:
             url = f"{settings.project_service_url}/projects/{project_id}/check-membership"
             resp = await client.get(url, params={"user_id": current_user.user_id})
             if resp.status_code == 200:
                 return resp.json()
        except Exception as e:
            print(f"Failed to check project membership: {e}")
            pass
    
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

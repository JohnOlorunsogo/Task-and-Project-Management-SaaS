
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData
from shared.auth.rbac import (
    PermissionResult,
    ProjectPermission,
    OrgPermission,
    check_project_permission,
    check_org_permission,
)
from app.dependencies import get_current_user, get_db
from app.models import ProjectMembership


async def get_project_membership(
    project_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[dict[str, Any]]:
    """
    Fetch project membership for the current user.
    """
    stmt = select(ProjectMembership).where(
        ProjectMembership.project_id == project_id,
        ProjectMembership.user_id == uuid.UUID(current_user.user_id),
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()
    
    if membership:
        return {"role": membership.role}
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


def require_org_permission(permission: OrgPermission):
    """
    Request-scoped dependency to check org permissions.
    """
    async def _dependency(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        check_org_permission(current_user, permission)
        return current_user

    return _dependency

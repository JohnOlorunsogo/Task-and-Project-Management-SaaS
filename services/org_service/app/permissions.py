"""Organization Service Permissions."""

from __future__ import annotations

import uuid

from fastapi import Depends

from shared.auth import TokenData
from shared.auth.rbac import (
    OrgPermission, OrgRole, check_org_permission, check_org_role
)

from app.dependencies import get_current_user


def require_org_permission(permission: OrgPermission):
    """
    FastAPI dependency factory for checking org-level permissions.
    Injects current_user and verifies org_id from the path matches
    the user's current org context (org-match guard).
    """
    async def _dependency(
        org_id: uuid.UUID,
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        check_org_permission(current_user, permission, target_org_id=str(org_id))
        return current_user
    return _dependency


def require_org_role(*roles: OrgRole):
    """
    FastAPI dependency factory for checking org-level roles.
    Injects current_user and verifies org_id from the path matches.
    """
    async def _dependency(
        org_id: uuid.UUID,
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        # Verify org match first
        if current_user.org_id and current_user.org_id != str(org_id):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted on a different organization",
            )
        check_org_role(current_user, list(roles))
        return current_user
    return _dependency

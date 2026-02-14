"""Organization Service Permissions."""

from __future__ import annotations

from fastapi import Depends

from shared.auth import TokenData
from shared.auth.rbac import (
    OrgPermission, OrgRole, check_org_permission, check_org_role
)

from app.dependencies import get_current_user


def require_org_permission(permission: OrgPermission):
    """
    FastAPI dependency factory for checking org-level permissions.
    Injects current_user from app dependencies.
    """
    async def _dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        check_org_permission(current_user, permission)
        return current_user
    return _dependency


def require_org_role(*roles: OrgRole):
    """
    FastAPI dependency factory for checking org-level roles.
    Injects current_user from app dependencies.
    """
    async def _dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        check_org_role(current_user, list(roles))
        return current_user
    return _dependency

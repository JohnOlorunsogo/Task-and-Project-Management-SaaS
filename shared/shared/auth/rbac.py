"""RBAC permission enforcement for org-level and project-level roles."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from shared.auth import TokenData



# Role Definitions

class OrgRole(str, Enum):
    ORG_ADMIN = "org_admin"
    PROJ_ADMIN = "proj_admin"
    MEMBER = "member"


class ProjectRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    TEAM_MEMBER = "team_member"
    VIEWER = "viewer"


# Permission Definitions

# Permission Definitions

class ProjectPermission(str, Enum):
    # Project-level
    DELETE_PROJECT = "delete_project"
    EDIT_PROJECT = "edit_project"
    MANAGE_MEMBERS = "manage_members"
    ASSIGN_ROLES = "assign_roles"
    CREATE_TASK = "create_task"
    EDIT_ANY_TASK = "edit_any_task"
    DELETE_ANY_TASK = "delete_any_task"
    EDIT_ASSIGNED_TASK = "edit_assigned_task"
    DELETE_ASSIGNED_TASK = "delete_assigned_task"
    ASSIGN_TASK = "assign_task"
    CHANGE_STATUS = "change_status"
    POST_COMMENT = "post_comment"
    LOG_TIME = "log_time"
    MANAGE_ATTACHMENTS = "manage_attachments"
    VIEW = "view"


class OrgPermission(str, Enum):
    # Org-level
    MANAGE_ORG_MEMBERS = "manage_org_members"
    MANAGE_ORG_ROLES = "manage_org_roles"
    MANAGE_PROJECTS = "manage_projects"  # Create/Delete projects & templates
    MANAGE_TEAMS = "manage_teams"
    MANAGE_ORG_SETTINGS = "manage_org_settings"
    VIEW_ANALYTICS = "view_analytics"


# Project role → set of permissions
PROJECT_PERMISSIONS: dict[ProjectRole, set[ProjectPermission]] = {
    ProjectRole.OWNER: {
        ProjectPermission.DELETE_PROJECT, ProjectPermission.EDIT_PROJECT, ProjectPermission.MANAGE_MEMBERS,
        ProjectPermission.ASSIGN_ROLES, ProjectPermission.CREATE_TASK, ProjectPermission.EDIT_ANY_TASK,
        ProjectPermission.DELETE_ANY_TASK, ProjectPermission.ASSIGN_TASK, ProjectPermission.CHANGE_STATUS,
        ProjectPermission.POST_COMMENT, ProjectPermission.LOG_TIME, ProjectPermission.MANAGE_ATTACHMENTS,
        ProjectPermission.VIEW,
    },
    ProjectRole.ADMIN: {
        ProjectPermission.EDIT_PROJECT, ProjectPermission.MANAGE_MEMBERS, ProjectPermission.ASSIGN_ROLES,
        ProjectPermission.CREATE_TASK, ProjectPermission.EDIT_ANY_TASK, ProjectPermission.DELETE_ANY_TASK,
        ProjectPermission.ASSIGN_TASK, ProjectPermission.CHANGE_STATUS, ProjectPermission.POST_COMMENT,
        ProjectPermission.LOG_TIME, ProjectPermission.MANAGE_ATTACHMENTS, ProjectPermission.VIEW,
    },
    ProjectRole.PROJECT_MANAGER: {
        ProjectPermission.CREATE_TASK, ProjectPermission.EDIT_ANY_TASK, ProjectPermission.DELETE_ANY_TASK,
        ProjectPermission.ASSIGN_TASK, ProjectPermission.CHANGE_STATUS, ProjectPermission.POST_COMMENT,
        ProjectPermission.LOG_TIME, ProjectPermission.MANAGE_ATTACHMENTS, ProjectPermission.VIEW,
    },
    ProjectRole.TEAM_MEMBER: {
        ProjectPermission.CREATE_TASK, ProjectPermission.EDIT_ASSIGNED_TASK, ProjectPermission.DELETE_ASSIGNED_TASK,
        ProjectPermission.CHANGE_STATUS, ProjectPermission.POST_COMMENT, ProjectPermission.LOG_TIME,
        ProjectPermission.MANAGE_ATTACHMENTS, ProjectPermission.VIEW,
    },
    ProjectRole.VIEWER: {
        ProjectPermission.VIEW,
    },
}

# Org role -> set of permissions
ORG_PERMISSIONS: dict[OrgRole, set[OrgPermission]] = {
    OrgRole.ORG_ADMIN: {
        OrgPermission.MANAGE_ORG_MEMBERS, OrgPermission.MANAGE_ORG_ROLES,
        OrgPermission.MANAGE_PROJECTS, OrgPermission.MANAGE_TEAMS,
        OrgPermission.MANAGE_ORG_SETTINGS, OrgPermission.VIEW_ANALYTICS,
    },
    OrgRole.PROJ_ADMIN: {
        OrgPermission.MANAGE_PROJECTS, OrgPermission.MANAGE_TEAMS,
    },
    OrgRole.MEMBER: set(), # Members have no implicit org-level management permissions
}


class PermissionResult(BaseModel):
    """Result of permission check, includes role and whether assignment must be verified."""
    role: str
    user_id: str
    org_id: str
    check_assignment: bool = False


# Org-Level RBAC Dependency

def require_org_permission(permission: OrgPermission):
    """
    FastAPI dependency factory: require a specific org-level permission.
    """
    async def _dependency(current_user: TokenData) -> TokenData:
        if not current_user.org_role:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization role assigned",
            )
        
        user_role = OrgRole(current_user.org_role)
        allowed = ORG_PERMISSIONS.get(user_role, set())

        if permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Org Permission '{permission.value}' denied for role '{user_role.value}'",
            )
        
        return current_user

    return _dependency


def require_org_role(*roles: OrgRole):
    """
    FastAPI dependency factory: require the user to have one of the given org-level roles.
    DEPRECATED: Prefer require_org_permission for granular control.
    """

    async def _dependency(current_user: TokenData) -> TokenData:
        if not current_user.org_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization role assigned",
            )
        user_role = OrgRole(current_user.org_role)
        # OrgAdmin always passes
        if OrgRole.ORG_ADMIN in roles and user_role == OrgRole.ORG_ADMIN:
            return current_user
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in roles]}",
            )
        return current_user

    return _dependency


# Project-Level RBAC Dependency

def require_project_permission(permission: ProjectPermission):
    """
    FastAPI dependency factory: require a specific project-level permission.

    Usage in route:
        @router.post("/tasks")
        async def create_task(
            perm: PermissionResult = Depends(require_project_permission(ProjectPermission.CREATE_TASK)),
            ...
        ):

    The calling service must provide a `get_project_membership` function
    via the dependency override system.
    """

    async def _dependency(
        project_id: uuid.UUID,
        current_user: TokenData,
        membership: Optional[dict[str, Any]] = None,
    ) -> PermissionResult:
        # OrgAdmin bypasses project-level checks
        if current_user.org_role == OrgRole.ORG_ADMIN.value:
            return PermissionResult(
                role="org_admin",
                user_id=current_user.user_id,
                org_id=current_user.org_id or "",
            )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this project",
            )

        role = ProjectRole(membership["role"])
        allowed = PROJECT_PERMISSIONS.get(role, set())

        if permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' denied for role '{role.value}'",
            )

        check_assignment = (
            role == ProjectRole.TEAM_MEMBER
            and permission in (ProjectPermission.EDIT_ASSIGNED_TASK, ProjectPermission.DELETE_ASSIGNED_TASK)
        )

        return PermissionResult(
            role=role.value,
            user_id=current_user.user_id,
            org_id=current_user.org_id or "",
            check_assignment=check_assignment,
        )

    return _dependency

"""Project Service API Routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from shared.auth import TokenData
from shared.auth.rbac import Permission, ProjectRole

from app.dependencies import get_current_user, get_project_service
from app.schemas import (
    AddProjectMemberRequest, ChangeProjectRoleRequest, CreateFromTemplateRequest,
    CreateProjectRequest, CreateStatusRequest, CustomStatusResponse,
    ProjectMemberResponse, ProjectResponse, UpdateProjectRequest, UpdateStatusRequest,
)
from app.services import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


# ---- Project CRUD ----

@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: CreateProjectRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    org_id = current_user.org_id
    if not org_id:
        from fastapi import HTTPException
        raise HTTPException(400, "No organization context")
    return await project_service.create_project(org_id, current_user.user_id, data)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    return await project_service.list_user_projects(
        current_user.org_id or "", current_user.user_id
    )


@router.get("/all", response_model=list[ProjectResponse])
async def list_all_projects(
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    """List all projects in org (OrgAdmin only in practice)."""
    return await project_service.list_projects(current_user.org_id or "")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await project_service.get_project(project_id, current_user.org_id or "")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: UpdateProjectRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await project_service.update_project(project_id, current_user.org_id or "", data)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    # RBAC: Only owner can delete — enforced at gateway/RBAC layer
    await project_service.delete_project(project_id, current_user.org_id or "")


# ---- Templates ----

@router.post("/templates", response_model=ProjectResponse, status_code=201)
async def create_template(
    data: CreateProjectRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await project_service.create_template(
        current_user.org_id or "", current_user.user_id, data
    )


@router.get("/templates/list", response_model=list[ProjectResponse])
async def list_templates(
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    return await project_service.list_templates(current_user.org_id or "")


@router.post("/from-template/{template_id}", response_model=ProjectResponse, status_code=201)
async def create_from_template(
    template_id: uuid.UUID,
    data: CreateFromTemplateRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await project_service.create_from_template(
        template_id, current_user.org_id or "", current_user.user_id, data
    )


# ---- Members ----

@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_members(
    project_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectMemberResponse]:
    return await project_service.list_members(project_id)


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=201)
async def add_member(
    project_id: uuid.UUID,
    data: AddProjectMemberRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    return await project_service.add_member(project_id, data)


@router.put("/{project_id}/members/{user_id}/role", response_model=ProjectMemberResponse)
async def change_member_role(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ChangeProjectRoleRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    return await project_service.change_member_role(project_id, user_id, data)


@router.delete("/{project_id}/members/{user_id}", status_code=204)
async def remove_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    await project_service.remove_member(project_id, user_id)


# ---- Custom Statuses ----

@router.get("/{project_id}/statuses", response_model=list[CustomStatusResponse])
async def list_statuses(
    project_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> list[CustomStatusResponse]:
    return await project_service.list_statuses(project_id)


@router.post("/{project_id}/statuses", response_model=CustomStatusResponse, status_code=201)
async def create_status(
    project_id: uuid.UUID,
    data: CreateStatusRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> CustomStatusResponse:
    return await project_service.create_status(project_id, data)


@router.put("/{project_id}/statuses/{status_id}", response_model=CustomStatusResponse)
async def update_status(
    project_id: uuid.UUID,
    status_id: uuid.UUID,
    data: UpdateStatusRequest,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> CustomStatusResponse:
    return await project_service.update_status(status_id, data)


@router.delete("/{project_id}/statuses/{status_id}", status_code=204)
async def delete_status(
    project_id: uuid.UUID,
    status_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    await project_service.delete_status(status_id)

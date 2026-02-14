"""Organization Service API Routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from shared.auth import TokenData
from shared.auth.rbac import OrgRole, require_org_role

from app.dependencies import get_current_user, get_org_service
from app.schemas import (
    AddMemberRequest, AddTeamMemberRequest, ChangeMemberRoleRequest,
    CreateOrgRequest, CreateTeamRequest, OrgMemberResponse, OrgResponse,
    TeamMemberResponse, TeamResponse, UpdateOrgRequest,
)
from app.services import OrgService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ---- Organization CRUD ----

@router.post("", response_model=OrgResponse, status_code=201)
async def create_org(
    data: CreateOrgRequest,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> OrgResponse:
    return await org_service.create_org(data, current_user.user_id)


@router.get("/me", response_model=list[OrgResponse])
async def list_my_orgs(
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> list[OrgResponse]:
    return await org_service.list_user_orgs(current_user.user_id)


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> OrgResponse:
    return await org_service.get_org(org_id)


@router.put("/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: uuid.UUID,
    data: UpdateOrgRequest,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> OrgResponse:
    return await org_service.update_org(org_id, data)


# ---- Members ----

@router.get("/{org_id}/members", response_model=list[OrgMemberResponse])
async def list_members(
    org_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> list[OrgMemberResponse]:
    return await org_service.list_members(org_id)


@router.post("/{org_id}/members", response_model=OrgMemberResponse, status_code=201)
async def add_member(
    org_id: uuid.UUID,
    data: AddMemberRequest,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> OrgMemberResponse:
    return await org_service.add_member(org_id, data)


@router.delete("/{org_id}/members/{user_id}", status_code=204)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> None:
    await org_service.remove_member(org_id, user_id)


@router.put("/{org_id}/members/{user_id}/role", response_model=OrgMemberResponse)
async def change_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ChangeMemberRoleRequest,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> OrgMemberResponse:
    return await org_service.change_member_role(org_id, user_id, data)


# ---- Teams ----

@router.post("/{org_id}/teams", response_model=TeamResponse, status_code=201)
async def create_team(
    org_id: uuid.UUID,
    data: CreateTeamRequest,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> TeamResponse:
    return await org_service.create_team(org_id, data)


@router.get("/{org_id}/teams", response_model=list[TeamResponse])
async def list_teams(
    org_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> list[TeamResponse]:
    return await org_service.list_teams(org_id)


@router.post("/{org_id}/teams/{team_id}/members", response_model=TeamMemberResponse, status_code=201)
async def add_team_member(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    data: AddTeamMemberRequest,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> TeamMemberResponse:
    return await org_service.add_team_member(team_id, data)


@router.get("/{org_id}/teams/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> list[TeamMemberResponse]:
    return await org_service.list_team_members(team_id)


@router.delete("/{org_id}/teams/{team_id}/members/{user_id}", status_code=204)
async def remove_team_member(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    org_service: OrgService = Depends(get_org_service),
) -> None:
    await org_service.remove_team_member(team_id, user_id)

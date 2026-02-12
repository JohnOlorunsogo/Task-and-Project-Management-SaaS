"""Organization Service Pydantic Schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Organization Schemas
# =============================================================================

class CreateOrgRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")


class UpdateOrgRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)


class OrgResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime


# =============================================================================
# Membership Schemas
# =============================================================================

class AddMemberRequest(BaseModel):
    user_id: uuid.UUID
    role: str = Field(default="member", pattern=r"^(org_admin|proj_admin|member)$")


class ChangeMemberRoleRequest(BaseModel):
    role: str = Field(pattern=r"^(org_admin|proj_admin|member)$")


class OrgMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime


# =============================================================================
# Team Schemas
# =============================================================================

class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime


class AddTeamMemberRequest(BaseModel):
    user_id: uuid.UUID


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

"""Project Service Pydantic Schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Project Schemas
# =============================================================================

class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: Optional[str]
    owner_id: uuid.UUID
    start_date: Optional[date]
    end_date: Optional[date]
    is_template: bool
    created_at: datetime


class CreateFromTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# =============================================================================
# Membership Schemas
# =============================================================================

class AddProjectMemberRequest(BaseModel):
    user_id: uuid.UUID
    role: str = Field(default="team_member", pattern=r"^(owner|admin|project_manager|team_member|viewer)$")


class ChangeProjectRoleRequest(BaseModel):
    role: str = Field(pattern=r"^(owner|admin|project_manager|team_member|viewer)$")


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime
    # Enriched fields
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserProjectMembershipResponse(BaseModel):
    """Response for checking membership of a user in a project."""
    model_config = ConfigDict(from_attributes=True)
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: str


# =============================================================================
# Custom Status Schemas
# =============================================================================

class CreateStatusRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    position: int = Field(default=0, ge=0)


class UpdateStatusRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    position: Optional[int] = Field(default=None, ge=0)


class CustomStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    position: int
    color: Optional[str]
    is_default: bool
    created_at: datetime

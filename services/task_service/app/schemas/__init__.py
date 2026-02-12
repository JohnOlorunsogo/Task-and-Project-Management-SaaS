"""Task Service Pydantic Schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Task Schemas
# =============================================================================

class CreateTaskRequest(BaseModel):
    project_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    status_id: Optional[uuid.UUID] = None
    status_name: Optional[str] = "To Do"
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    custom_properties: Optional[dict[str, Any]] = None
    assignee_ids: Optional[list[uuid.UUID]] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    status_id: Optional[uuid.UUID] = None
    status_name: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern=r"^(low|medium|high|critical)$")
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    custom_properties: Optional[dict[str, Any]] = None
    position: Optional[int] = None


class TaskAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    assigned_at: datetime


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    org_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    title: str
    description: Optional[str]
    status_id: Optional[uuid.UUID]
    status_name: Optional[str]
    priority: str
    due_date: Optional[datetime]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    custom_properties: Optional[dict[str, Any]]
    position: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    assignments: list[TaskAssignmentResponse] = []
    subtask_count: int = 0


class TaskListResponse(BaseModel):
    """Lightweight task for list views."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    status_name: Optional[str]
    priority: str
    due_date: Optional[datetime]
    position: int
    assignee_count: int = 0
    subtask_count: int = 0


# =============================================================================
# Sub-task
# =============================================================================

class CreateSubtaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    due_date: Optional[datetime] = None
    assignee_ids: Optional[list[uuid.UUID]] = None


# =============================================================================
# Dependency Schemas
# =============================================================================

class CreateDependencyRequest(BaseModel):
    predecessor_id: uuid.UUID
    dependency_type: str = Field(default="finish_to_start")


class TaskDependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    dependency_type: str


# =============================================================================
# Comment Schemas
# =============================================================================

class CreateCommentRequest(BaseModel):
    content: str = Field(min_length=1)
    parent_id: Optional[uuid.UUID] = None
    mentions: Optional[list[uuid.UUID]] = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    author_id: uuid.UUID
    content: str
    mentions: Optional[list]
    created_at: datetime
    updated_at: datetime
    replies: list["CommentResponse"] = []


# =============================================================================
# Time Entry Schemas
# =============================================================================

class CreateTimeEntryRequest(BaseModel):
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    description: Optional[str] = None


class TimeEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    description: Optional[str]
    created_at: datetime


class StartTimerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime


class StopTimerRequest(BaseModel):
    pass  # No body needed


# =============================================================================
# Task Reorder
# =============================================================================

class ReorderTaskRequest(BaseModel):
    position: int = Field(ge=0)
    status_id: Optional[uuid.UUID] = None
    status_name: Optional[str] = None


# =============================================================================
# Assignment
# =============================================================================

class AssignTaskRequest(BaseModel):
    user_id: uuid.UUID


# =============================================================================
# View Responses
# =============================================================================

class KanbanColumn(BaseModel):
    status_id: Optional[uuid.UUID]
    status_name: str
    tasks: list[TaskListResponse]


class KanbanResponse(BaseModel):
    columns: list[KanbanColumn]


class GanttTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    due_date: Optional[datetime]
    dependencies: list[uuid.UUID] = []
    progress: float = 0.0


class CalendarTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    due_date: datetime
    priority: str
    status_name: Optional[str]

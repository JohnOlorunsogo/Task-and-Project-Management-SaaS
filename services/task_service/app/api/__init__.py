"""Task Service API Routes."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status

from shared.auth import TokenData

from app.dependencies import get_current_user, get_task_service
from app.schemas import (
    AssignTaskRequest, CalendarTaskResponse, CommentResponse,
    CreateCommentRequest, CreateDependencyRequest, CreateSubtaskRequest,
    CreateTaskRequest, CreateTimeEntryRequest, GanttTaskResponse,
    KanbanResponse, ReorderTaskRequest, StartTimerResponse,
    TaskAssignmentResponse, TaskDependencyResponse, TaskListResponse,
    TaskResponse, TimeEntryResponse, UpdateTaskRequest,
)
from app.services import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ---- Task CRUD ----

@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: CreateTaskRequest,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required",
        )
    return await task_service.create_task(
        current_user.org_id, current_user.user_id, data
    )


@router.get("", response_model=list[TaskListResponse])
async def list_tasks(
    project_id: Optional[uuid.UUID] = Query(default=None),
    assignee_id: Optional[uuid.UUID] = Query(default=None),
    status_name: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[TaskListResponse]:
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required",
        )
    return await task_service.list_tasks(
        org_id=current_user.org_id,
        project_id=project_id,
        assignee_id=assignee_id,
        status_name=status_name,
        priority=priority,
    )


@router.get("/my", response_model=list[TaskListResponse])
async def my_tasks(
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[TaskListResponse]:
    """Get tasks assigned to the current user."""
    return await task_service.list_tasks(
        org_id=current_user.org_id or "",
        assignee_id=uuid.UUID(current_user.user_id),
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await task_service.get_task(task_id, current_user.org_id or "")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: UpdateTaskRequest,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await task_service.update_task(
        task_id, current_user.org_id or "", current_user.user_id, data
    )


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> None:
    await task_service.delete_task(task_id, current_user.org_id or "", current_user.user_id)


# ---- Comments ----

@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=201)
async def add_comment(
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    data: CreateCommentRequest,
    perm: PermissionResult = Depends(require_project_permission(ProjectPermission.POST_COMMENT)),
    task_service: TaskService = Depends(get_task_service),
) -> TaskCommentResponse:
    return await task_service.add_comment(task_id, perm.user_id, data)


@router.get("/{task_id}/comments", response_model=list[TaskCommentResponse])
async def list_comments(
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    perm: PermissionResult = Depends(require_project_permission(ProjectPermission.VIEW)),
    task_service: TaskService = Depends(get_task_service),
) -> list[TaskCommentResponse]:
    return await task_service.list_comments(task_id)


# ---- Time Logs ----

@router.post("/{task_id}/time-logs", response_model=TimeLogResponse, status_code=201)
async def log_time(
    task_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TimeEntryResponse:
    return await task_service.log_time(
        task_id, current_user.org_id or "", current_user.user_id, data
    )


@router.post("/{task_id}/time-entries/start", response_model=StartTimerResponse, status_code=201)
async def start_timer(
    task_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> StartTimerResponse:
    return await task_service.start_timer(
        task_id, current_user.org_id or "", current_user.user_id
    )


@router.put("/{task_id}/time-entries/{entry_id}/stop", response_model=TimeEntryResponse)
async def stop_timer(
    task_id: uuid.UUID,
    entry_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TimeEntryResponse:
    return await task_service.stop_timer(task_id, entry_id, current_user.user_id)


@router.get("/{task_id}/time-entries", response_model=list[TimeEntryResponse])
async def list_time_entries(
    task_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[TimeEntryResponse]:
    return await task_service.list_time_entries(task_id)


# ---- Views ----

@router.get("/views/kanban", response_model=KanbanResponse)
async def kanban_view(
    project_id: uuid.UUID = Query(...),
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> KanbanResponse:
    return await task_service.get_kanban(project_id, current_user.org_id or "")


@router.get("/views/gantt", response_model=list[GanttTaskResponse])
async def gantt_view(
    project_id: uuid.UUID = Query(...),
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[GanttTaskResponse]:
    return await task_service.get_gantt(project_id, current_user.org_id or "")


@router.get("/views/calendar", response_model=list[CalendarTaskResponse])
async def calendar_view(
    project_id: uuid.UUID = Query(...),
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[CalendarTaskResponse]:
    return await task_service.get_calendar(project_id, current_user.org_id or "")

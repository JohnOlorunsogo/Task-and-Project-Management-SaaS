"""Task Service API Routes."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status

from shared.auth import TokenData
from shared.auth.rbac import PermissionResult, ProjectPermission

from app.permissions import (
    get_project_membership,
    require_project_permission,
    require_task_project_permission,
)
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


def _require_org_id(current_user: TokenData) -> str:
    """Extract org_id from token, raising 400 if missing."""
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required",
        )
    return current_user.org_id


# ---- Task CRUD ----


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: CreateTaskRequest,
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Create a new task.

    Requires CREATE_TASK permission on the target project.
    Permission is checked inline because project_id comes from the request body.
    """
    org_id = _require_org_id(current_user)

    # Inline permission check (project_id is in the body, not in URL)
    from shared.auth.rbac import check_project_permission
    membership = await get_project_membership(data.project_id, current_user)
    check_project_permission(current_user, membership, ProjectPermission.CREATE_TASK)

    return await task_service.create_task(org_id, current_user.user_id, data)


@router.get("", response_model=list[TaskListResponse])
async def list_tasks(
    project_id: Optional[uuid.UUID] = Query(default=None),
    assignee_id: Optional[uuid.UUID] = Query(default=None),
    status_name: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    current_user: TokenData = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[TaskListResponse]:
    """List tasks, optionally filtered by project.

    When project_id is provided, VIEW permission is checked.
    """
    org_id = _require_org_id(current_user)

    # If project_id is provided, verify VIEW permission
    if project_id:
        from shared.auth.rbac import check_project_permission
        membership = await get_project_membership(project_id, current_user)
        check_project_permission(current_user, membership, ProjectPermission.VIEW)

    return await task_service.list_tasks(
        org_id=org_id,
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
    """Get tasks assigned to the current user.

    No project-level check — user only sees tasks assigned to them.
    """
    org_id = _require_org_id(current_user)
    return await task_service.list_tasks(
        org_id=org_id,
        assignee_id=uuid.UUID(current_user.user_id),
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Get a single task. Requires VIEW permission on the task's project."""
    return await task_service.get_task(task_id, perm.org_id)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: UpdateTaskRequest,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.EDIT_TASK)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update a task. Requires EDIT_TASK permission on the task's project."""
    return await task_service.update_task(task_id, perm.org_id, perm.user_id, data)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.DELETE_TASK)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task. Requires DELETE_TASK permission on the task's project."""
    await task_service.delete_task(task_id, perm.org_id, perm.user_id)


# ---- Comments ----

@router.post("/{task_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    task_id: uuid.UUID,
    data: CreateCommentRequest,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.POST_COMMENT)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> CommentResponse:
    """Add a comment to a task. Requires POST_COMMENT permission."""
    return await task_service.add_comment(task_id, perm.org_id, perm.user_id, data)


@router.get("/{task_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    task_id: uuid.UUID,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> list[CommentResponse]:
    """List comments on a task. Requires VIEW permission."""
    return await task_service.list_comments(task_id)


# ---- Time Logs ----

@router.post("/{task_id}/time-logs", response_model=TimeEntryResponse, status_code=201)
async def log_time(
    task_id: uuid.UUID,
    data: CreateTimeEntryRequest,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> TimeEntryResponse:
    """Log time on a task. Requires VIEW (member) permission."""
    return await task_service.log_time(task_id, perm.org_id, perm.user_id, data)


@router.post("/{task_id}/time-entries/start", response_model=StartTimerResponse, status_code=201)
async def start_timer(
    task_id: uuid.UUID,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> StartTimerResponse:
    """Start a timer on a task. Requires VIEW (member) permission."""
    return await task_service.start_timer(task_id, perm.org_id, perm.user_id)


@router.put("/{task_id}/time-entries/{entry_id}/stop", response_model=TimeEntryResponse)
async def stop_timer(
    task_id: uuid.UUID,
    entry_id: uuid.UUID,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> TimeEntryResponse:
    """Stop a running timer. Requires VIEW (member) permission."""
    return await task_service.stop_timer(task_id, entry_id, perm.user_id)


@router.get("/{task_id}/time-entries", response_model=list[TimeEntryResponse])
async def list_time_entries(
    task_id: uuid.UUID,
    perm: PermissionResult = Depends(
        require_task_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> list[TimeEntryResponse]:
    """List time entries for a task. Requires VIEW (member) permission."""
    return await task_service.list_time_entries(task_id)


# ---- Views ----

@router.get("/views/kanban", response_model=KanbanResponse)
async def kanban_view(
    project_id: uuid.UUID = Query(...),
    perm: PermissionResult = Depends(
        require_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> KanbanResponse:
    """Kanban board view. Requires VIEW permission on the project."""
    return await task_service.get_kanban(project_id, perm.org_id)


@router.get("/views/gantt", response_model=list[GanttTaskResponse])
async def gantt_view(
    project_id: uuid.UUID = Query(...),
    perm: PermissionResult = Depends(
        require_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> list[GanttTaskResponse]:
    """Gantt chart view. Requires VIEW permission on the project."""
    return await task_service.get_gantt(project_id, perm.org_id)


@router.get("/views/calendar", response_model=list[CalendarTaskResponse])
async def calendar_view(
    project_id: uuid.UUID = Query(...),
    perm: PermissionResult = Depends(
        require_project_permission(ProjectPermission.VIEW)
    ),
    task_service: TaskService = Depends(get_task_service),
) -> list[CalendarTaskResponse]:
    """Calendar view. Requires VIEW permission on the project."""
    return await task_service.get_calendar(project_id, perm.org_id)

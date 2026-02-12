"""Task Service - Business Logic."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.events import (
    COMMENT_ADDED, TASK_ASSIGNED, TASK_CREATED, TASK_DELETED,
    TASK_STATUS_CHANGED, TASK_UNASSIGNED, TASK_UPDATED, TOPICS,
)
from shared.events.producer import event_producer

from app.models import Comment, Task, TaskAssignment, TaskDependency, TimeEntry
from app.schemas import (
    AssignTaskRequest, CalendarTaskResponse, CommentResponse,
    CreateCommentRequest, CreateDependencyRequest, CreateSubtaskRequest,
    CreateTaskRequest, CreateTimeEntryRequest, GanttTaskResponse,
    KanbanColumn, KanbanResponse, ReorderTaskRequest, StartTimerResponse,
    TaskAssignmentResponse, TaskDependencyResponse, TaskListResponse,
    TaskResponse, TimeEntryResponse, UpdateTaskRequest,
)


class TaskService:
    """Task business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Task CRUD ----

    async def create_task(
        self, org_id: str, user_id: str, data: CreateTaskRequest
    ) -> TaskResponse:
        task = Task(
            project_id=data.project_id,
            org_id=uuid.UUID(org_id),
            title=data.title,
            description=data.description,
            status_id=data.status_id,
            status_name=data.status_name or "To Do",
            priority=data.priority,
            due_date=data.due_date,
            start_date=data.start_date,
            end_date=data.end_date,
            custom_properties=data.custom_properties or {},
            created_by=uuid.UUID(user_id),
        )
        self.db.add(task)
        await self.db.flush()

        # Create assignments
        if data.assignee_ids:
            for uid in data.assignee_ids:
                assignment = TaskAssignment(task_id=task.id, user_id=uid)
                self.db.add(assignment)
            await self.db.flush()

        await event_producer.publish(
            TOPICS["tasks"],
            {
                "event_type": TASK_CREATED,
                "task_id": str(task.id),
                "project_id": str(task.project_id),
                "org_id": org_id,
                "title": task.title,
                "assignees": [str(uid) for uid in (data.assignee_ids or [])],
                "actor_id": user_id,
            },
            key=str(task.id),
        )

        return await self._get_task_response(task.id)

    async def get_task(self, task_id: uuid.UUID, org_id: str) -> TaskResponse:
        return await self._get_task_response(task_id)

    async def list_tasks(
        self,
        org_id: str,
        project_id: Optional[uuid.UUID] = None,
        assignee_id: Optional[uuid.UUID] = None,
        status_name: Optional[str] = None,
        priority: Optional[str] = None,
        parent_only: bool = True,
    ) -> list[TaskListResponse]:
        stmt = select(Task).where(Task.org_id == uuid.UUID(org_id))

        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        if assignee_id:
            stmt = stmt.join(TaskAssignment).where(TaskAssignment.user_id == assignee_id)
        if status_name:
            stmt = stmt.where(Task.status_name == status_name)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if parent_only:
            stmt = stmt.where(Task.parent_id.is_(None))

        stmt = stmt.order_by(Task.position, Task.created_at.desc())
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        responses = []
        for t in tasks:
            # Count subtasks and assignees
            sub_count = await self.db.scalar(
                select(func.count()).select_from(Task).where(Task.parent_id == t.id)
            )
            assign_count = await self.db.scalar(
                select(func.count()).select_from(TaskAssignment).where(TaskAssignment.task_id == t.id)
            )
            responses.append(TaskListResponse(
                id=t.id, project_id=t.project_id, title=t.title,
                status_name=t.status_name, priority=t.priority,
                due_date=t.due_date, position=t.position,
                assignee_count=assign_count or 0, subtask_count=sub_count or 0,
            ))

        return responses

    async def update_task(
        self, task_id: uuid.UUID, org_id: str, user_id: str, data: UpdateTaskRequest
    ) -> TaskResponse:
        stmt = select(Task).where(Task.id == task_id, Task.org_id == uuid.UUID(org_id))
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

        old_status = task.status_name
        changed_fields = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if getattr(task, field) != value:
                changed_fields.append(field)
                setattr(task, field, value)

        await self.db.flush()

        if "status_name" in changed_fields or "status_id" in changed_fields:
            await event_producer.publish(
                TOPICS["tasks"],
                {
                    "event_type": TASK_STATUS_CHANGED,
                    "task_id": str(task_id),
                    "old_status": old_status,
                    "new_status": task.status_name,
                    "actor_id": user_id,
                },
                key=str(task_id),
            )
        elif changed_fields:
            await event_producer.publish(
                TOPICS["tasks"],
                {
                    "event_type": TASK_UPDATED,
                    "task_id": str(task_id),
                    "changed_fields": changed_fields,
                    "actor_id": user_id,
                },
                key=str(task_id),
            )

        return await self._get_task_response(task_id)

    async def delete_task(self, task_id: uuid.UUID, org_id: str, user_id: str) -> None:
        stmt = select(Task).where(Task.id == task_id, Task.org_id == uuid.UUID(org_id))
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

        await self.db.delete(task)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["tasks"],
            {"event_type": TASK_DELETED, "task_id": str(task_id), "actor_id": user_id},
            key=str(task_id),
        )

    # ---- Sub-tasks ----

    async def create_subtask(
        self, parent_id: uuid.UUID, org_id: str, user_id: str, data: CreateSubtaskRequest
    ) -> TaskResponse:
        parent = await self.db.execute(select(Task).where(Task.id == parent_id))
        parent_task = parent.scalar_one_or_none()
        if not parent_task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent task not found")

        subtask = Task(
            project_id=parent_task.project_id,
            org_id=uuid.UUID(org_id),
            parent_id=parent_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            status_name="To Do",
            created_by=uuid.UUID(user_id),
        )
        self.db.add(subtask)
        await self.db.flush()

        if data.assignee_ids:
            for uid in data.assignee_ids:
                self.db.add(TaskAssignment(task_id=subtask.id, user_id=uid))
            await self.db.flush()

        return await self._get_task_response(subtask.id)

    async def list_subtasks(self, parent_id: uuid.UUID) -> list[TaskListResponse]:
        stmt = select(Task).where(Task.parent_id == parent_id).order_by(Task.position)
        result = await self.db.execute(stmt)
        return [
            TaskListResponse(
                id=t.id, project_id=t.project_id, title=t.title,
                status_name=t.status_name, priority=t.priority,
                due_date=t.due_date, position=t.position,
            )
            for t in result.scalars().all()
        ]

    # ---- Assignments ----

    async def assign_task(
        self, task_id: uuid.UUID, data: AssignTaskRequest, actor_id: str
    ) -> TaskAssignmentResponse:
        existing = await self.db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.user_id == data.user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "User already assigned")

        assignment = TaskAssignment(task_id=task_id, user_id=data.user_id)
        self.db.add(assignment)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["tasks"],
            {
                "event_type": TASK_ASSIGNED,
                "task_id": str(task_id),
                "user_id": str(data.user_id),
                "actor_id": actor_id,
            },
            key=str(task_id),
        )

        return TaskAssignmentResponse.model_validate(assignment)

    async def unassign_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = delete(TaskAssignment).where(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")

    # ---- Dependencies ----

    async def add_dependency(
        self, task_id: uuid.UUID, data: CreateDependencyRequest
    ) -> TaskDependencyResponse:
        dep = TaskDependency(
            predecessor_id=data.predecessor_id,
            successor_id=task_id,
            dependency_type=data.dependency_type,
        )
        self.db.add(dep)
        await self.db.flush()
        return TaskDependencyResponse.model_validate(dep)

    async def list_dependencies(self, task_id: uuid.UUID) -> list[TaskDependencyResponse]:
        stmt = select(TaskDependency).where(
            (TaskDependency.predecessor_id == task_id) | (TaskDependency.successor_id == task_id)
        )
        result = await self.db.execute(stmt)
        return [TaskDependencyResponse.model_validate(d) for d in result.scalars().all()]

    async def remove_dependency(self, dep_id: uuid.UUID) -> None:
        stmt = delete(TaskDependency).where(TaskDependency.id == dep_id)
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dependency not found")

    # ---- Reorder (Kanban drag-drop) ----

    async def reorder_task(
        self, task_id: uuid.UUID, org_id: str, data: ReorderTaskRequest
    ) -> TaskResponse:
        stmt = select(Task).where(Task.id == task_id, Task.org_id == uuid.UUID(org_id))
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

        task.position = data.position
        if data.status_id:
            task.status_id = data.status_id
        if data.status_name:
            task.status_name = data.status_name

        await self.db.flush()
        return await self._get_task_response(task_id)

    # ---- Comments ----

    async def add_comment(
        self, task_id: uuid.UUID, org_id: str, user_id: str, data: CreateCommentRequest
    ) -> CommentResponse:
        comment = Comment(
            task_id=task_id,
            parent_id=data.parent_id,
            author_id=uuid.UUID(user_id),
            org_id=uuid.UUID(org_id),
            content=data.content,
            mentions=[str(m) for m in data.mentions] if data.mentions else None,
        )
        self.db.add(comment)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["comments"],
            {
                "event_type": COMMENT_ADDED,
                "comment_id": str(comment.id),
                "task_id": str(task_id),
                "author_id": user_id,
                "mentions": [str(m) for m in (data.mentions or [])],
            },
            key=str(task_id),
        )

        return CommentResponse.model_validate(comment)

    async def list_comments(self, task_id: uuid.UUID) -> list[CommentResponse]:
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id, Comment.parent_id.is_(None))
            .options(selectinload(Comment.replies))
            .order_by(Comment.created_at)
        )
        result = await self.db.execute(stmt)
        return [CommentResponse.model_validate(c) for c in result.scalars().all()]

    # ---- Time Entries ----

    async def log_time(
        self, task_id: uuid.UUID, org_id: str, user_id: str, data: CreateTimeEntryRequest
    ) -> TimeEntryResponse:
        entry = TimeEntry(
            task_id=task_id,
            user_id=uuid.UUID(user_id),
            org_id=uuid.UUID(org_id),
            started_at=data.started_at,
            ended_at=data.ended_at,
            duration_seconds=data.duration_seconds,
            description=data.description,
        )
        self.db.add(entry)
        await self.db.flush()
        return TimeEntryResponse.model_validate(entry)

    async def start_timer(
        self, task_id: uuid.UUID, org_id: str, user_id: str
    ) -> StartTimerResponse:
        # Check for existing running timer
        stmt = select(TimeEntry).where(
            TimeEntry.task_id == task_id,
            TimeEntry.user_id == uuid.UUID(user_id),
            TimeEntry.ended_at.is_(None),
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "Timer already running")

        entry = TimeEntry(
            task_id=task_id,
            user_id=uuid.UUID(user_id),
            org_id=uuid.UUID(org_id),
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        await self.db.flush()
        return StartTimerResponse.model_validate(entry)

    async def stop_timer(
        self, task_id: uuid.UUID, entry_id: uuid.UUID, user_id: str
    ) -> TimeEntryResponse:
        stmt = select(TimeEntry).where(
            TimeEntry.id == entry_id,
            TimeEntry.task_id == task_id,
            TimeEntry.user_id == uuid.UUID(user_id),
            TimeEntry.ended_at.is_(None),
        )
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()
        if not entry:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Running timer not found")

        now = datetime.now(timezone.utc)
        entry.ended_at = now
        entry.duration_seconds = int((now - entry.started_at).total_seconds())
        await self.db.flush()

        return TimeEntryResponse.model_validate(entry)

    async def list_time_entries(self, task_id: uuid.UUID) -> list[TimeEntryResponse]:
        stmt = select(TimeEntry).where(TimeEntry.task_id == task_id).order_by(TimeEntry.started_at.desc())
        result = await self.db.execute(stmt)
        return [TimeEntryResponse.model_validate(e) for e in result.scalars().all()]

    # ---- Views ----

    async def get_kanban(self, project_id: uuid.UUID, org_id: str) -> KanbanResponse:
        stmt = (
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.org_id == uuid.UUID(org_id),
                Task.parent_id.is_(None),
            )
            .order_by(Task.position)
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        # Group by status
        columns: dict[str, list] = {}
        status_order: dict[str, Optional[uuid.UUID]] = {}
        for t in tasks:
            key = t.status_name or "Unknown"
            if key not in columns:
                columns[key] = []
                status_order[key] = t.status_id
            columns[key].append(TaskListResponse(
                id=t.id, project_id=t.project_id, title=t.title,
                status_name=t.status_name, priority=t.priority,
                due_date=t.due_date, position=t.position,
            ))

        return KanbanResponse(
            columns=[
                KanbanColumn(status_id=status_order.get(name), status_name=name, tasks=task_list)
                for name, task_list in columns.items()
            ]
        )

    async def get_gantt(self, project_id: uuid.UUID, org_id: str) -> list[GanttTaskResponse]:
        stmt = (
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.org_id == uuid.UUID(org_id),
                Task.parent_id.is_(None),
            )
            .options(selectinload(Task.predecessors))
            .order_by(Task.start_date.nulls_last(), Task.created_at)
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        return [
            GanttTaskResponse(
                id=t.id, title=t.title,
                start_date=t.start_date, end_date=t.end_date, due_date=t.due_date,
                dependencies=[d.predecessor_id for d in t.predecessors],
            )
            for t in tasks
        ]

    async def get_calendar(self, project_id: uuid.UUID, org_id: str) -> list[CalendarTaskResponse]:
        stmt = (
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.org_id == uuid.UUID(org_id),
                Task.due_date.isnot(None),
            )
            .order_by(Task.due_date)
        )
        result = await self.db.execute(stmt)
        return [CalendarTaskResponse.model_validate(t) for t in result.scalars().all()]

    # ---- Helper ----

    async def _get_task_response(self, task_id: uuid.UUID) -> TaskResponse:
        stmt = (
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.assignments))
        )
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

        sub_count = await self.db.scalar(
            select(func.count()).select_from(Task).where(Task.parent_id == task_id)
        )

        resp = TaskResponse.model_validate(task)
        resp.subtask_count = sub_count or 0
        return resp

    async def is_assigned(self, task_id: uuid.UUID, user_id: str) -> bool:
        stmt = select(TaskAssignment).where(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == uuid.UUID(user_id),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

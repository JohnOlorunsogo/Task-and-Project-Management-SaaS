"""Task Service SQLAlchemy Models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class Task(Base):
    """Task model with support for sub-tasks via parent_id."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))  # Refs project_service custom_statuses
    status_name: Mapped[Optional[str]] = mapped_column(String(100), default="To Do")
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low|medium|high|critical
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    custom_properties: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subtasks = relationship("Task", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Task", back_populates="subtasks", remote_side="Task.id")
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")

    # Dependencies
    predecessors = relationship(
        "TaskDependency", foreign_keys="TaskDependency.successor_id",
        back_populates="successor", cascade="all, delete-orphan"
    )
    successors = relationship(
        "TaskDependency", foreign_keys="TaskDependency.predecessor_id",
        back_populates="predecessor", cascade="all, delete-orphan"
    )


class TaskAssignment(Base):
    """Task → User assignment (many-to-many)."""

    __tablename__ = "task_assignments"
    __table_args__ = (UniqueConstraint("task_id", "user_id", name="uq_task_assignee"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="assignments")


class TaskDependency(Base):
    """Finish-to-start task dependency."""

    __tablename__ = "task_dependencies"
    __table_args__ = (UniqueConstraint("predecessor_id", "successor_id", name="uq_task_dep"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    predecessor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    successor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    dependency_type: Mapped[str] = mapped_column(String(30), default="finish_to_start")

    predecessor = relationship("Task", foreign_keys=[predecessor_id], back_populates="successors")
    successor = relationship("Task", foreign_keys=[successor_id], back_populates="predecessors")


class Comment(Base):
    """Threaded comment on a task."""

    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE")
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[Optional[list]] = mapped_column(JSONB)  # List of user_ids
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    task = relationship("Task", back_populates="comments")
    replies = relationship("Comment", back_populates="parent_comment", cascade="all, delete-orphan")
    parent_comment = relationship("Comment", back_populates="replies", remote_side="Comment.id")


class TimeEntry(Base):
    """Time tracking entry per task/user."""

    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="time_entries")

"""Project Service SQLAlchemy Models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    template_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    memberships = relationship("ProjectMembership", back_populates="project", cascade="all, delete-orphan")
    custom_statuses = relationship("CustomStatus", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class ProjectMembership(Base):
    """Project membership with project-level role."""

    __tablename__ = "project_memberships"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="team_member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="memberships")


class CustomStatus(Base):
    """Custom status/column for Kanban board per project."""

    __tablename__ = "custom_statuses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="custom_statuses")

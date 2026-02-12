"""Notification Service SQLAlchemy Models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Notification(Base):
    """User notification model."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. task.assigned, comment.added
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSONB)  # Additional context (task_id, project_id, etc.)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationPreference(Base):
    """User notification preferences."""

    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    email_on_assignment: Mapped[bool] = mapped_column(Boolean, default=True)
    email_on_mention: Mapped[bool] = mapped_column(Boolean, default=True)
    email_on_due_date: Mapped[bool] = mapped_column(Boolean, default=True)
    email_on_status_change: Mapped[bool] = mapped_column(Boolean, default=False)
    in_app_on_assignment: Mapped[bool] = mapped_column(Boolean, default=True)
    in_app_on_mention: Mapped[bool] = mapped_column(Boolean, default=True)
    in_app_on_due_date: Mapped[bool] = mapped_column(Boolean, default=True)
    in_app_on_status_change: Mapped[bool] = mapped_column(Boolean, default=True)

"""File Service SQLAlchemy Models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class File(Base):
    """File metadata model."""

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True)
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")


class FileVersion(Base):
    """File version for versioning support."""

    __tablename__ = "file_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)  # S3/MinIO object key
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    file = relationship("File", back_populates="versions")

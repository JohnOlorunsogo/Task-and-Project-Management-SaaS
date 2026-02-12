"""File Service - FastAPI Application with MinIO integration."""

from __future__ import annotations

import io
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import timedelta
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.auth import TokenData, get_current_user as _get_current_user_factory
from shared.config import BaseServiceSettings
from shared.database import db_manager
from shared.events import TOPICS, FILE_UPLOADED
from shared.events.producer import event_producer
from shared.models import HealthResponse

from app.models import File as FileModel, FileVersion

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("file_service")


class FileSettings(BaseServiceSettings):
    database_url: str = "postgresql+asyncpg://taskpm_user:taskpm_secret_dev@localhost:5432/file_db"
    service_port: int = 8006


@lru_cache()
def get_settings() -> FileSettings:
    return FileSettings()


settings = get_settings()
get_current_user = _get_current_user_factory(settings.jwt_public_key, settings.jwt_algorithm)

# MinIO client
minio_client: Minio | None = None


def get_minio() -> Minio:
    global minio_client
    if minio_client is None:
        minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=settings.minio_use_ssl,
        )
    return minio_client


async def get_db():
    async for session in db_manager.get_session():
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting File Service on port %s", settings.service_port)

    db_manager.init(settings.database_url)
    from shared.database import Base
    # Models already imported at module level as FileModel and FileVersion
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Ensure MinIO bucket exists
    client = get_minio()
    try:
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
            logger.info("Created MinIO bucket: %s", settings.minio_bucket)
    except Exception:
        logger.warning("Could not connect to MinIO, file operations may fail")

    await event_producer.start(settings.kafka_bootstrap_servers)
    yield

    await event_producer.stop()
    await db_manager.close()


app = FastAPI(
    title="TaskPM File Service",
    description="File upload, versioning, and management",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

router = APIRouter(prefix="/files", tags=["Files"])

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    org_id: uuid.UUID
    project_id: Optional[uuid.UUID]
    task_id: Optional[uuid.UUID]
    original_name: str
    content_type: str
    current_version: int
    created_at: object  # datetime


class FileVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    file_id: uuid.UUID
    version_number: int
    size_bytes: int
    uploaded_by: uuid.UUID
    created_at: object


@router.post("/upload", response_model=FileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[uuid.UUID] = Query(default=None),
    task_id: Optional[uuid.UUID] = Query(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file to S3/MinIO."""
    org_id = current_user.org_id
    if not org_id:
        raise HTTPException(400, "No organization context")

    # Read file content
    content = await file.read()
    size = len(content)

    # Create file record
    file_record = FileModel(
        org_id=uuid.UUID(org_id),
        project_id=project_id,
        task_id=task_id,
        uploaded_by=uuid.UUID(current_user.user_id),
        original_name=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        current_version=1,
    )
    db.add(file_record)
    await db.flush()

    # Upload to MinIO
    storage_key = f"{org_id}/{file_record.id}/v1/{file.filename}"
    client = get_minio()
    client.put_object(
        settings.minio_bucket,
        storage_key,
        io.BytesIO(content),
        length=size,
        content_type=file.content_type or "application/octet-stream",
    )

    # Create version record
    version = FileVersion(
        file_id=file_record.id,
        version_number=1,
        storage_key=storage_key,
        size_bytes=size,
        uploaded_by=uuid.UUID(current_user.user_id),
    )
    db.add(version)
    await db.flush()

    await event_producer.publish(
        TOPICS["files"],
        {
            "event_type": FILE_UPLOADED,
            "file_id": str(file_record.id),
            "org_id": org_id,
            "project_id": str(project_id) if project_id else None,
            "uploaded_by": current_user.user_id,
        },
        key=str(file_record.id),
    )

    return FileResponse.model_validate(file_record)


@router.post("/{file_id}/versions", response_model=FileVersionResponse, status_code=201)
async def upload_new_version(
    file_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new version of an existing file."""
    stmt = select(FileModel).where(FileModel.id == file_id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(404, "File not found")

    content = await file.read()
    size = len(content)

    new_version_num = file_record.current_version + 1
    storage_key = f"{file_record.org_id}/{file_id}/v{new_version_num}/{file.filename}"

    client = get_minio()
    client.put_object(
        settings.minio_bucket,
        storage_key,
        io.BytesIO(content),
        length=size,
        content_type=file.content_type or "application/octet-stream",
    )

    version = FileVersion(
        file_id=file_id,
        version_number=new_version_num,
        storage_key=storage_key,
        size_bytes=size,
        uploaded_by=uuid.UUID(current_user.user_id),
    )
    db.add(version)

    file_record.current_version = new_version_num
    file_record.original_name = file.filename or file_record.original_name
    file_record.content_type = file.content_type or file_record.content_type
    await db.flush()

    return FileVersionResponse.model_validate(version)


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FileModel).where(FileModel.id == file_id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(404, "File not found")
    return FileResponse.model_validate(file_record)


@router.get("/{file_id}/versions", response_model=list[FileVersionResponse])
async def list_versions(
    file_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(FileVersion)
        .where(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_number.desc())
    )
    result = await db.execute(stmt)
    return [FileVersionResponse.model_validate(v) for v in result.scalars().all()]


@router.get("/{file_id}/download")
async def download_file(
    file_id: uuid.UUID,
    version: Optional[int] = Query(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a pre-signed download URL for a file."""
    stmt = select(FileModel).where(FileModel.id == file_id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(404, "File not found")

    # Get the requested version or latest
    if version:
        ver_stmt = select(FileVersion).where(
            FileVersion.file_id == file_id,
            FileVersion.version_number == version,
        )
    else:
        ver_stmt = (
            select(FileVersion)
            .where(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_number.desc())
            .limit(1)
        )
    ver_result = await db.execute(ver_stmt)
    file_version = ver_result.scalar_one_or_none()
    if not file_version:
        raise HTTPException(404, "Version not found")

    # Generate pre-signed URL
    client = get_minio()
    url = client.presigned_get_object(
        settings.minio_bucket,
        file_version.storage_key,
        expires=timedelta(hours=1),
    )

    return {"download_url": url, "filename": file_record.original_name}


@router.get("", response_model=list[FileResponse])
async def list_files(
    project_id: Optional[uuid.UUID] = Query(default=None),
    task_id: Optional[uuid.UUID] = Query(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List files for a project or task."""
    org_id = current_user.org_id
    stmt = select(FileModel).where(FileModel.org_id == uuid.UUID(org_id or ""))
    if project_id:
        stmt = stmt.where(FileModel.project_id == project_id)
    if task_id:
        stmt = stmt.where(FileModel.task_id == task_id)

    stmt = stmt.order_by(FileModel.created_at.desc())
    result = await db.execute(stmt)
    return [FileResponse.model_validate(f) for f in result.scalars().all()]


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: uuid.UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FileModel).where(FileModel.id == file_id).options(selectinload(FileModel.versions))
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    if not file_record:
        raise HTTPException(404, "File not found")

    # Delete from MinIO
    client = get_minio()
    for version in file_record.versions:
        try:
            client.remove_object(settings.minio_bucket, version.storage_key)
        except Exception:
            logger.warning("Failed to delete from MinIO: %s", version.storage_key)

    await db.delete(file_record)
    await db.flush()


app.include_router(router)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(service="file_service")

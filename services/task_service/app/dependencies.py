"""Task Service Dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData, get_current_user as _get_current_user_factory
from shared.database import db_manager

from app.config import get_settings
from app.services import TaskService

_settings = get_settings()


async def get_db() -> AsyncSession:
    async for session in db_manager.get_session():
        yield session


get_current_user = _get_current_user_factory(
    _settings.jwt_public_key, _settings.jwt_algorithm
)


async def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    return TaskService(db=db)

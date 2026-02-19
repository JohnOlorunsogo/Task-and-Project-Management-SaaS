"""Task Service Dependencies."""

from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData, get_current_user as _get_current_user_factory
from shared.auth.resolver import PermissionResolver
from shared.database import db_manager

from app.config import get_settings
from app.services import TaskService

_settings = get_settings()

# Base JWT decoder (identity-only — no role)
_get_jwt_user = _get_current_user_factory(
    _settings.jwt_public_key, _settings.jwt_algorithm
)


async def get_db() -> AsyncSession:
    async for session in db_manager.get_session():
        yield session


def get_redis(request: Request) -> aioredis.Redis:
    """Get the Redis client stored on app state during lifespan."""
    return request.app.state.redis


def get_resolver(request: Request) -> PermissionResolver:
    """Get the PermissionResolver stored on app state during lifespan."""
    return request.app.state.resolver


async def get_current_user(
    jwt_user: TokenData = Depends(_get_jwt_user),
    resolver: PermissionResolver = Depends(get_resolver),
) -> TokenData:
    """Enrich JWT identity with live org_role from Redis cache (or HTTP fallback)."""
    if not jwt_user.org_id:
        return jwt_user

    org_role = await resolver.get_org_role(jwt_user.user_id, jwt_user.org_id)
    jwt_user.org_role = org_role
    return jwt_user


async def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    return TaskService(db=db)

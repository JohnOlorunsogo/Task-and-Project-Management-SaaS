"""Organization Service Dependencies."""

from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData, get_current_user as _get_current_user_factory
from shared.auth.resolver import PermissionResolver
from shared.database import db_manager

from app.config import get_settings
from app.services import OrgService

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
    db: AsyncSession = Depends(get_db),
    resolver: PermissionResolver = Depends(get_resolver),
) -> TokenData:
    """Enrich JWT identity with live org_role from local DB (org owns this data).

    For org_service, we resolve directly from the DB since this service owns
    the org_memberships table. We also push the result to Redis cache for
    other services to read.
    """
    if not jwt_user.org_id:
        return jwt_user

    # Try Redis cache first
    cache_key = f"org_role:{jwt_user.user_id}:{jwt_user.org_id}"
    cached = await resolver.redis.get(cache_key)
    if cached is not None:
        value = cached.decode() if isinstance(cached, bytes) else cached
        jwt_user.org_role = value if value != "__none__" else None
        return jwt_user

    # Direct DB query (org_service owns org_memberships)
    from app.models import OrgMembership
    import uuid
    stmt = select(OrgMembership.role).where(
        OrgMembership.org_id == uuid.UUID(jwt_user.org_id),
        OrgMembership.user_id == uuid.UUID(jwt_user.user_id),
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    # Cache for other services
    from shared.auth.resolver import ROLE_CACHE_TTL
    await resolver.redis.setex(cache_key, ROLE_CACHE_TTL, role or "__none__")

    jwt_user.org_role = role
    return jwt_user


async def get_org_service(
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> OrgService:
    redis_client = getattr(request.app.state, "redis", None) if request else None
    return OrgService(db=db, redis_client=redis_client)

"""Auth Service Dependencies (FastAPI DI)."""

from __future__ import annotations

import redis.asyncio as redis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import TokenData, get_current_user as _get_current_user_factory
from shared.database import db_manager

from app.config import get_settings
from app.services import AuthService

_settings = get_settings()

# Redis client (lazy singleton)
_redis_client: redis.Redis | None = None


async def get_db() -> AsyncSession:
    """Get async database session."""
    async for session in db_manager.get_session():
        yield session


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(_settings.redis_url, decode_responses=True)
    return _redis_client


# Current user dependency using shared JWT verification
get_current_user = _get_current_user_factory(
    _settings.jwt_public_key, _settings.jwt_algorithm
)


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> AuthService:
    """Inject AuthService with all dependencies."""
    return AuthService(
        db=db,
        redis_client=redis_client,
        private_key=_settings.jwt_private_key,
        public_key=_settings.jwt_public_key,
        algorithm=_settings.jwt_algorithm,
        access_expire_minutes=_settings.jwt_access_token_expire_minutes,
        refresh_expire_days=_settings.jwt_refresh_token_expire_days,
    )

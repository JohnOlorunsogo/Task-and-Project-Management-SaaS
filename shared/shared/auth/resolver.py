"""Request-time permission resolver with Redis caching.

Each service reads roles from Redis at request time. Role data is pushed
to Redis by org_service and project_service when memberships change.
If Redis has no entry, the service falls back to an HTTP call to the
owning service and populates the cache.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Cache TTL for role entries (seconds)
ROLE_CACHE_TTL = 300  # 5 minutes

# Module-level HTTP client for fallback lookups
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=5.0)
    return _http_client


class PermissionResolver:
    """Resolves org and project roles at request time using Redis cache."""

    def __init__(
        self,
        redis_client: aioredis.Redis,
        org_service_url: str = "",
        project_service_url: str = "",
        internal_service_key: str = "",
    ) -> None:
        self.redis = redis_client
        self.org_service_url = org_service_url
        self.project_service_url = project_service_url
        self.internal_service_key = internal_service_key

    # ---- Org Role ----

    async def get_org_role(self, user_id: str, org_id: str) -> Optional[str]:
        """Get the user's role in the given org. Returns None if not a member."""
        cache_key = f"org_role:{user_id}:{org_id}"

        # 1. Try cache
        cached = await self.redis.get(cache_key)
        if cached is not None:
            value = cached.decode() if isinstance(cached, bytes) else cached
            return value if value != "__none__" else None

        # 2. Fallback: HTTP to org_service
        role = await self._fetch_org_role(user_id, org_id)

        # 3. Cache result (even negatives, to avoid repeated misses)
        await self.redis.setex(cache_key, ROLE_CACHE_TTL, role or "__none__")
        return role

    async def _fetch_org_role(self, user_id: str, org_id: str) -> Optional[str]:
        """Fetch org role from org_service via HTTP."""
        if not self.org_service_url:
            return None
        try:
            client = _get_http_client()
            url = f"{self.org_service_url}/organizations/memberships"
            resp = await client.get(
                url,
                params={"user_id": user_id},
                headers={"x-internal-service-key": self.internal_service_key},
            )
            if resp.status_code == 200:
                memberships = resp.json()
                for m in memberships:
                    if m.get("org_id") == org_id:
                        return m.get("role")
        except Exception:
            logger.exception("Failed to fetch org role from org_service")
        return None

    # ---- Project Role ----

    async def get_project_role(self, user_id: str, project_id: str) -> Optional[str]:
        """Get the user's role in the given project. Returns None if not a member."""
        cache_key = f"proj_role:{user_id}:{project_id}"

        cached = await self.redis.get(cache_key)
        if cached is not None:
            value = cached.decode() if isinstance(cached, bytes) else cached
            return value if value != "__none__" else None

        role = await self._fetch_project_role(user_id, project_id)
        await self.redis.setex(cache_key, ROLE_CACHE_TTL, role or "__none__")
        return role

    async def _fetch_project_role(self, user_id: str, project_id: str) -> Optional[str]:
        """Fetch project role from project_service via HTTP."""
        if not self.project_service_url:
            return None
        try:
            client = _get_http_client()
            url = f"{self.project_service_url}/projects/{project_id}/check-membership"
            resp = await client.get(
                url,
                params={"user_id": user_id},
                headers={"x-internal-service-key": self.internal_service_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("role")
        except Exception:
            logger.exception("Failed to fetch project role from project_service")
        return None

    # ---- Cache Invalidation (called by org/project services) ----

    @staticmethod
    async def invalidate_org_role(
        redis_client: aioredis.Redis, user_id: str, org_id: str
    ) -> None:
        """Invalidate cached org role. Call when membership changes."""
        await redis_client.delete(f"org_role:{user_id}:{org_id}")

    @staticmethod
    async def invalidate_project_role(
        redis_client: aioredis.Redis, user_id: str, project_id: str
    ) -> None:
        """Invalidate cached project role. Call when membership changes."""
        await redis_client.delete(f"proj_role:{user_id}:{project_id}")

    @staticmethod
    async def set_org_role(
        redis_client: aioredis.Redis, user_id: str, org_id: str, role: str
    ) -> None:
        """Directly set org role in cache (push model from org_service)."""
        await redis_client.setex(f"org_role:{user_id}:{org_id}", ROLE_CACHE_TTL, role)

    @staticmethod
    async def set_project_role(
        redis_client: aioredis.Redis, user_id: str, project_id: str, role: str
    ) -> None:
        """Directly set project role in cache (push model from project_service)."""
        await redis_client.setex(f"proj_role:{user_id}:{project_id}", ROLE_CACHE_TTL, role)

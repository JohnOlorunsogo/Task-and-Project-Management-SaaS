"""Organization Service Configuration."""

from __future__ import annotations

from functools import lru_cache

from shared.config import BaseServiceSettings


class OrgSettings(BaseServiceSettings):
    database_url: str = "postgresql+asyncpg://taskpm_user:taskpm_secret_dev@localhost:5432/org_db"
    service_port: int = 8002
    auth_service_url: str = "http://auth_service:8001"


@lru_cache()
def get_settings() -> OrgSettings:
    return OrgSettings()

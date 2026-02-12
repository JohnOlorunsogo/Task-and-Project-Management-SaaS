"""Project Service Configuration."""

from __future__ import annotations

from functools import lru_cache

from shared.config import BaseServiceSettings


class ProjectSettings(BaseServiceSettings):
    database_url: str = "postgresql+asyncpg://taskpm_user:taskpm_secret_dev@localhost:5432/project_db"
    service_port: int = 8003


@lru_cache()
def get_settings() -> ProjectSettings:
    return ProjectSettings()

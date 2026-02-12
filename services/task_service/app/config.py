"""Task Service Configuration."""

from __future__ import annotations

from functools import lru_cache

from shared.config import BaseServiceSettings


class TaskSettings(BaseServiceSettings):
    database_url: str = "postgresql+asyncpg://taskpm_user:taskpm_secret_dev@localhost:5432/task_db"
    service_port: int = 8004


@lru_cache()
def get_settings() -> TaskSettings:
    return TaskSettings()

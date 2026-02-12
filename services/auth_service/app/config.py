"""Auth Service Configuration."""

from __future__ import annotations

from functools import lru_cache

from shared.config import BaseServiceSettings


class AuthSettings(BaseServiceSettings):
    """Auth service specific settings."""
    database_url: str = "postgresql+asyncpg://taskpm_user:taskpm_secret_dev@localhost:5432/auth_db"
    service_port: int = 8001


@lru_cache()
def get_settings() -> AuthSettings:
    return AuthSettings()

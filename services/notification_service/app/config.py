"""Notification Service Configuration."""

from __future__ import annotations

from functools import lru_cache

from shared.config import BaseServiceSettings


class NotificationSettings(BaseServiceSettings):
    database_url: str = "postgresql+asyncpg://taskpm_user:taskpm_secret_dev@localhost:5432/notification_db"
    service_port: int = 8005
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@taskpm.local"


@lru_cache()
def get_settings() -> NotificationSettings:
    return NotificationSettings()

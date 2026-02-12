"""Shared configuration using Pydantic Settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Base settings inherited by every microservice."""

    # Database
    database_url: str = "postgresql+asyncpg://taskpm_user:taskpm_secret_dev@localhost:5432/auth_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # JWT
    jwt_public_key_path: str = "/app/keys/public.pem"
    jwt_private_key_path: str = "/app/keys/private.pem"
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_bucket: str = "taskpm-files"
    minio_use_ssl: bool = False

    # Service
    service_port: int = 8000
    debug: bool = False

    # Service URLs
    auth_service_url: str = "http://auth_service:8001"
    org_service_url: str = "http://org_service:8002"
    project_service_url: str = "http://project_service:8003"
    task_service_url: str = "http://task_service:8004"
    notification_service_url: str = "http://notification_service:8005"
    file_service_url: str = "http://file_service:8006"

    @property
    def jwt_public_key(self) -> str:
        return Path(self.jwt_public_key_path).read_text()

    @property
    def jwt_private_key(self) -> str:
        return Path(self.jwt_private_key_path).read_text()

    class Config:
        env_file = ".env"
        extra = "ignore"

"""Project Service - FastAPI Application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.auth.resolver import PermissionResolver
from shared.database import db_manager
from shared.events.producer import event_producer
from shared.middleware import OrgScopingMiddleware
from shared.models import HealthResponse

from app.api import router as project_router
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("project_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting Project Service on port %s", settings.service_port)

    db_manager.init(settings.database_url)
    from shared.database import Base
    from app.models import Project, ProjectMembership, CustomStatus  # noqa
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Redis + PermissionResolver
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=False)
    app.state.redis = redis_client
    app.state.resolver = PermissionResolver(
        redis_client=redis_client,
        org_service_url=settings.org_service_url,
        project_service_url=settings.project_service_url,
        internal_service_key=settings.internal_service_key,
    )
    logger.info("Redis + PermissionResolver initialized")

    await event_producer.start(settings.kafka_bootstrap_servers)
    yield

    await event_producer.stop()
    await redis_client.aclose()
    await db_manager.close()


app = FastAPI(
    title="TaskPM Project Service",
    description="Project management, templates, and membership",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=[get_settings().frontend_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(OrgScopingMiddleware)
app.include_router(project_router)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(service="project_service")

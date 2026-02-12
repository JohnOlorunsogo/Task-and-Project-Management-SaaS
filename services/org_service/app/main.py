"""Organization Service - FastAPI Application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.database import db_manager
from shared.events.producer import event_producer
from shared.middleware import OrgScopingMiddleware
from shared.models import HealthResponse

from app.api import router as org_router
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("org_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting Organization Service on port %s", settings.service_port)

    db_manager.init(settings.database_url)
    from shared.database import Base
    from app.models import Organization, OrgMembership, Team, TeamMembership  # noqa
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    await event_producer.start(settings.kafka_bootstrap_servers)
    yield

    await event_producer.stop()
    await db_manager.close()
    logger.info("Organization Service stopped")


app = FastAPI(
    title="TaskPM Organization Service",
    description="Organization, team, and membership management",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(OrgScopingMiddleware)
app.include_router(org_router)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(service="org_service")

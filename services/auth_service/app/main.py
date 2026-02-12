"""Auth Service - FastAPI Application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.database import db_manager
from shared.events.producer import event_producer
from shared.models import HealthResponse

from app.api import router as auth_router
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("auth_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    logger.info("Starting Auth Service on port %s", settings.service_port)

    # Initialize database
    db_manager.init(settings.database_url)

    # Create tables (dev only — use Alembic in production)
    from shared.database import Base
    from app.models import User  # noqa: F401 — ensure model is registered
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Start Kafka producer
    await event_producer.start(settings.kafka_bootstrap_servers)

    yield

    # Shutdown
    await event_producer.stop()
    await db_manager.close()
    logger.info("Auth Service stopped")


app = FastAPI(
    title="TaskPM Auth Service",
    description="Authentication and user management microservice",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(service="auth_service")
